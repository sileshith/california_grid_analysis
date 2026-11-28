"""Post-freeze operator definition and target-alignment sensitivity checks."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
from .benchmark import BA, UTC, METHODS, panels, proportional, bounds

ROOT=Path(__file__).resolve().parents[1]
MET=ROOT/'outputs/metrics'


def save(name,data):
    (MET/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def errors(rows,actual):
    e=rows.authority-rows[actual]
    return dict(hours=int(e.notna().sum()),bias_mw=float(e.mean()),mae_mw=float(e.abs().mean()))


def score(frame,spec,frozen,target='actual'):
    daily,paired=panels(frame,spec,target)
    model=frozen['candidate']
    return dict(g=proportional(daily[model],daily.authority),upper95=bounds(daily,model,frozen['block_days'],spec),eligible_days=len(daily),matched_hours=len(paired),ratios={ba:float(daily[(model,ba)].mean()/daily[('authority',ba)].mean()) for ba in daily.authority.columns})


def main():
    spec=json.loads((ROOT/'config/holdout.json').read_text());frozen=json.loads((ROOT/'config/frozen_benchmark.json').read_text())
    pred=pd.read_parquet(ROOT/'.artifacts/benchmark/predictions.parquet')
    keys=[BA,UTC]
    meta=pred.drop_duplicates(keys).drop(columns=['method','forecast_mw']).set_index(keys)
    wide=meta.join(pred.pivot(index=keys,columns='method',values='forecast_mw')).reset_index()
    wide['hour']=(wide[UTC]-pd.Timedelta(hours=1)).dt.tz_convert('America/Los_Angeles').dt.hour
    wide['month']=(wide[UTC]-pd.Timedelta(hours=1)).dt.tz_convert('America/Los_Angeles').dt.strftime('%Y-%m')
    diagnostic=[];sensitivity={}
    for target in ['actual','reported']:
        for shift in [-1,0,1]:
            changed=wide.copy()
            source=wide.set_index(keys)[target]
            lookup=pd.MultiIndex.from_arrays([wide[BA],wide[UTC]+pd.Timedelta(hours=shift)])
            changed['variant_target']=source.reindex(lookup).to_numpy()
            # Alignment checks preserve frozen eligibility flags for diagnostic rows.
            common=changed[changed.matched & changed.variant_target.notna()]
            for ba,rows in common.groupby(BA):
                diagnostic.append(dict(authority=ba,target='adjusted' if target=='actual' else 'reported',shift_hours=shift,overall=errors(rows,'variant_target'),by_local_hour=[dict(hour=int(h),**errors(r,'variant_target')) for h,r in rows.groupby('hour')],by_month=[dict(month=m,**errors(r,'variant_target')) for m,r in rows.groupby('month')]))
            name=('adjusted' if target=='actual' else 'reported')+f'_shift_{shift:+d}'
            sensitivity[name]=score(changed,spec,frozen,'variant_target')
    requests=json.loads((ROOT/'verification/oasis_download_requests.json').read_text())
    if not all(r.get('validation',{}).get('valid') for r in requests):raise ValueError('OASIS download gate incomplete')
    cross=[];oasis_parts=[];alignment=[]
    for request in requests:
        path=ROOT/request['target']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==request['sha256']
        with ZipFile(path) as z: oasis=pd.read_csv(z.open(request['validation']['member']))
        oasis[UTC]=pd.to_datetime(oasis.INTERVALENDTIME_GMT,utc=True)
        for area,ba in [('CA ISO-TAC','CISO'),('LADWP','LDWP')]:
            subset=oasis[oasis.TAC_AREA_NAME.eq(area)][[UTC,'MW']]
            subset[BA]=ba
            subset['market']=request['market_run_id']
            oasis_parts.append(subset.copy())
            base=wide[wide[BA].eq(ba)]
            # Report all available seasonal hours, including frozen unmatched rows.
            merged=base.merge(subset,on=UTC,validate='one_to_one')
            if request['market_run_id']=='ACTUAL':
                observed=subset.set_index(UTC).MW
                target=base.set_index(UTC).actual
                for shift in [-1,0,1]:
                    changed=pd.Series(target.reindex(observed.index+pd.Timedelta(hours=shift)).to_numpy(),index=observed.index)-observed
                    valid=changed.dropna()
                    alignment.append(dict(authority=ba,start=request['startdatetime'],shift_hours=shift,hours=len(valid),bias_mw=float(valid.mean()),mae_difference_mw=float(valid.abs().mean())))
            fields=['authority'] if request['market_run_id']=='DAM' else ['actual','reported']
            for field in fields:
                d=(merged[field]-merged.MW).dropna()
                cross.append(dict(authority=ba,market=request['market_run_id'],start=request['startdatetime'],end_exclusive=request['enddatetime'],eia_field=field,matched_hours=len(d),bias_eia_minus_oasis_mw=float(d.mean()),mae_difference_mw=float(d.abs().mean()),max_absolute_difference_mw=float(d.abs().max()),exact_equal_hours=int(d.eq(0).sum())))
    oasis_all=pd.concat(oasis_parts)
    op=oasis_all.pivot(index=keys,columns='market',values='MW').rename(columns={'ACTUAL':'oasis_actual','DAM':'oasis_operator'})
    seasonal_days=set(wide[wide[UTC].isin(oasis_all[UTC])].day)
    seasonal=wide[wide.day.isin(seasonal_days)].merge(op,on=keys,how='left',validate='one_to_one')
    sensitivity['seasonal_original_adjusted']=score(seasonal,spec,frozen)
    for variant in ['oasis_actual','oasis_actual_and_operator']:
        v=seasonal.copy()
        relevant=v[BA].isin(['CISO','LDWP'])
        v.loc[relevant,'actual']=v.loc[relevant,'oasis_actual']
        if variant=='oasis_actual_and_operator':v.loc[relevant,'authority']=v.loc[relevant,'oasis_operator']
        sensitivity['seasonal_'+variant]=score(v,spec,frozen)
        sensitivity['seasonal_'+variant]['scope']='Only sampled seasonal weeks. CISO and LDWP use OASIS targets. Other authorities retain EIA targets. Not comparable to full-window G.'
    storage=[];parts=[]
    sources=json.loads((ROOT/'data/manifest/operator_eia_sources.json').read_text())
    for s in sources:
        fields=[c for c in s['columns'] if any(k in c.lower() for k in ['battery','storage'])]
        storage.append(dict(path=s['path'],sha256=s['sha256'],columns=fields))
        cols=['Balancing Authority','UTC Time at End of Hour','Net Generation (MW) from Battery Storage']
        raw=pd.read_csv(ROOT/s['path'],usecols=lambda c:c in cols,low_memory=False)
        raw=raw[raw['Balancing Authority'].isin(wide[BA].unique())].rename(columns={'Balancing Authority':BA,'UTC Time at End of Hour':UTC,'Net Generation (MW) from Battery Storage':'battery_net_generation_mw'})
        raw[UTC]=pd.to_datetime(raw[UTC],utc=True,format='mixed');parts.append(raw)
    battery=pd.concat(parts).drop_duplicates(keys)
    v=wide.merge(battery,on=keys,how='left',validate='one_to_one')
    # Net generation cannot separate concurrent fleet charging and discharge.
    # Subtract negative net output only as an explicitly exploratory proxy.
    v['storage_proxy_target']=v.actual
    selected=v[BA].eq('LDWP')
    v.loc[selected,'storage_proxy_target']=v.loc[selected,'actual']+v.loc[selected,'battery_net_generation_mw'].clip(upper=0)
    sensitivity['adjusted_ldwp_net_battery_charging_proxy']=score(v,spec,frozen,'storage_proxy_target')
    sensitivity['adjusted_ldwp_net_battery_charging_proxy']['formula']='LDWP adjusted demand + min(battery net generation, 0), other authorities unchanged. Missing LDWP battery values remain unavailable. Exploratory net-charging proxy, not a validated demand definition. CISO has no observed dedicated battery-generation values. No integrated, pumped or other storage is removed.'
    sensitivity['adjusted_ldwp_net_battery_charging_proxy']['source_vintage']='Newly retrieved holdout bulk files match the frozen source hashes.'
    save('operator_diagnostics.json',dict(status='post-freeze sensitivity',shift_convention='At forecast time t, compare with demand at t + shift_hours. Negative means earlier demand.',diagnostics=diagnostic,oasis_comparisons=cross,oasis_alignment_checks=alignment,storage_headers=storage,storage_coverage=v.groupby(BA).battery_net_generation_mw.count().astype(int).to_dict(),conclusion='Hour shifts and net-battery proxies are exploratory. OASIS comparisons do not establish EIA publication-time forecast availability or a causal storage correction. Retain CISO and LDWP definitional caveats.'))
    save('forecast_sensitivity.json',dict(status='post-freeze sensitivity',frozen_predictions_unchanged=True,eligibility='Recomputed under each target variant using the frozen rule. Shift endpoints can change common eligible days. No imputation.',variants=sensitivity))
    print(json.dumps(sensitivity,indent=2))


if __name__=='__main__':main()
