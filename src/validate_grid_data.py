"""
validate_grid_data.py

Validate raw EIA-930 data before transformation.
Checks for required columns, California balancing authority presence,
minimum row count, and basic data quality expectations.

This is step 2 in the California Grid Operations Intelligence Pipeline.
"""

import pandas as pd

CALIFORNIA_AUTHORITIES = ["BANC", "CISO", "IID", "LDWP", "TIDC"]

REQUIRED_RAW_COLUMNS = [
    "Balancing Authority",
    "UTC Time at End of Hour",
    "Demand Forecast (MW)",
    "Demand (MW)",
    "Net Generation (MW)",
    "Total Interchange (MW)",
]


def validate_grid_data(df):
    """
    Validate that the raw DataFrame has the expected structure for pipeline processing.

    Checks performed:
    - All required source columns are present
    - At least one California balancing authority is found in the data
    - DataFrame is not empty

    Parameters
    ----------
    df : pd.DataFrame
        Raw EIA-930 DataFrame returned by fetch_or_load_eia_data.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        The original DataFrame (unchanged) and a validation report dictionary.

    Raises
    ------
    ValueError
        If any critical validation check fails.
    """
    report = {}
    errors = []

    # Check required columns
    missing_columns = [c for c in REQUIRED_RAW_COLUMNS if c not in df.columns]
    report["required_columns_present"] = len(missing_columns) == 0
    if missing_columns:
        errors.append(f"Missing required source columns: {missing_columns}")

    # Check that California authorities are present
    if "Balancing Authority" in df.columns:
        all_authorities = set(df["Balancing Authority"].unique())
        ca_found = [a for a in CALIFORNIA_AUTHORITIES if a in all_authorities]
        report["california_authorities_found"] = ca_found
        report["total_authorities_in_file"] = len(all_authorities)
        if len(ca_found) == 0:
            errors.append("No California balancing authorities found in source data.")
    else:
        ca_found = []
        report["california_authorities_found"] = []

    # Check row count
    report["total_rows"] = len(df)
    if len(df) == 0:
        errors.append("Source DataFrame is empty.")

    if errors:
        raise ValueError("[validate] Validation failed:\n" + "\n".join(errors))

    print(f"[validate] Passed: {len(df):,} rows | CA authorities found: {ca_found}")
    return df, report


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from fetch_or_load_eia_data import fetch_or_load_eia_data
    df = fetch_or_load_eia_data()
    _, report = validate_grid_data(df)
    print(report)
