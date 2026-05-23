"""
test_pipeline_outputs.py

Validate that pipeline output files are generated correctly.
Checks Tableau export files and the monitoring summary.

Run with:
    pytest tests/test_pipeline_outputs.py -v

These tests check the outputs/ directory. If files don't exist, tests are
skipped — run the pipeline first (src/ modules or the Airflow DAG).
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TABLEAU_EXPORTS_DIR = os.path.join(BASE_DIR, "outputs", "tableau_exports")
MONITORING_DIR = os.path.join(BASE_DIR, "outputs", "monitoring")


def load_csv_or_skip(path, label):
    """Load a CSV file or skip the test if it doesn't exist."""
    if not os.path.exists(path):
        pytest.skip(
            f"{label} not found at: {path}\n"
            "Run the pipeline first: python src/export_tableau_data.py"
        )
    return pd.read_csv(path)


# ── Tableau export tests ──────────────────────────────────────────────────────

def test_dashboard_ready_export_exists_and_nonempty():
    """california_grid_dashboard_ready.csv must exist and contain data."""
    path = os.path.join(TABLEAU_EXPORTS_DIR, "california_grid_dashboard_ready.csv")
    df = load_csv_or_skip(path, "Dashboard-ready export")
    assert len(df) > 0, "Dashboard-ready CSV is empty"


def test_dashboard_ready_has_required_columns():
    """Dashboard-ready export must have stress_index and review_priority."""
    path = os.path.join(TABLEAU_EXPORTS_DIR, "california_grid_dashboard_ready.csv")
    df = load_csv_or_skip(path, "Dashboard-ready export")
    for col in ["stress_index", "review_priority", "balancing_authority", "demand_mw"]:
        assert col in df.columns, f"Missing column: {col}"


def test_high_priority_queue_export_exists():
    """high_priority_review_queue.csv must exist and be non-empty."""
    path = os.path.join(TABLEAU_EXPORTS_DIR, "high_priority_review_queue.csv")
    df = load_csv_or_skip(path, "High-priority queue export")
    assert len(df) > 0, "High-priority queue CSV is empty"


def test_high_priority_queue_contains_only_high_priority():
    """Every row in the high-priority queue must be High Review Priority."""
    path = os.path.join(TABLEAU_EXPORTS_DIR, "high_priority_review_queue.csv")
    df = load_csv_or_skip(path, "High-priority queue export")
    non_high = df[df["review_priority"] != "High Review Priority"]
    assert len(non_high) == 0, (
        f"Found {len(non_high)} non-High-Priority rows in the high-priority queue"
    )


def test_monthly_summary_export_exists():
    """california_grid_monthly_summary.csv must exist and have correct structure."""
    path = os.path.join(TABLEAU_EXPORTS_DIR, "california_grid_monthly_summary.csv")
    df = load_csv_or_skip(path, "Monthly summary export")
    assert len(df) > 0, "Monthly summary CSV is empty"
    assert "year_month" in df.columns, "Monthly summary missing year_month column"
    assert "avg_stress_index" in df.columns, "Monthly summary missing avg_stress_index column"


def test_hourly_risk_summary_export_exists():
    """california_grid_hourly_risk_summary.csv must exist with hour_of_day column."""
    path = os.path.join(TABLEAU_EXPORTS_DIR, "california_grid_hourly_risk_summary.csv")
    df = load_csv_or_skip(path, "Hourly risk summary export")
    assert len(df) > 0, "Hourly risk summary CSV is empty"
    assert "hour_of_day" in df.columns, "Hourly risk summary missing hour_of_day column"


# ── Monitoring summary tests ──────────────────────────────────────────────────

def test_monitoring_summary_exists_and_nonempty():
    """daily_monitoring_summary.csv must exist and contain at least one run record."""
    path = os.path.join(MONITORING_DIR, "daily_monitoring_summary.csv")
    df = load_csv_or_skip(path, "Monitoring summary")
    assert len(df) > 0, "Monitoring summary is empty"


def test_monitoring_summary_required_fields():
    """Monitoring summary must have all required operational fields."""
    path = os.path.join(MONITORING_DIR, "daily_monitoring_summary.csv")
    df = load_csv_or_skip(path, "Monitoring summary")
    required = [
        "pipeline_run_date",
        "total_scored_hours",
        "high_priority_hours",
        "average_stress_index",
        "peak_demand_mw",
        "highest_stress_authority",
        "largest_forecast_error_mw",
        "source_file",
        "run_status",
    ]
    missing = [f for f in required if f not in df.columns]
    assert not missing, f"Monitoring summary missing fields: {missing}"


def test_monitoring_summary_has_successful_run():
    """At least one pipeline run should have run_status == 'success'."""
    path = os.path.join(MONITORING_DIR, "daily_monitoring_summary.csv")
    df = load_csv_or_skip(path, "Monitoring summary")
    success_count = (df["run_status"] == "success").sum()
    assert success_count > 0, "No successful pipeline runs recorded in monitoring summary"


def test_monitoring_summary_stress_index_positive():
    """Average stress index in monitoring log should be a positive number."""
    path = os.path.join(MONITORING_DIR, "daily_monitoring_summary.csv")
    df = load_csv_or_skip(path, "Monitoring summary")
    assert (df["average_stress_index"] > 0).all(), (
        "average_stress_index should be positive in all monitoring records"
    )
