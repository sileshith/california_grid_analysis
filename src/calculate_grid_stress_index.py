"""
calculate_grid_stress_index.py

Calculate the Grid Stress Index and review-priority classification for each
hourly record in the California grid dataset.

Grid Stress Index formula:
    stress_index = (demand_mw / peak_demand_mw) * 100

Where peak_demand_mw is the highest observed demand for that balancing authority
across the full dataset window. The index expresses how close each hour is to
the observed peak — a value of 100 means the hour IS the peak.

Review priority thresholds:
    High Review Priority   : stress_index >= 90
    Medium Review Priority : stress_index >= 75 and < 90
    Low Review Priority    : stress_index < 75

This is step 4 in the California Grid Operations Intelligence Pipeline.
"""

import pandas as pd

HIGH_PRIORITY_THRESHOLD = 90.0
MEDIUM_PRIORITY_THRESHOLD = 75.0


def calculate_grid_stress_index(df):
    """
    Add stress_index, peak_demand_mw, review_priority, and composite stress metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Transformed California grid DataFrame (output of transform_energy_metrics).

    Returns
    -------
    pd.DataFrame
        Input DataFrame with stress scoring columns:
        - peak_demand_mw: observed peak for each authority
        - stress_index: 0-100 scale (demand / peak × 100)
        - review_priority: High/Medium/Low classification
        - grid_stress_composite: 0-1 weighted composite index
        - grid_stress_level: Low/Moderate/Elevated/High classification
    """
    # Observed peak demand per balancing authority over the full dataset window
    peak_demand = (
        df.groupby("balancing_authority")["demand_mw"]
        .max()
        .rename("peak_demand_mw")
        .reset_index()
    )
    df = df.merge(peak_demand, on="balancing_authority", how="left")

    # Stress Index: demand as a percentage of observed peak (0-100 scale)
    df["stress_index"] = (df["demand_mw"] / df["peak_demand_mw"] * 100).round(2)

    # Review priority classification (based on 0-100 stress_index)
    df["review_priority"] = df["stress_index"].apply(_classify_priority)

    # Composite Grid Stress Index (Step 15) - weighted 0-1 scale
    # Normalize import reliance (already 0-1 from transform step)
    df["normalized_import_reliance"] = df["import_reliance_ratio"].clip(0, 1.0)
    
    # Normalize forecast shock (forecast_error_pct already 0-1 from transform step)
    df["normalized_forecast_shock"] = df["forecast_error_pct"].clip(0, 1.0)
    
    # Weighted composite: 50% demand + 30% import + 20% forecast
    df["grid_stress_composite"] = (
        0.50 * df["normalized_demand"] +
        0.30 * df["normalized_import_reliance"] +
        0.20 * df["normalized_forecast_shock"]
    ).clip(0, 1.0).round(4)
    
    # Grid stress level classification (0-1 scale)
    df["grid_stress_level"] = df["grid_stress_composite"].apply(_classify_stress_level)

    high_count = (df["review_priority"] == "High Review Priority").sum()
    med_count = (df["review_priority"] == "Medium Review Priority").sum()
    elevated_count = (df["grid_stress_level"] == "Elevated").sum()
    high_stress_count = (df["grid_stress_level"] == "High").sum()
    print(
        f"[stress_index] Scored {len(df):,} hours | "
        f"Review Priority - High: {high_count} | Medium: {med_count} | "
        f"Low: {len(df) - high_count - med_count}"
    )
    print(
        f"[stress_composite] Stress Level - High: {high_stress_count} | "
        f"Elevated: {elevated_count} | "
        f"Moderate: {((df['grid_stress_level'] == 'Moderate').sum())} | "
        f"Low: {((df['grid_stress_level'] == 'Low').sum())}"
    )
    return df


def _classify_priority(stress_index):
    """Return review priority label based on stress index value (0-100 scale)."""
    if stress_index >= HIGH_PRIORITY_THRESHOLD:
        return "High Review Priority"
    elif stress_index >= MEDIUM_PRIORITY_THRESHOLD:
        return "Medium Review Priority"
    else:
        return "Low Review Priority"


def _classify_stress_level(composite_score):
    """Return stress level label based on composite score (0-1 scale)."""
    if composite_score >= 0.75:
        return "High"
    elif composite_score >= 0.50:
        return "Elevated"
    elif composite_score >= 0.25:
        return "Moderate"
    else:
        return "Low"


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from fetch_or_load_eia_data import fetch_or_load_eia_data
    from validate_grid_data import validate_grid_data
    from transform_energy_metrics import transform_energy_metrics
    df = fetch_or_load_eia_data()
    df, _ = validate_grid_data(df)
    df = transform_energy_metrics(df)
    df = calculate_grid_stress_index(df)
    print(df[["balancing_authority", "demand_mw", "peak_demand_mw", "stress_index", "review_priority"]].head(10))
