"""Compare CISO daily review rules at equal workload with historical CAISO events."""
import argparse
import json
from pathlib import Path

import pandas as pd


def evaluate(frame, catalog, start, end, budget, version):
    r=frame[frame.balancing_authority.eq("CISO")].set_index("utc_time").sort_index()
    demand=r["demand_mw"+version]
    past=demand.shift(1).rolling(24*30,min_periods=24*21)
    peak=past.quantile(.99)
    low=past.min()
    norm=(demand-low)/(past.max()-low).where(past.max()>low)
    imports=(-r["total_interchange_mw"+version]/demand.where(demand>0)).clip(0,1)
    shock=((r.demand_forecast_mw-demand).abs()/demand.where(demand>0)).clip(0,1)
    scores=pd.DataFrame({"demand":demand/peak.where(peak>0),"composite":.5*norm.clip(0,1)+.3*imports+.2*shock}).dropna()
    day=(scores.index-pd.Timedelta(hours=1)).tz_convert("America/Los_Angeles").strftime("%Y-%m-%d")
    grouped=scores.groupby(day)
    daily=grouped.max().loc[start:end]
    daily=daily[grouped.size().reindex(daily.index)>=22]
    if budget>len(daily) or budget<1:
        raise ValueError("Review budget outside eligible days")
    if start<catalog["catalog_start"] or end>catalog["catalog_end"]:
        raise ValueError("Evaluation outside documented catalog coverage")
    labels={e["date"] for e in catalog["events"] if start<=e["date"]<=end}
    eligible_events=labels & set(daily.index)
    selections={k:list(daily.sort_values(k,ascending=False,kind="stable").head(budget).index) for k in daily}
    summary={}
    for rule,days in selections.items():
        hits=sorted(eligible_events & set(days))
        summary[rule]={"flagged_days":days,"hits":hits,"missed":sorted(eligible_events-set(days)),
                       "precision":len(hits)/budget,"recall":len(hits)/len(eligible_events) if eligible_events else None}
    return dict(start=start,end=end,field="reported" if not version else "adjusted",eligible_days=len(daily),
                documented_event_days=sorted(labels),unscorable_events=sorted(labels-eligible_events),
                review_budget=budget,rules=summary)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("hourly",type=Path)
    p.add_argument("--catalog",type=Path,default=Path("data/events/ciso_events.json"))
    p.add_argument("--out",type=Path,default=Path("outputs/metrics/event_validation.json"))
    a=p.parse_args()
    frame=pd.read_parquet(a.hourly)
    catalog=json.loads(a.catalog.read_text())
    runs=[evaluate(frame,catalog,f"{y}-01-01",f"{y}-12-31",k,v)
          for y in [2024,2025] for k in [6,12,24] for v in ["","_adjusted"]]
    a.out.write_text(json.dumps({"catalog_sha256":catalog["sha256"],"runs":runs},indent=2)+"\n")
