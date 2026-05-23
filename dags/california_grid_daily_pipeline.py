"""
california_grid_daily_pipeline.py

Apache Airflow DAG: California Grid Operations Intelligence Pipeline.

Orchestrates the full seven-step ELT pipeline for daily California grid
stress monitoring, SQL-based operational reporting, and Tableau-ready exports.

Pipeline task sequence:
    fetch_or_load_eia_data
        >> validate_grid_data
        >> transform_energy_metrics
        >> calculate_grid_stress_index
        >> load_results_to_sql
        >> export_tableau_data
        >> generate_monitoring_summary

DAG identity:
    dag_id   : california_grid_operations_pipeline
    owner    : sileshi
    schedule : @daily (override to None for manual local testing)
    tags     : energy, airflow, elt, tableau, tesla-alignment, grid-analytics

To run locally without Airflow:
    python dags/california_grid_daily_pipeline.py

To trigger via Airflow CLI:
    airflow dags trigger california_grid_operations_pipeline

To run standalone (no Airflow installed):
    Each src/ module has an if __name__ == '__main__' block for direct execution.
"""

import os
import sys
from datetime import datetime, timedelta

# All execution code lives inside functions — this file is safe to import.
# Airflow parses DAG files on every scheduler heartbeat; nothing runs at import time.

SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


# ── Task callables ────────────────────────────────────────────────────────────
# Each function is a self-contained unit. XCom is used to pass intermediate
# file paths between tasks so each task loads its own data from disk.

def run_fetch_or_load_eia_data(**context):
    # API mode is controlled by USE_EIA_API and EIA_API_KEY environment variables.
    # Local CSV fallback remains the default for reproducible portfolio runs.
    from fetch_or_load_eia_data import fetch_or_load_eia_data, get_source_label
    df = fetch_or_load_eia_data()
    temp_path = "/tmp/ca_grid_raw.parquet"
    df.to_parquet(temp_path, index=False)
    context["ti"].xcom_push(key="raw_data_path", value=temp_path)
    context["ti"].xcom_push(key="raw_row_count", value=len(df))
    context["ti"].xcom_push(key="source_label", value=get_source_label())
    return temp_path


def run_validate_grid_data(**context):
    import pandas as pd
    from validate_grid_data import validate_grid_data
    raw_path = context["ti"].xcom_pull(key="raw_data_path", task_ids="fetch_or_load_eia_data")
    df = pd.read_parquet(raw_path)
    _, report = validate_grid_data(df)
    context["ti"].xcom_push(key="validation_report", value=str(report))
    return report


def run_transform_energy_metrics(**context):
    import pandas as pd
    from transform_energy_metrics import transform_energy_metrics
    raw_path = context["ti"].xcom_pull(key="raw_data_path", task_ids="fetch_or_load_eia_data")
    df = pd.read_parquet(raw_path)
    df_transformed = transform_energy_metrics(df)
    temp_path = "/tmp/ca_grid_transformed.parquet"
    df_transformed.to_parquet(temp_path, index=False)
    context["ti"].xcom_push(key="transformed_data_path", value=temp_path)
    return temp_path


def run_calculate_grid_stress_index(**context):
    import pandas as pd
    from calculate_grid_stress_index import calculate_grid_stress_index
    transformed_path = context["ti"].xcom_pull(
        key="transformed_data_path", task_ids="transform_energy_metrics"
    )
    df = pd.read_parquet(transformed_path)
    df_scored = calculate_grid_stress_index(df)
    temp_path = "/tmp/ca_grid_scored.parquet"
    df_scored.to_parquet(temp_path, index=False)
    context["ti"].xcom_push(key="scored_data_path", value=temp_path)
    return temp_path


def run_load_results_to_sql(**context):
    import pandas as pd
    from load_results_to_sql import load_results_to_sql
    scored_path = context["ti"].xcom_pull(
        key="scored_data_path", task_ids="calculate_grid_stress_index"
    )
    df = pd.read_parquet(scored_path)
    db_path = load_results_to_sql(df)
    return db_path


def run_export_tableau_data(**context):
    import pandas as pd
    from export_tableau_data import export_tableau_data
    scored_path = context["ti"].xcom_pull(
        key="scored_data_path", task_ids="calculate_grid_stress_index"
    )
    df = pd.read_parquet(scored_path)
    exported_files = export_tableau_data(df)
    return exported_files


def run_generate_monitoring_summary(**context):
    import pandas as pd
    from generate_monitoring_summary import generate_monitoring_summary
    scored_path = context["ti"].xcom_pull(
        key="scored_data_path", task_ids="calculate_grid_stress_index"
    )
    source_label = context["ti"].xcom_pull(
        key="source_label", task_ids="fetch_or_load_eia_data"
    )
    df = pd.read_parquet(scored_path)
    summary = generate_monitoring_summary(df, source_file=source_label)
    return summary


# ── DAG definition ────────────────────────────────────────────────────────────
# Wrapped in a try/except so the file can be run directly (python dags/...py)
# without requiring Airflow to be installed.

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator

    default_args = {
        "owner": "sileshi",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "email_on_failure": False,
        "email_on_retry": False,
    }

    with DAG(
        dag_id="california_grid_operations_pipeline",
        description=(
            "Daily California grid operations intelligence pipeline for stress "
            "monitoring, SQL reporting, and Tableau-ready exports."
        ),
        schedule_interval="@daily",
        start_date=datetime(2026, 1, 1),
        catchup=False,
        default_args=default_args,
        tags=["energy", "airflow", "elt", "tableau", "tesla-alignment", "grid-analytics"],
    ) as dag:

        fetch = PythonOperator(
            task_id="fetch_or_load_eia_data",
            python_callable=run_fetch_or_load_eia_data,
        )
        validate = PythonOperator(
            task_id="validate_grid_data",
            python_callable=run_validate_grid_data,
        )
        transform = PythonOperator(
            task_id="transform_energy_metrics",
            python_callable=run_transform_energy_metrics,
        )
        stress = PythonOperator(
            task_id="calculate_grid_stress_index",
            python_callable=run_calculate_grid_stress_index,
        )
        sql_load = PythonOperator(
            task_id="load_results_to_sql",
            python_callable=run_load_results_to_sql,
        )
        tableau_export = PythonOperator(
            task_id="export_tableau_data",
            python_callable=run_export_tableau_data,
        )
        monitoring = PythonOperator(
            task_id="generate_monitoring_summary",
            python_callable=run_generate_monitoring_summary,
        )

        fetch >> validate >> transform >> stress >> sql_load >> tableau_export >> monitoring

except ImportError:
    # Airflow not installed — DAG definition is skipped but pipeline functions
    # remain available for direct execution via the src/ modules.
    pass


# ── Standalone execution (no Airflow required) ────────────────────────────────
if __name__ == "__main__":
    print("Running California Grid Operations Intelligence Pipeline (standalone mode)")
    print("=" * 70)

    context = {"ti": type("XCom", (), {
        "_store": {},
        "xcom_push": lambda self, key, value: self._store.update({key: value}),
        "xcom_pull": lambda self, key, task_ids: self._store.get(key),
    })()}

    run_fetch_or_load_eia_data(**context)
    run_validate_grid_data(**context)
    run_transform_energy_metrics(**context)
    run_calculate_grid_stress_index(**context)
    run_load_results_to_sql(**context)
    run_export_tableau_data(**context)
    run_generate_monitoring_summary(**context)

    print("=" * 70)
    print("Pipeline complete.")
