"""Supply isolated pipeline outputs when a clean checkout has no raw data."""
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture(scope='session',autouse=True)
def pipeline_outputs_for_clean_checkout(request,tmp_path_factory):
    root=Path(__file__).resolve().parents[1]
    if (root/'outputs/tableau_exports/california_grid_dashboard_ready.csv').exists():
        return
    from src.demo import fixture
    dest=tmp_path_factory.mktemp('pipeline')
    for folder in ['src','dags']:
        shutil.copytree(root/folder,dest/folder,ignore=shutil.ignore_patterns('__pycache__'))
    raw=dest/'data/raw/EIA930_BALANCE_2026_Jan_Jun.csv';raw.parent.mkdir(parents=True)
    fixture().to_csv(raw,index=False)
    env=dict(os.environ,DATABASE_URL='',USE_EIA_API='false',AIRFLOW_HOME=str(dest/'airflow'))
    subprocess.run([sys.executable,'dags/california_grid_daily_pipeline.py'],cwd=dest,env=env,check=True,capture_output=True,text=True)
    for item in request.session.items:
        module=item.module
        if module.__name__.endswith(('test_pipeline_outputs','test_required_columns')):
            module.TABLEAU_EXPORTS_DIR=str(dest/'outputs/tableau_exports')
            module.MONITORING_DIR=str(dest/'outputs/monitoring')
            module.DASHBOARD_FILE=str(dest/'outputs/tableau_exports/california_grid_dashboard_ready.csv')
