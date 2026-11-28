"""Stage bounded EIA extracts and publish complete intervals atomically."""
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime,timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine,text

from .fetch_eia_api_data import get_eia_api_config,fetch_eia_api_data,normalize_eia_api_response
from .quality_audit import BA,UTC, FIELDS, CALIFORNIA_AUTHORITIES


def stage(start,end,root,csv=None):
    lo,hi = pd.Timestamp(start),pd.Timestamp(end)
    if lo.tzinfo is None or hi.tzinfo is None or hi<=lo:
        raise ValueError("Expected increasing timezone-aware UTC boundaries")
    if csv:
        data=pd.read_csv(csv,usecols=lambda col: col in FIELDS,low_memory=False)
        source="archive"
    else:
        config=get_eia_api_config()
        config.update(start=lo.tz_convert("UTC").strftime("%Y-%m-%dT%H"),end=(hi-pd.Timedelta(hours=1)).tz_convert("UTC").strftime("%Y-%m-%dT%H"))
        data=normalize_eia_api_response(fetch_eia_api_data(config))
        source="api"
    data=data.rename(columns=FIELDS)
    data[UTC]=pd.to_datetime(data[UTC],utc=True,format="mixed")
    data=data[data[BA].isin(CALIFORNIA_AUTHORITIES)&data[UTC].ge(lo)&data[UTC].lt(hi)].sort_values([BA,UTC])
    expected=len(pd.date_range(lo,hi,freq="h",inclusive="left"))*len(CALIFORNIA_AUTHORITIES)
    if len(data)!=expected or data.duplicated([BA,UTC]).any() or data.demand_mw.isna().any() or data[UTC].ne(data[UTC].dt.floor("h")).any():
        raise ValueError(f"Incomplete or conflicting interval: {len(data)} rows for {expected} authority-hours")
    root.mkdir(parents=True,exist_ok=True)
    folder=Path(tempfile.mkdtemp(dir=root,prefix="interval-"))
    data.to_json(folder/"rows.json",orient="records",date_format="iso",double_precision=15)
    meta={"start":lo.isoformat(),"end":hi.isoformat(),"source":source,"retrieved":datetime.now(timezone.utc).isoformat(),
          "rows":len(data),"sha256":hashlib.sha256((folder/"rows.json").read_bytes()).hexdigest()}
    (folder/"manifest.json").write_text(json.dumps(meta))
    return str(folder)


DDL=[
    "CREATE TABLE IF NOT EXISTS grid_revisions (ba TEXT, utc_hour TEXT, digest TEXT, payload TEXT NOT NULL, PRIMARY KEY(ba,utc_hour,digest))",
    "CREATE TABLE IF NOT EXISTS grid_current (ba TEXT, utc_hour TEXT, vintage TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(ba,utc_hour))",
    "CREATE TABLE IF NOT EXISTS grid_publications (batch TEXT, vintage TEXT, source TEXT, interval_start TEXT, interval_end TEXT, rows_published INTEGER, PRIMARY KEY(batch,vintage))",
]


def publish(folder,db_url,fail=False):
    folder=Path(folder)
    meta=json.loads((folder/"manifest.json").read_text())
    blob=(folder/"rows.json").read_bytes()
    if hashlib.sha256(blob).hexdigest()!=meta["sha256"]:
        raise ValueError("Changed staged payload")
    rows=[]
    for record in json.loads(blob):
        payload=json.dumps(record,sort_keys=True,separators=(",",":"))
        rows.append(dict(ba=record[BA],utc=record[UTC],payload=payload,
                         digest=hashlib.sha256(payload.encode()).hexdigest(),vintage=meta["retrieved"]))
    engine=create_engine(db_url)
    try:
        with engine.begin() as conn:
            for stmt in DDL:
                conn.execute(text(stmt))
            conn.execute(text("INSERT INTO grid_revisions VALUES (:ba,:utc,:digest,:payload) ON CONFLICT (ba,utc_hour,digest) DO NOTHING"),rows)
            if fail:
                raise RuntimeError("Injected stage-to-publication failure")
            conn.execute(text("""INSERT INTO grid_current VALUES (:ba,:utc,:vintage,:digest,:payload)
            ON CONFLICT (ba,utc_hour) DO UPDATE SET digest=excluded.digest,payload=excluded.payload,vintage=excluded.vintage
            WHERE grid_current.vintage < excluded.vintage"""),rows)
            conn.execute(text("""INSERT INTO grid_publications VALUES (:sha256,:retrieved,:source,:start,:end,:rows)
                                ON CONFLICT (batch,vintage) DO NOTHING"""),meta)
    finally:
        engine.dispose()
    return meta


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("start")
    p.add_argument("end")
    p.add_argument("--csv",type=Path)
    p.add_argument("--stage",type=Path,default=Path(".artifacts/stage"))
    a=p.parse_args()
    print(publish(stage(a.start,a.end,a.stage,a.csv),os.environ["GRID_DATABASE_URL"]))
