"""Prepare the development specification, then replay its frozen day-ahead forecast."""
import argparse
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from prophet import Prophet

from .quality_audit import BA, UTC, hourly, CALIFORNIA_AUTHORITIES

TZ = "America/Los_Angeles"
ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["hour", "weekday", "weekly", "recent", "last", "horizon"]
METHODS = ["authority", "previous_week", "moving_average", "lightgbm", "prophet"]
OUT = ROOT / ".artifacts/benchmark"
SPEC = ROOT / "config/holdout.json"
FREEZE = ROOT / "config/frozen_benchmark.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def prepare(paths):
    from .quality_audit import FIELDS
    parts, manifest = [], []
    for path in sorted(paths):
        part = pd.read_csv(path, usecols=lambda c: c in FIELDS, low_memory=False)
        selected = part[part["Balancing Authority"].isin(CALIFORNIA_AUTHORITIES)]
        times = pd.to_datetime(selected["UTC Time at End of Hour"], format="mixed", utc=True)
        manifest.append(dict(file=path.name, sha256=digest(path), bytes=path.stat().st_size,
                             raw_rows=len(part), selected_rows=len(selected), first=str(times.min()), last=str(times.max()),
                             url="https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"+path.name))
        parts.append(selected)
    frame, duplicates = hourly(pd.concat(parts))
    OUT.mkdir(exist_ok=True, parents=True)
    duplicates.to_parquet(OUT/"duplicates.parquet", index=False)
    frame.to_parquet(OUT/"hourly.parquet", index=False)
    dump(ROOT/"data/manifest/benchmark_sources.json", manifest)


def design(rows, spec):
    rows = rows.sort_values(UTC).set_index(UTC)
    t = rows.index
    wall = (t-pd.Timedelta(hours=1)).tz_convert(TZ).tz_localize(None)
    day = wall.normalize()
    issue = (day-pd.Timedelta(days=1)+pd.Timedelta(hours=spec["issue_hour_pacific"])).tz_localize(TZ).tz_convert("UTC")
    cutoff = issue-pd.Timedelta(hours=spec["assumed_reporting_delay_hours"])
    weekly = (t.tz_convert(TZ).tz_localize(None)-pd.Timedelta(days=7)).tz_localize(TZ, ambiguous="NaT", nonexistent="NaT")
    demand = rows.demand_mw
    d = pd.DataFrame(index=t)
    d[BA], d["day"], d["issue"] = rows[BA], day, issue
    d["hour"], d["weekday"], d["horizon"] = wall.hour, wall.dayofweek, (t-issue).total_seconds()/3600
    d["weekly"] = demand.reindex(weekly).to_numpy()
    d["recent"] = demand.rolling("168h",min_periods=120).mean().reindex(cutoff).to_numpy()
    d["last"] = demand.reindex(cutoff).to_numpy()
    d["actual"], d["reported"], d["authority"] = rows.demand_mw_adjusted, demand, rows.demand_forecast_mw
    return d.reset_index()


def predict_window(frame, start, end, spec):
    targets = frame[(frame.day >= start) & (frame.day < end)].copy()
    cutoff = targets.issue.min()-pd.Timedelta(hours=spec["assumed_reporting_delay_hours"])
    train = frame[frame[UTC].le(cutoff)].dropna(subset=["reported","weekly","recent"])
    if train.empty or targets.empty:
        raise ValueError("Insufficient training or target coverage")
    lgb = LGBMRegressor(n_estimators=150, learning_rate=.04, num_leaves=15, n_jobs=1, random_state=42, verbosity=-1)
    lgb.fit(train[FEATURES], train.reported)
    prophet = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=True)
    prophet.fit(pd.DataFrame({"ds":train[UTC].dt.tz_localize(None),"y":train.reported}))
    targets["lightgbm"] = lgb.predict(targets[FEATURES])
    targets["prophet"] = prophet.predict(pd.DataFrame({"ds":targets[UTC].dt.tz_localize(None)})).yhat.to_numpy()
    targets["previous_week"],targets["moving_average"] = targets.weekly,targets.recent
    targets["peak_threshold_mw"] = train.reported.quantile(.99)
    targets["train_cutoff"] = cutoff
    return targets


def panels(frame, spec, actual="actual"):
    paired = frame.dropna(subset=[actual,*METHODS]).copy()
    for method in METHODS:
        paired[method] = (paired[method]-paired[actual]).abs()
    groups = paired.groupby([BA,"day"])
    loss = groups[METHODS].mean()
    dates = loss.index.get_level_values("day")
    hours = ((dates+pd.Timedelta(days=1)).tz_localize(TZ)-dates.tz_localize(TZ)).total_seconds()/3600
    loss = loss[groups.size() >= np.ceil(spec["minimum_daily_fraction"]*hours)]
    daily = loss.unstack(BA).reindex(columns=pd.MultiIndex.from_product([METHODS,CALIFORNIA_AUTHORITIES])).dropna()
    if daily.empty:
        raise ValueError("No eligible common days")
    return daily,frame[frame.day.isin(daily.index)].dropna(subset=[actual,*METHODS])


def proportional(a,b):
    ratios = np.mean(a,axis=0)/np.mean(b,axis=0)
    if not np.isfinite(ratios).all() or (ratios<=0).any():
        raise ValueError("Undefined log ratio")
    return float(np.exp(np.mean(np.log(ratios))))


def bounds(daily, method, length, spec):
    a,b = daily[method].to_numpy(),daily["authority"].to_numpy()
    starts=[i for i in range(len(a)-length+1) if (daily.index[i+length-1]-daily.index[i]).days==length-1]
    if not starts or len(a)<4*length:
        return None
    rng=np.random.default_rng(spec["seed"])
    estimates=[]
    for _ in range(spec["replicates"]):
        ix=(rng.choice(starts,int(np.ceil(len(a)/length)))[:,None]+np.arange(length)).ravel()[:len(a)]
        estimates.append(proportional(a[ix],b[ix]))
    return float(np.quantile(estimates,spec["confidence"]))


def execute(mode):
    spec=json.loads(SPEC.read_text())
    hashes={p.name:digest(p) for p in [SPEC,Path(__file__),ROOT/"src/quality_audit.py",ROOT/"data/manifest/benchmark_sources.json",OUT/"hourly.parquet"]}
    if mode=="score":
        frozen=json.loads(FREEZE.read_text())
        tag=subprocess.check_output(["git","show","spec-frozen-v1:config/frozen_benchmark.json"],cwd=ROOT)
        if tag!=FREEZE.read_bytes() or hashes!=frozen["hashes"]:
            raise ValueError("Frozen specification, code or data mismatch")
    raw=pd.read_parquet(OUT/"hourly.parquet")
    start,end=(spec["validation_start"],spec["test_start"]) if mode=="freeze" else (spec["test_start"],spec["end_exclusive"])
    predictions=pd.concat([predict_window(design(group,spec),start,end,spec) for _,group in raw.groupby(BA)])
    if mode=="freeze":
        # Discard the whole last delivery day, whose outcomes would arrive after the first test issue.
        predictions=predictions[predictions.day < pd.Timestamp(end)-pd.Timedelta(days=1)]
    daily,paired=panels(predictions,spec)
    scores={m:proportional(daily[m],daily["authority"]) for m in spec["candidate_pool"]}
    if mode=="freeze":
        candidate=min(scores,key=scores.get)
        dif=(daily[candidate]-daily["authority"]).mean(axis=1).asfreq("D")
        length=next((i for i in range(1,8) if abs(dif.autocorr(i))<.2),7)
        dump(FREEZE,{"candidate":candidate,"block_days":length,"validation_scores":scores,"hashes":hashes})
        return
    candidate=frozen["candidate"]
    detail=[]
    for ba,rows in paired.groupby(BA):
        for method in METHODS:
            error=rows[method]-rows.actual
            peak=rows.actual.ge(rows.peak_threshold_mw)
            detail.append({BA:ba,"method":method,"matched_hours":len(rows),
                           "daily_mae_mw":daily[(method,ba)].mean(),"mae_mw":error.abs().mean(),
                           "bias_mw":error.mean(),"rmse_mw":np.sqrt(error.pow(2).mean()),
                           "peak_hours":int(peak.sum()),"peak_mae_mw":error[peak].abs().mean() if peak.any() else None})
    alt,_=panels(predictions,spec,"reported")
    stats=dict(candidate=candidate,g=scores[candidate],reported_target_g=proportional(alt[candidate],alt["authority"]),
               eligible_days=len(daily),matched_hours=len(paired),intended_hours=len(predictions),start=start,end_exclusive=end,
               upper95={str(k):bounds(daily,candidate,k,spec) for k in set([3,7,14,frozen["block_days"]])},
               block_days=frozen["block_days"],authority_metrics=detail,freeze_sha256=digest(FREEZE))
    dump(ROOT/"outputs/metrics/forecast_benchmark.json",stats)
    long=predictions.melt(id_vars=[BA,UTC,"day","issue","train_cutoff","horizon","actual","reported","peak_threshold_mw"],value_vars=METHODS,var_name="method",value_name="forecast_mw")
    long["run_id"]=digest(FREEZE)[:16]
    long["matched"]=pd.MultiIndex.from_frame(long[[BA,UTC]]).isin(pd.MultiIndex.from_frame(paired[[BA,UTC]]))
    long.to_parquet(OUT/"predictions.parquet",index=False)
    with sqlite3.connect(OUT/"forecast.sqlite") as conn:
        long.to_sql("predictions",conn,index=False,if_exists="replace")
        conn.execute("CREATE UNIQUE INDEX forecast_key ON predictions(run_id,method,balancing_authority,issue,utc_time)")
    print({k:v for k,v in stats.items() if k!="authority_metrics"})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["prepare","freeze","score"])
    parser.add_argument("paths",nargs="*",type=Path)
    args=parser.parse_args()
    if args.mode=="prepare":
        prepare(args.paths)
    else:
        execute(args.mode)
