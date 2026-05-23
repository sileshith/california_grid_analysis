"""
fetch_or_load_eia_data.py

Entry point for step 1 of the California Grid Operations Intelligence Pipeline.
Supports two ingestion modes controlled by the USE_EIA_API environment variable.

API mode (USE_EIA_API=true):
    Fetches hourly balancing authority data from the EIA Open Data API.
    Requires EIA_API_KEY. Supports date-window parameters EIA_START_DATE
    and EIA_END_DATE. Paginates automatically.

CSV fallback (default, USE_EIA_API not set or false):
    Loads raw EIA-930 data from the local CSV file.
    No API key required. Reproducible for portfolio and offline use.

Environment variables:
    USE_EIA_API     Set to "true" to enable API mode. Default: false.
    EIA_API_KEY     Required for API mode. Never committed or logged.
    EIA_START_DATE  API date-window start. Format: "2026-01-01T00"
    EIA_END_DATE    API date-window end.   Format: "2026-01-31T23"

Both modes return a DataFrame with the same six column schema:
    Balancing Authority, UTC Time at End of Hour, Demand (MW),
    Demand Forecast (MW), Net Generation (MW), Total Interchange (MW)

Data source (CSV fallback):
    EIA Form EIA-930, Balancing Authority Hourly Operations
    Download: https://www.eia.gov/electricity/gridmonitor/
"""

import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "EIA930_BALANCE_2026_Jan_Jun.csv")


def get_source_label(file_path=None):
    """
    Return a human-readable data source identifier for the monitoring summary.

    CSV mode:  filename only, e.g. "EIA930_BALANCE_2026_Jan_Jun.csv"
    API mode:  "EIA Open Data API - electricity/rto/region-data"
    """
    use_api = os.getenv("USE_EIA_API", "false").strip().lower() == "true"
    if use_api:
        route = os.getenv(
            "EIA_API_ROUTE",
            "https://api.eia.gov/v2/electricity/rto/region-data/data/",
        )
        # Strip base URL and trailing /data/ for a compact, readable label
        label = route.replace("https://api.eia.gov/v2/", "").rstrip("/")
        if label.endswith("/data"):
            label = label[:-5]
        return f"EIA Open Data API - {label}"
    else:
        if file_path is None:
            file_path = RAW_DATA_PATH
        return os.path.basename(file_path)


def _load_csv_fallback(file_path):
    """Load raw EIA-930 data from the local CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Raw data file not found: {file_path}\n"
            "Download EIA-930 data from https://www.eia.gov/electricity/gridmonitor/ "
            "and place it at data/raw/EIA930_BALANCE_2026_Jan_Jun.csv"
        )
    print(f"[fetch] Loading raw EIA-930 data from: {os.path.basename(file_path)}")
    df = pd.read_csv(file_path, low_memory=False)
    print(f"[fetch] Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def fetch_or_load_eia_data(file_path=None):
    """
    Load raw EIA-930 balancing authority hourly data.

    Checks USE_EIA_API environment variable to select ingestion mode:
    - "true":     fetches from EIA Open Data API (requires EIA_API_KEY)
    - otherwise:  loads from local CSV file (default, reproducible)

    Both modes return a DataFrame with the same six-column schema that
    validate_grid_data.py and transform_energy_metrics.py expect.

    Parameters
    ----------
    file_path : str, optional
        Path to the raw CSV file for fallback mode only.
        Defaults to data/raw/EIA930_BALANCE_2026_Jan_Jun.csv.

    Returns
    -------
    pd.DataFrame
        Raw EIA-930 data with source column names intact.

    Raises
    ------
    FileNotFoundError
        If CSV fallback file is not found (CSV mode only).
    ValueError
        If EIA_API_KEY is not set in the environment (API mode only).
    """
    # API mode is controlled by USE_EIA_API and EIA_API_KEY environment variables.
    # Local CSV fallback remains the default for reproducible portfolio runs.
    use_api = os.getenv("USE_EIA_API", "false").strip().lower() == "true"

    if use_api:
        print("[fetch] USE_EIA_API=true - fetching EIA data from Open Data API")
        from fetch_eia_api_data import (
            get_eia_api_config,
            fetch_eia_api_data,
            normalize_eia_api_response,
            save_api_raw_snapshot,
        )
        config = get_eia_api_config()
        df_raw = fetch_eia_api_data(config)
        save_api_raw_snapshot(df_raw, label="raw")
        df = normalize_eia_api_response(df_raw)
        save_api_raw_snapshot(df, label="normalized")
        return df
    else:
        print("[fetch] USE_EIA_API not enabled - loading local CSV fallback")
        if file_path is None:
            file_path = RAW_DATA_PATH
        return _load_csv_fallback(file_path)


if __name__ == "__main__":
    df = fetch_or_load_eia_data()
    print(df[["Balancing Authority", "UTC Time at End of Hour", "Demand (MW)"]].head())
