"""Record the day-ahead release decision and any timely authority fallback."""
import json
from datetime import datetime,timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine,text

from .transform_energy_metrics import CALIFORNIA_AUTHORITIES

TZ="America/Los_Angeles"


def record(issue,db_url,authority_snapshot=None):
    cutoff=pd.Timestamp(issue)
    if cutoff.tzinfo is None or cutoff.tz_convert(TZ).strftime("%H:%M:%S")!="12:00:00":
        raise ValueError("Expected a noon Pacific issue timestamp")
    day=cutoff.tz_convert(TZ).tz_localize(None).normalize()+pd.Timedelta(days=1)
    starts=pd.date_range(day.tz_localize(TZ),(day+pd.Timedelta(days=1)).tz_localize(TZ),freq="h",inclusive="left")
    forecasts={}
    if authority_snapshot:
        folder=Path(authority_snapshot)
        manifest=json.loads((folder/"manifest.json").read_text())
        import hashlib
        blob=(folder/"rows.json").read_bytes()
        if manifest["sha256"]!=hashlib.sha256(blob).hexdigest():
            raise ValueError("Changed operator snapshot")
        if manifest["source"]=="api" and pd.Timestamp(manifest["retrieved"])<=cutoff:
            for row in json.loads(blob):
                value=row.get("demand_forecast_mw")
                if value is not None:
                    forecasts[(row["balancing_authority"],pd.Timestamp(row["utc_time"]))]=float(value)
    rows=[]
    for ba in CALIFORNIA_AUTHORITIES:
        for start in starts:
            target=(start+pd.Timedelta(hours=1)).tz_convert("UTC")
            value=forecasts.get((ba,target))
            rows.append({"ba":ba,"issue":cutoff.tz_convert("UTC").isoformat(),"target":target.isoformat(),
                         "mw":value,"status":"authority_fallback" if value is not None else "unavailable",
                         "reason":"candidate_did_not_clear_holdout_criterion"})
    engine=create_engine(db_url)
    try:
        with engine.begin() as conn:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS grid_forecast_status
            (ba TEXT,issue TEXT,target TEXT,mw DOUBLE PRECISION,status TEXT,reason TEXT,
            PRIMARY KEY(ba,issue,target))"""))
            conn.execute(text("""INSERT INTO grid_forecast_status VALUES (:ba,:issue,:target,:mw,:status,:reason)
                ON CONFLICT (ba,issue,target) DO NOTHING"""),rows)
    finally:
        engine.dispose()
    return len(rows)
