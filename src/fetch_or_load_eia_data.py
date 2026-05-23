"""
fetch_or_load_eia_data.py

Load raw EIA-930 balancing authority hourly data from a local CSV file.
This is the first step in the California Grid Operations Intelligence Pipeline.

Data source: EIA Form EIA-930, Balancing Authority Hourly Operations
Download: https://www.eia.gov/electricity/gridmonitor/
"""

import os
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "EIA930_BALANCE_2026_Jan_Jun.csv")


def fetch_or_load_eia_data(file_path=None):
    """
    Load the raw EIA-930 CSV from disk and return a DataFrame.

    Parameters
    ----------
    file_path : str, optional
        Path to the raw CSV file. Defaults to data/raw/EIA930_BALANCE_2026_Jan_Jun.csv.

    Returns
    -------
    pd.DataFrame
        Raw EIA-930 data with all source columns intact.

    Raises
    ------
    FileNotFoundError
        If the raw data file is not found at the expected path.
    """
    if file_path is None:
        file_path = RAW_DATA_PATH

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


if __name__ == "__main__":
    df = fetch_or_load_eia_data()
    print(df[["Balancing Authority", "UTC Time at End of Hour", "Demand (MW)"]].head())
