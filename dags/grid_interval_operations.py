"""Two-task transactional daily publication. GRID_STAGE must be shared by workers."""
import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.decorators import dag,task


@dag(schedule="@daily",start_date=pendulum.datetime(2024,1,1,tz="UTC"),catchup=False,
     default_args={"retries":2,"retry_delay":timedelta(minutes=5)},tags=["grid","incremental"])
def grid_interval_operations():
    @task
    def extract(**context):
        from src.interval_store import stage
        return stage(context["data_interval_start"],context["data_interval_end"],
                     Path(os.environ["GRID_STAGE"]),os.getenv("GRID_INPUT_CSV"))

    @task
    def publish_interval(folder):
        from src.interval_store import publish
        return publish(folder,os.environ["GRID_DATABASE_URL"])
    publish_interval(extract())


interval_dag = grid_interval_operations()


@dag(schedule="0 12 * * *",start_date=pendulum.datetime(2024,1,1,tz="America/Los_Angeles"),
     catchup=False,tags=["grid","day-ahead"])
def grid_forecast_release_status():
    @task
    def release(**context):
        from src.forecast_status import record
        return record(context["data_interval_end"],os.environ["GRID_DATABASE_URL"],
                      os.getenv("GRID_OPERATOR_SNAPSHOT"))
    release()


forecast_status_dag = grid_forecast_release_status()
