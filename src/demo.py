"""Run the pipeline and its tests against generated data in an isolated directory."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree

import numpy as np
import pandas as pd
from .quality_audit import CALIFORNIA_AUTHORITIES


def fixture():
    times=pd.date_range("2026-03-01",periods=360,freq="h",tz="UTC")
    frames=[]
    for n,ba in enumerate(CALIFORNIA_AUTHORITIES):
        demand=np.round(200*(n+1)+40*np.sin(np.arange(len(times))*np.pi/12),2)
        frames.append(pd.DataFrame({"Balancing Authority":ba,"UTC Time at End of Hour":times.astype(str),
            "Demand (MW)":demand,"Demand (MW) (Adjusted)":demand,"Net Generation (MW)":demand-10,
            "Total Interchange (MW)":-10,"Demand Forecast (MW)":demand+2}))
    return pd.concat(frames,ignore_index=True)


def main():
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        dest=Path(tmp)
        for folder in ["src","dags","tests","config","data/manifest","data/events","outputs/metrics"]:
            if (root/folder).exists():
                shutil.copytree(root/folder,dest/folder,ignore=shutil.ignore_patterns("__pycache__"))
        for file in ["README.md","pytest.ini"]:
            shutil.copy2(root/file,dest/file)
        raw=dest/"data/raw/EIA930_BALANCE_2026_Jan_Jun.csv"
        raw.parent.mkdir(parents=True)
        fixture().to_csv(raw,index=False)
        env=dict(os.environ, DATABASE_URL="",USE_EIA_API="false",AIRFLOW_HOME=str(dest/"airflow"),
                 GRID_STAGE=str(dest/"stage"),PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        subprocess.run([sys.executable,"dags/california_grid_daily_pipeline.py"],cwd=dest,env=env,check=True)
        subprocess.run([sys.executable,"-m","pytest","-q","--junitxml=demo.xml"],cwd=dest,env=env,check=True)
        if ElementTree.parse(dest/"demo.xml").find(".//skipped") is not None:
            raise ValueError("Required fixture suite skipped tests")


if __name__=="__main__":
    main()
