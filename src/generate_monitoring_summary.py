"""
generate_monitoring_summary.py

Generate a pipeline monitoring summary with run statistics and key grid metrics.
One row is appended to outputs/monitoring/daily_monitoring_summary.csv on each run.

Summary fields:
    pipeline_run_date        — calendar date of this pipeline run
    total_scored_hours       — total hourly records processed
    high_priority_hours      — hours classified as High Review Priority
    average_stress_index     — mean stress index across all scored hours
    peak_demand_mw           — highest single-hour demand in the dataset
    highest_stress_authority — authority with the highest average stress index
    largest_forecast_error_mw — largest absolute forecast error (MW)
    source_file              — name of the raw input file
    run_status               — 'success' or 'failed'

This is step 7 (final step) in the California Grid Operations Intelligence Pipeline.
"""

import os
import datetime
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MONITORING_DIR = os.path.join(BASE_DIR, "outputs", "monitoring")
DEFAULT_SOURCE_FILE = "EIA930_BALANCE_2026_Jan_Jun.csv"


def generate_monitoring_summary(df, source_file=None, export_dir=None):
    """
    Compute summary statistics and append a run record to the monitoring log.

    Parameters
    ----------
    df : pd.DataFrame
        Scored California grid DataFrame (output of calculate_grid_stress_index).
    source_file : str, optional
        Path or name of the raw source file used in this run.
    export_dir : str, optional
        Directory for the monitoring summary CSV. Defaults to outputs/monitoring/.

    Returns
    -------
    dict
        The monitoring summary for this run.
    """
    if export_dir is None:
        export_dir = MONITORING_DIR
    os.makedirs(export_dir, exist_ok=True)

    # Highest average stress index authority
    avg_stress_by_auth = df.groupby("balancing_authority")["stress_index"].mean()
    highest_stress_authority = avg_stress_by_auth.idxmax()

    # Largest absolute forecast error
    if "forecast_error_mw" in df.columns:
        largest_forecast_error = round(df["forecast_error_mw"].abs().max(), 1)
    else:
        largest_forecast_error = None

    # Accept the label as-is — callers supply either a filename (CSV mode) or
    # a full "EIA Open Data API - ..." string (API mode).
    source_name = source_file if source_file else DEFAULT_SOURCE_FILE

    summary = {
        "pipeline_run_date": datetime.date.today().isoformat(),
        "total_scored_hours": len(df),
        "high_priority_hours": int((df["review_priority"] == "High Review Priority").sum()),
        "average_stress_index": round(float(df["stress_index"].mean()), 2),
        "peak_demand_mw": float(df["demand_mw"].max()),
        "highest_stress_authority": highest_stress_authority,
        "largest_forecast_error_mw": largest_forecast_error,
        "source_file": source_name,
        "run_status": "success",
    }

    summary_df = pd.DataFrame([summary])
    output_path = os.path.join(export_dir, "daily_monitoring_summary.csv")

    # Append to existing log or create new file
    if os.path.exists(output_path):
        existing = pd.read_csv(output_path)
        summary_df = pd.concat([existing, summary_df], ignore_index=True)

    summary_df.to_csv(output_path, index=False)

    print("[monitoring] Pipeline run summary:")
    for key, val in summary.items():
        print(f"    {key}: {val}")
    print(f"[monitoring] Summary saved: {output_path}")
    return summary


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from fetch_or_load_eia_data import fetch_or_load_eia_data, get_source_label
    from validate_grid_data import validate_grid_data
    from transform_energy_metrics import transform_energy_metrics
    from calculate_grid_stress_index import calculate_grid_stress_index
    df = fetch_or_load_eia_data()
    df, _ = validate_grid_data(df)
    df = transform_energy_metrics(df)
    df = calculate_grid_stress_index(df)
    generate_monitoring_summary(df, source_file=get_source_label())
