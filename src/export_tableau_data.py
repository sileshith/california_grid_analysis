"""
export_tableau_data.py

Export the scored California grid dataset as Tableau-ready CSV files.

Files produced:
    california_grid_dashboard_ready.csv   — full hourly detail (13,020 rows)
    california_grid_monthly_summary.csv   — monthly aggregates by authority
    california_grid_hourly_risk_summary.csv — hour-of-day demand profile
    high_priority_review_queue.csv        — only High Review Priority hours

All files are written to outputs/tableau_exports/.
CSV files are excluded from git by .gitignore; run the pipeline to regenerate them.

This is step 6 in the California Grid Operations Intelligence Pipeline.
"""

import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORT_DIR = os.path.join(BASE_DIR, "outputs", "tableau_exports")

DETAIL_COLS = [
    "balancing_authority",
    "local_time_pacific",
    "demand_mw",
    "demand_forecast_mw",
    "net_generation_mw",
    "total_interchange_mw",
    "stress_index",
    "review_priority",
    "peak_demand_mw",
]


def export_tableau_data(df, export_dir=None):
    """
    Export four Tableau-ready CSV files from the scored grid DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Scored California grid DataFrame (output of calculate_grid_stress_index).
    export_dir : str, optional
        Destination directory. Defaults to outputs/tableau_exports/.

    Returns
    -------
    list[str]
        List of file paths for all exported files.
    """
    if export_dir is None:
        export_dir = EXPORT_DIR
    os.makedirs(export_dir, exist_ok=True)

    exported = []
    detail_cols_available = [c for c in DETAIL_COLS if c in df.columns]

    # 1. Full hourly detail — primary dashboard data source
    detail_path = os.path.join(export_dir, "california_grid_dashboard_ready.csv")
    df[detail_cols_available].to_csv(detail_path, index=False)
    exported.append(detail_path)
    print(f"[export] {len(df):,} rows -> {os.path.basename(detail_path)}")

    # 2. Monthly summary — one row per authority per calendar month
    df_m = df.copy()
    df_m["year_month"] = df_m["local_time_pacific"].dt.strftime("%Y-%m")
    monthly = (
        df_m.groupby(["balancing_authority", "year_month"])
        .agg(
            avg_demand_mw=("demand_mw", "mean"),
            max_demand_mw=("demand_mw", "max"),
            min_demand_mw=("demand_mw", "min"),
            avg_stress_index=("stress_index", "mean"),
            max_stress_index=("stress_index", "max"),
            total_hours=("demand_mw", "count"),
            high_priority_hours=(
                "review_priority", lambda x: (x == "High Review Priority").sum()
            ),
            medium_priority_hours=(
                "review_priority", lambda x: (x == "Medium Review Priority").sum()
            ),
            low_priority_hours=(
                "review_priority", lambda x: (x == "Low Review Priority").sum()
            ),
        )
        .round(2)
        .reset_index()
    )
    monthly_path = os.path.join(export_dir, "california_grid_monthly_summary.csv")
    monthly.to_csv(monthly_path, index=False)
    exported.append(monthly_path)
    print(f"[export] {len(monthly)} rows -> {os.path.basename(monthly_path)}")

    # 3. Hourly risk summary — hour-of-day demand and stress profile
    df_h = df.copy()
    df_h["hour_of_day"] = df_h["local_time_pacific"].dt.hour
    hourly_risk = (
        df_h.groupby(["balancing_authority", "hour_of_day"])
        .agg(
            avg_demand_mw=("demand_mw", "mean"),
            max_demand_mw=("demand_mw", "max"),
            avg_stress_index=("stress_index", "mean"),
            max_stress_index=("stress_index", "max"),
            total_observations=("demand_mw", "count"),
            high_priority_count=(
                "review_priority", lambda x: (x == "High Review Priority").sum()
            ),
            medium_priority_count=(
                "review_priority", lambda x: (x == "Medium Review Priority").sum()
            ),
            low_priority_count=(
                "review_priority", lambda x: (x == "Low Review Priority").sum()
            ),
        )
        .round(2)
        .reset_index()
    )
    hourly_path = os.path.join(export_dir, "california_grid_hourly_risk_summary.csv")
    hourly_risk.to_csv(hourly_path, index=False)
    exported.append(hourly_path)
    print(f"[export] {len(hourly_risk)} rows -> {os.path.basename(hourly_path)}")

    # 4. High-priority review queue — filtered view for the triage tab
    hp = df[df["review_priority"] == "High Review Priority"].copy()
    hp_path = os.path.join(export_dir, "high_priority_review_queue.csv")
    hp[detail_cols_available].to_csv(hp_path, index=False)
    exported.append(hp_path)
    print(f"[export] {len(hp)} high-priority rows -> {os.path.basename(hp_path)}")

    return exported


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from fetch_or_load_eia_data import fetch_or_load_eia_data
    from validate_grid_data import validate_grid_data
    from transform_energy_metrics import transform_energy_metrics
    from calculate_grid_stress_index import calculate_grid_stress_index
    df = fetch_or_load_eia_data()
    df, _ = validate_grid_data(df)
    df = transform_energy_metrics(df)
    df = calculate_grid_stress_index(df)
    export_tableau_data(df)
