import json
import os
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine,text

from src.benchmark import BA,UTC,FEATURES,METHODS,design,panels,proportional
from src.demo import fixture
from src.interval_store import stage,publish
from src.quality_audit import audit

SPEC=json.loads(Path("config/holdout.json").read_text())


@pytest.mark.parametrize(("day","hours"),[("2026-03-08",23),("2026-11-01",25),("2026-02-18",24)])
def test_issue_cutoff_and_dst(day,hours):
    d=pd.Timestamp(day)
    t=pd.date_range((d-pd.Timedelta(days=12)).tz_localize("UTC"),(d+pd.Timedelta(days=2)).tz_localize("UTC"),freq="h")
    raw=pd.DataFrame({BA:"CISO",UTC:t,"demand_mw":np.arange(len(t)),"demand_mw_adjusted":50.,"demand_forecast_mw":51.})
    a=design(raw,SPEC)
    test=a[a.day.eq(d)]
    assert len(test)==hours and test.issue.nunique()==1
    raw.loc[raw[UTC]>test.issue.iloc[0]-pd.Timedelta(hours=1),"demand_mw"]=999999
    b=design(raw,SPEC)
    pd.testing.assert_frame_equal(test[FEATURES],b.loc[b.day.eq(d),FEATURES])


def test_equal_daily_weights():
    frames=[]
    for ba in ["BANC","CISO","IID","LDWP","TIDC"]:
        for i,n in [(0,22),(1,24)]:
            rows=pd.DataFrame({"day":pd.Timestamp("2026-02-01")+pd.Timedelta(days=i),BA:ba,"actual":np.zeros(n),
                               **{m:np.ones(n) for m in METHODS}})
            rows["lightgbm"]=2+2*i
            frames.append(rows)
    daily,_=panels(pd.concat(frames),SPEC)
    assert proportional(daily.lightgbm,daily.authority)==pytest.approx(3.)


def test_quality_gap_zero_and_duplicate():
    raw=fixture()
    raw.loc[1,"Demand (MW)"]=0
    raw=pd.concat([raw.iloc[1:],raw.iloc[[2]]])
    summary,_,_,duplicates=audit(raw)
    ba=summary["BANC"]
    assert (ba["missing_hours"],ba["zero_reported"],ba["duplicate_keys"])==(1,1,1)
    assert len(duplicates)==2


def test_transaction_replay_recovery(tmp_path):
    db=os.getenv("GRID_TEST_DATABASE_URL","sqlite:///"+str(tmp_path/"ops.db"))
    source=tmp_path/"source.csv"
    data=fixture()
    data.to_csv(source,index=False)
    def extract(day):
        d=pd.Timestamp(day,tz="UTC")
        return stage(d,d+pd.Timedelta(days=1),tmp_path,source)
    def counts():
        with create_engine(db).connect() as c:
            return [c.scalar(text("select count(*) from "+name)) for name in ["grid_current","grid_revisions"]]
    one=extract("2026-03-02")
    publish(one,db)
    publish(one,db)
    assert counts()==[120,120]
    two=extract("2026-03-03")
    with pytest.raises(RuntimeError,match="Injected"):
        publish(two,db,fail=True)
    assert counts()==[120,120]
    publish(two,db)
    assert counts()==[240,240]
    idx=(data["UTC Time at End of Hour"].eq("2026-03-02 00:00:00+00:00") & data["Balancing Authority"].eq("BANC"))
    data.loc[idx,"Demand (MW)"]+=1
    data.to_csv(source,index=False)
    publish(extract("2026-03-02"),db)
    assert counts()==[240,241]
    publish(one,db)
    with create_engine(db).connect() as conn:
        payload=conn.scalar(text("select payload from grid_current where ba='BANC' and utc_hour like '2026-03-02T00:%'"))
    assert json.loads(payload)["demand_mw"]==data.loc[idx,"Demand (MW)"].iloc[0]


def test_unavailable_forecast_and_clock_change(tmp_path):
    from src.forecast_status import record
    path=tmp_path/"status.db"
    url="sqlite:///"+str(path)
    assert record("2026-03-07T20:00Z",url)==115
    assert record("2026-03-07T20:00Z",url)==115
    with sqlite3.connect(path) as c:
        assert c.execute("select count(*) from grid_forecast_status where status='unavailable' and mw is null").fetchone()[0]==115
