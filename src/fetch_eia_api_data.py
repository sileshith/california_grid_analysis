"""
fetch_eia_api_data.py

EIA Open Data API ingestion for the California Grid Operations Intelligence Pipeline.

Route used:
    https://api.eia.gov/v2/electricity/rto/region-data/data/

This is the correct route for BA-level hourly operations data (demand, demand forecast,
net generation, total interchange) for BANC, CISO, IID, LDWP, and TIDC.

Note: region-sub-ba-data/data/ covers sub-BA planning areas, not the main BAs listed
above. Requests to that route with D/DF/NG/TI type codes return HTTP 400.

Response format:
    Long-format: one row per (period, respondent, type). The type column holds the
    measurement code (D, DF, NG, TI). This module pivots to wide format before
    returning so the output matches the existing CSV-based downstream schema.

Type codes used:
    D  - Demand (megawatthours)
    DF - Demand Forecast (megawatthours)
    NG - Net Generation (megawatthours)
    TI - Total Interchange (megawatthours)

Environment variables:
    EIA_API_KEY           Required when USE_EIA_API=true. Never committed or logged.
    EIA_START_DATE        Date-window start: "YYYY-MM-DDTHH" (e.g. "2026-01-01T00")
    EIA_END_DATE          Date-window end:   "YYYY-MM-DDTHH" (e.g. "2026-01-31T23")
    EIA_API_ROUTE         Full API route URL (default: region-data/data/ route)
    EIA_API_PAGE_SIZE     Rows per page (default: 5000; EIA max is 5000)
    SAVE_EIA_API_SNAPSHOT If "true", saves CSV snapshots to data/interim/ for
                          debugging. Snapshots are gitignored. Default: false.

Period timezone assumption:
    The EIA v2 region-data/data/ route returns period in "YYYY-MM-DDTHH" format in UTC.
    This module parses period as UTC and assigns it to "UTC Time at End of Hour" to
    match the existing CSV-based schema. If live testing shows the API returns local
    Pacific time, update _parse_period_to_utc_string() to localize and convert to UTC.
"""

import os
import time

import pandas as pd
import requests

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DEFAULT_EIA_API_ROUTE = (
    "https://api.eia.gov/v2/electricity/rto/region-data/data/"
)
DEFAULT_PAGE_SIZE = 5000

CALIFORNIA_AUTHORITIES = ["BANC", "CISO", "IID", "LDWP", "TIDC"]

# Type codes to request from the EIA API
EIA_TYPE_CODES = ["D", "DF", "NG", "TI"]

# Maps EIA type codes to downstream column names expected by validate_grid_data.py
TYPE_TO_COLUMN_MAP = {
    "D":  "Demand (MW)",
    "DF": "Demand Forecast (MW)",
    "NG": "Net Generation (MW)",
    "TI": "Total Interchange (MW)",
}


def redact_sensitive_params(params):
    """
    Return a copy of params with the api_key value replaced by ***REDACTED***.

    Used to build safe error messages and log output that can be shown to users
    without exposing credentials.

    Parameters
    ----------
    params : list of (str, str) tuples, or dict

    Returns
    -------
    Same type as input, with api_key values replaced.
    """
    if isinstance(params, list):
        return [
            (k, "***REDACTED***" if k == "api_key" else v)
            for k, v in params
        ]
    if isinstance(params, dict):
        return {
            k: ("***REDACTED***" if k == "api_key" else v)
            for k, v in params.items()
        }
    return params


def get_eia_api_config():
    """
    Read EIA API configuration from environment variables.

    Returns
    -------
    dict with keys: api_key, route, start, end, page_size

    Raises
    ------
    ValueError
        If EIA_API_KEY is not set in the environment.
    """
    api_key = os.getenv("EIA_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "[eia_api] EIA_API_KEY environment variable is not set.\n"
            "Set it before enabling API mode:\n"
            "  export EIA_API_KEY='your_api_key_here'\n"
            "Register for a free key at: https://www.eia.gov/opendata/register.php"
        )
    return {
        "api_key":   api_key,
        "route":     os.getenv("EIA_API_ROUTE", DEFAULT_EIA_API_ROUTE),
        "start":     os.getenv("EIA_START_DATE", "").strip(),
        "end":       os.getenv("EIA_END_DATE", "").strip(),
        "page_size": int(os.getenv("EIA_API_PAGE_SIZE", str(DEFAULT_PAGE_SIZE))),
    }


def build_eia_request_params(api_key, start="", end="", offset=0, page_size=DEFAULT_PAGE_SIZE):
    """
    Build the parameter list for one EIA API request to region-data/data/.

    The EIA v2 API uses array-style query parameters. Passing a list of tuples
    to requests.get() encodes them correctly:
        data[]=value
        facets[type][]=D&facets[type][]=DF&facets[type][]=NG&facets[type][]=TI
        facets[respondent][]=BANC&facets[respondent][]=CISO&...

    For region-data/data/:
    - data[]=value requests the measurement value column.
    - facets[type][] filters by measurement type code (D, DF, NG, TI).
    - facets[respondent][] filters by balancing authority code.

    Parameters
    ----------
    api_key   : str - EIA API key (included in request, never printed)
    start     : str - Start period e.g. "2026-01-01T00" (optional)
    end       : str - End period e.g. "2026-01-31T23" (optional)
    offset    : int - Pagination offset (0-based)
    page_size : int - Number of rows to return per page

    Returns
    -------
    list of (str, str) tuples ready for requests.get(params=...)
    """
    params = [
        ("api_key",            api_key),
        ("frequency",          "hourly"),
        ("data[]",             "value"),
        ("sort[0][column]",    "period"),
        ("sort[0][direction]", "asc"),
        ("offset",             str(offset)),
        ("length",             str(page_size)),
    ]

    # Filter by measurement type codes
    for type_code in EIA_TYPE_CODES:
        params.append(("facets[type][]", type_code))

    # Filter to California balancing authorities
    for authority in CALIFORNIA_AUTHORITIES:
        params.append(("facets[respondent][]", authority))

    if start:
        params.append(("start", start))
    if end:
        params.append(("end", end))

    return params


def fetch_eia_api_page(route, params):
    """
    Fetch one page of data from the EIA Open Data API.

    Does NOT call response.raise_for_status() because that embeds the full
    request URL (which contains api_key=...) in the HTTPError traceback.
    Instead, checks response.ok and builds a sanitized RuntimeError.

    Parameters
    ----------
    route  : str  - Full API route URL
    params : list - List of (key, value) tuples

    Returns
    -------
    dict - Parsed JSON response body

    Raises
    ------
    RuntimeError
        On network error or non-2xx HTTP status. Error message contains
        route, status code, and redacted params — never the api_key value.
    ValueError
        If the response JSON does not contain the expected "response" key.
    """
    try:
        response = requests.get(route, params=params, timeout=60)
    except requests.exceptions.RequestException as exc:
        # Re-raise without chaining to avoid embedding the request URL in the traceback
        raise RuntimeError(
            f"[eia_api] Network error contacting EIA API.\n"
            f"Route: {route}\n"
            f"Error: {type(exc).__name__}"
        ) from None

    if not response.ok:
        safe_params = redact_sensitive_params(params)
        raise RuntimeError(
            f"[eia_api] EIA API returned HTTP {response.status_code}.\n"
            f"Route: {route}\n"
            f"Response body: {response.text[:500]}\n"
            f"Parameters (api_key redacted): {safe_params}"
        )

    body = response.json()
    if "response" not in body:
        raise ValueError(
            "[eia_api] Unexpected API response structure. "
            f"Expected top-level 'response' key. Got: {list(body.keys())}\n"
            "Check that EIA_API_ROUTE points to a valid EIA v2 data endpoint."
        )
    return body


def fetch_eia_api_data(config):
    """
    Fetch all pages of EIA hourly data for the configured date range and authorities.

    Paginates using offset+length until the returned row count is less than page_size.
    Adds a 0.25-second delay between pages as a courtesy to the EIA API.

    Parameters
    ----------
    config : dict - Output of get_eia_api_config()

    Returns
    -------
    pd.DataFrame - Raw long-format API rows (not yet normalized)

    Raises
    ------
    ValueError
        If the API returns no data rows after all pages are fetched.
    """
    route     = config["route"]
    api_key   = config["api_key"]
    start     = config["start"]
    end       = config["end"]
    page_size = config["page_size"]

    # Log route, date range, and authorities — never the API key
    print(f"[eia_api] Route: {route}")
    print(f"[eia_api] Authorities: {CALIFORNIA_AUTHORITIES}")
    print(f"[eia_api] Type codes: {EIA_TYPE_CODES}")
    if start:
        print(f"[eia_api] Start: {start}")
    if end:
        print(f"[eia_api] End: {end}")
    print(f"[eia_api] Page size: {page_size}")

    all_rows = []
    offset   = 0

    while True:
        params = build_eia_request_params(
            api_key=api_key,
            start=start,
            end=end,
            offset=offset,
            page_size=page_size,
        )
        body = fetch_eia_api_page(route, params)
        rows = body["response"].get("data", [])

        if not rows:
            break

        all_rows.extend(rows)
        print(
            f"[eia_api] Page offset={offset} | "
            f"rows this page={len(rows)} | "
            f"total so far={len(all_rows):,}"
        )

        if len(rows) < page_size:
            break

        offset += page_size
        time.sleep(0.25)

    if not all_rows:
        raise ValueError(
            "[eia_api] API returned no data rows. "
            "Check EIA_START_DATE, EIA_END_DATE, EIA_API_KEY, and the route. "
            "Verify the date range contains California BA data."
        )

    print(f"[eia_api] Total rows fetched: {len(all_rows):,}")
    return pd.DataFrame(all_rows)


def _parse_period_to_utc_string(period_str):
    """
    Parse an EIA API period string to a UTC timestamp string.

    EIA v2 API returns period as "YYYY-MM-DDTHH" (e.g. "2026-01-01T01").
    Returns "2026-01-01 01:00:00+00:00", which is compatible with
    pd.to_datetime(..., utc=True) used in transform_energy_metrics.py.

    Assumption: period is in UTC. If live testing shows the API returns local
    Pacific time, replace this with timezone-aware localization:
        dt = pd.to_datetime(period_str, format="%Y-%m-%dT%H")
        dt = dt.tz_localize("America/Los_Angeles", ambiguous="NaT")
        return str(dt.tz_convert("UTC"))
    """
    dt = pd.to_datetime(period_str, format="%Y-%m-%dT%H", utc=True)
    return str(dt)


def normalize_eia_api_response(df_raw):
    """
    Convert raw long-format EIA API rows into the schema expected by
    validate_grid_data.py and transform_energy_metrics.py.

    The region-data/data/ route returns long-format data:
        period | respondent | type | value
        one row per (period, respondent, type combination)

    This function pivots to wide format and renames columns to match
    the six-column schema the downstream pipeline expects (same as CSV):
        "Balancing Authority"     - BA code: BANC, CISO, IID, LDWP, TIDC
        "UTC Time at End of Hour" - UTC timestamp string
        "Demand (MW)"             - numeric (from type=D)
        "Demand Forecast (MW)"    - numeric (from type=DF)
        "Net Generation (MW)"     - numeric (from type=NG)
        "Total Interchange (MW)"  - numeric (from type=TI)

    Parameters
    ----------
    df_raw : pd.DataFrame - Raw long-format rows from fetch_eia_api_data()

    Returns
    -------
    pd.DataFrame - Wide-format DataFrame with downstream CSV column names

    Raises
    ------
    ValueError
        If required long-format fields (period, respondent, type, value) are missing.
    """
    required_fields = ["respondent", "period", "type", "value"]
    missing = [f for f in required_fields if f not in df_raw.columns]
    if missing:
        raise ValueError(
            f"[eia_api] API response is missing expected long-format fields: {missing}\n"
            f"Fields in response: {list(df_raw.columns)}\n"
            "Expected route: region-data/data/ with data[]=value and "
            "facets[type][]=D/DF/NG/TI."
        )

    df = df_raw.copy()

    # Keep only the four type codes needed downstream
    df = df[df["type"].isin(EIA_TYPE_CODES)].copy()

    if df.empty:
        raise ValueError(
            f"[eia_api] No rows with type codes {EIA_TYPE_CODES} found in API response. "
            f"Types present: {df_raw['type'].unique().tolist()}"
        )

    # Convert value to numeric — API may return strings or None
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Parse period to UTC timestamp string
    df["period_utc"] = df["period"].apply(_parse_period_to_utc_string)

    # Pivot long -> wide: one row per (respondent, period_utc), type codes become columns
    df_wide = df.pivot_table(
        index=["respondent", "period_utc"],
        columns="type",
        values="value",
        aggfunc="first",
    ).reset_index()
    df_wide.columns.name = None

    # Rename to downstream column names
    rename_map = {
        "respondent":  "Balancing Authority",
        "period_utc":  "UTC Time at End of Hour",
        **TYPE_TO_COLUMN_MAP,
    }
    df_wide = df_wide.rename(columns=rename_map)

    # Filter to California authorities (defensive — request already filters by facet)
    df_wide = df_wide[df_wide["Balancing Authority"].isin(CALIFORNIA_AUTHORITIES)].copy()

    # Keep only the six downstream columns (graceful if a type code was absent)
    output_cols = [
        "Balancing Authority",
        "UTC Time at End of Hour",
        "Demand (MW)",
        "Demand Forecast (MW)",
        "Net Generation (MW)",
        "Total Interchange (MW)",
    ]
    available = [c for c in output_cols if c in df_wide.columns]
    df_wide = df_wide[available].copy()

    print(
        f"[eia_api] Normalized {len(df_wide):,} wide-format rows | "
        f"authorities: {sorted(df_wide['Balancing Authority'].unique().tolist())}"
    )
    return df_wide.reset_index(drop=True)


def save_api_raw_snapshot(df, label="raw"):
    """
    Save an API response snapshot to data/interim/ for debugging.

    Only saves when SAVE_EIA_API_SNAPSHOT=true. The data/interim/ directory
    is gitignored so snapshots are never committed to the repository.

    Parameters
    ----------
    df    : pd.DataFrame - Data to save
    label : str          - Filename label ("raw" or "normalized")
    """
    if os.getenv("SAVE_EIA_API_SNAPSHOT", "false").strip().lower() != "true":
        return

    interim_dir = os.path.join(BASE_DIR, "data", "interim")
    os.makedirs(interim_dir, exist_ok=True)

    ts  = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(interim_dir, f"eia_api_{label}_{ts}.csv")
    df.to_csv(out, index=False)
    print(f"[eia_api] Snapshot saved: {out}")


if __name__ == "__main__":
    config = get_eia_api_config()
    df_raw = fetch_eia_api_data(config)
    df     = normalize_eia_api_response(df_raw)
    print(df[["Balancing Authority", "UTC Time at End of Hour", "Demand (MW)"]].head())
