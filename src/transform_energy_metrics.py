"""
transform_energy_metrics.py

Transform raw EIA-930 data into a clean California grid metrics dataset.

Steps applied:
1. Fix known column-name typo in the EIA-930 source file
2. Rename core columns to snake_case
3. Drop rows missing balancing authority or demand
4. Deduplicate on authority + timestamp
5. Filter to California balancing authorities only
6. Convert UTC timestamps to Pacific Time (PST/PDT-aware)
7. Engineer operational metrics: forecast_error, generation_demand_gap, import_pressure

This is step 3 in the California Grid Operations Intelligence Pipeline.
"""

import pandas as pd

CALIFORNIA_AUTHORITIES = ["BANC", "CISO", "IID", "LDWP", "TIDC"]

# The EIA-930 source file contains a known column-name typo.
# "witho" should be "without" in the solar-with-battery storage column.
COLUMN_NAME_FIXES = {
    "Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)":
        "Net Generation (MW) from Solar without Integrated Battery Storage (Adjusted)",
}

COLUMN_RENAME_MAP = {
    "Balancing Authority":       "balancing_authority",
    "UTC Time at End of Hour":   "utc_time",
    "Demand Forecast (MW)":      "demand_forecast_mw",
    "Demand (MW)":               "demand_mw",
    "Net Generation (MW)":       "net_generation_mw",
    "Total Interchange (MW)":    "total_interchange_mw",
}


def transform_energy_metrics(df):
    """
    Clean and transform the raw EIA-930 DataFrame into a California-only
    operational metrics dataset with engineered features.

    Parameters
    ----------
    df : pd.DataFrame
        Raw EIA-930 DataFrame (output of validate_grid_data).

    Returns
    -------
    pd.DataFrame
        Transformed DataFrame with 9 columns:
        balancing_authority, utc_time, local_time_pacific,
        demand_mw, demand_forecast_mw, net_generation_mw, total_interchange_mw,
        forecast_error_mw, generation_demand_gap_mw, import_pressure_mw
    """
    # Fix known source column-name typo
    df = df.rename(columns=COLUMN_NAME_FIXES)

    # Rename core columns to snake_case and keep only what we need
    df = df.rename(columns=COLUMN_RENAME_MAP)
    core_cols = list(COLUMN_RENAME_MAP.values())
    available_cols = [c for c in core_cols if c in df.columns]
    df = df[available_cols].copy()

    # Drop rows with missing authority or demand (cannot score them)
    df = df.dropna(subset=["balancing_authority", "demand_mw"])

    # Remove duplicates on authority + timestamp
    df = df.drop_duplicates(subset=["balancing_authority", "utc_time"])

    # Filter to California balancing authorities
    df = df[df["balancing_authority"].isin(CALIFORNIA_AUTHORITIES)].copy()

    # Convert UTC to Pacific Time (handles PST/PDT automatically)
    df["utc_time"] = pd.to_datetime(df["utc_time"], utc=True)
    df["local_time_pacific"] = df["utc_time"].dt.tz_convert("America/Los_Angeles")

    # Feature engineering
    df["forecast_error_mw"] = df["demand_mw"] - df["demand_forecast_mw"]
    df["generation_demand_gap_mw"] = df["demand_mw"] - df["net_generation_mw"]
    # import_pressure: positive when demand exceeds local generation (must import)
    df["import_pressure_mw"] = df["generation_demand_gap_mw"].clip(lower=0)

    print(
        f"[transform] {len(df):,} rows | "
        f"{df['balancing_authority'].nunique()} CA authorities | "
        f"date range: {df['local_time_pacific'].min().date()} to {df['local_time_pacific'].max().date()}"
    )
    return df.reset_index(drop=True)


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from fetch_or_load_eia_data import fetch_or_load_eia_data
    from validate_grid_data import validate_grid_data
    df_raw = fetch_or_load_eia_data()
    df_valid, _ = validate_grid_data(df_raw)
    df_transformed = transform_energy_metrics(df_valid)
    print(df_transformed[["balancing_authority", "local_time_pacific", "demand_mw", "forecast_error_mw"]].head())
