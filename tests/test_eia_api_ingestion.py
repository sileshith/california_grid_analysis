"""
test_eia_api_ingestion.py

Tests for the EIA Open Data API ingestion layer.

All tests are offline — no live network calls are made. API requests are
intercepted with monkeypatch so the test suite passes without an EIA_API_KEY.

Run with:
    pytest tests/test_eia_api_ingestion.py -v
"""

import os
import sys
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fetch_eia_api_data import (
    get_eia_api_config,
    build_eia_request_params,
    fetch_eia_api_data,
    normalize_eia_api_response,
    redact_sensitive_params,
    DEFAULT_EIA_API_ROUTE,
    DEFAULT_PAGE_SIZE,
    CALIFORNIA_AUTHORITIES,
    EIA_TYPE_CODES,
)

# Minimal mock API response rows in long format (one row per period + respondent + type).
# region-data/data/ returns this structure with data[]=value and facets[type][]=D/DF/NG/TI.
MOCK_API_ROWS = [
    {"period": "2026-01-01T01", "respondent": "CISO", "respondent-name": "California ISO",
     "type": "D",  "type-name": "Demand",            "value": "25000", "value-units": "megawatthours"},
    {"period": "2026-01-01T01", "respondent": "CISO", "respondent-name": "California ISO",
     "type": "DF", "type-name": "Demand Forecast",   "value": "24500", "value-units": "megawatthours"},
    {"period": "2026-01-01T01", "respondent": "CISO", "respondent-name": "California ISO",
     "type": "NG", "type-name": "Net Generation",    "value": "20000", "value-units": "megawatthours"},
    {"period": "2026-01-01T01", "respondent": "CISO", "respondent-name": "California ISO",
     "type": "TI", "type-name": "Total Interchange", "value": "-5000", "value-units": "megawatthours"},
    {"period": "2026-01-01T01", "respondent": "BANC", "respondent-name": "Balancing Authority of Northern California",
     "type": "D",  "type-name": "Demand",            "value": "1800",  "value-units": "megawatthours"},
    {"period": "2026-01-01T01", "respondent": "BANC", "respondent-name": "Balancing Authority of Northern California",
     "type": "DF", "type-name": "Demand Forecast",   "value": "1750",  "value-units": "megawatthours"},
    {"period": "2026-01-01T01", "respondent": "BANC", "respondent-name": "Balancing Authority of Northern California",
     "type": "NG", "type-name": "Net Generation",    "value": "1600",  "value-units": "megawatthours"},
    {"period": "2026-01-01T01", "respondent": "BANC", "respondent-name": "Balancing Authority of Northern California",
     "type": "TI", "type-name": "Total Interchange", "value": "100",   "value-units": "megawatthours"},
]


def test_missing_api_key_raises_clear_error(monkeypatch):
    """get_eia_api_config() must raise ValueError with a helpful message when key is absent."""
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    with pytest.raises(ValueError) as exc_info:
        get_eia_api_config()

    msg = str(exc_info.value)
    assert "EIA_API_KEY" in msg, "Error message must mention EIA_API_KEY"
    assert "register" in msg.lower() or "opendata" in msg.lower(), (
        "Error message should point to EIA registration page"
    )


def test_build_eia_request_params_structure():
    """build_eia_request_params() must include all required EIA API parameters."""
    params = build_eia_request_params(
        api_key="test_key_placeholder",
        start="2026-01-01T00",
        end="2026-01-01T23",
        offset=0,
        page_size=500,
    )

    param_dict = {}
    for key, val in params:
        param_dict.setdefault(key, []).append(val)

    # Required fixed parameters
    assert param_dict.get("frequency") == ["hourly"], "frequency must be hourly"
    assert param_dict.get("sort[0][column]") == ["period"], "must sort by period"
    assert param_dict.get("sort[0][direction]") == ["asc"], "must sort ascending"
    assert param_dict.get("offset") == ["0"], "offset must be present"
    assert param_dict.get("length") == ["500"], "length must equal page_size"

    # region-data/data/ uses data[]=value (not data[]=D etc.)
    assert param_dict.get("data[]") == ["value"], (
        "data[] must be 'value' for region-data/data/ long-format endpoint"
    )

    # Date window
    assert param_dict.get("start") == ["2026-01-01T00"], "start must be present"
    assert param_dict.get("end") == ["2026-01-01T23"], "end must be present"

    # Type code filters (facets[type][] not data[])
    type_filters = param_dict.get("facets[type][]", [])
    for code in EIA_TYPE_CODES:
        assert code in type_filters, f"facets[type][] must include type code '{code}'"

    # California authority filters
    authority_filters = param_dict.get("facets[respondent][]", [])
    for authority in CALIFORNIA_AUTHORITIES:
        assert authority in authority_filters, (
            f"facets[respondent][] must include '{authority}'"
        )

    # API key present exactly once
    assert len(param_dict.get("api_key", [])) == 1, "api_key must appear exactly once"


def test_normalize_eia_api_response_schema():
    """normalize_eia_api_response() must produce the exact six-column schema the pipeline expects."""
    df_raw = pd.DataFrame(MOCK_API_ROWS)
    df = normalize_eia_api_response(df_raw)

    expected_columns = [
        "Balancing Authority",
        "UTC Time at End of Hour",
        "Demand (MW)",
        "Demand Forecast (MW)",
        "Net Generation (MW)",
        "Total Interchange (MW)",
    ]
    for col in expected_columns:
        assert col in df.columns, f"Normalized output missing column: '{col}'"

    assert set(df.columns) == set(expected_columns), (
        f"Unexpected extra columns: {set(df.columns) - set(expected_columns)}"
    )

    # 8 long-format rows (2 authorities x 4 types) should pivot to 2 wide rows
    assert len(df) == 2, f"Expected 2 wide-format rows after pivot. Got: {len(df)}"


def test_normalize_eia_api_response_numeric_conversion():
    """normalize_eia_api_response() must convert string numeric fields to float."""
    df_raw = pd.DataFrame(MOCK_API_ROWS)
    df = normalize_eia_api_response(df_raw)

    for col in ["Demand (MW)", "Demand Forecast (MW)", "Net Generation (MW)", "Total Interchange (MW)"]:
        assert pd.api.types.is_numeric_dtype(df[col]), (
            f"Column '{col}' must be numeric after normalization"
        )

    ciso_row = df[df["Balancing Authority"] == "CISO"].iloc[0]
    assert ciso_row["Demand (MW)"] == 25000.0
    assert ciso_row["Demand Forecast (MW)"] == 24500.0
    assert ciso_row["Total Interchange (MW)"] == -5000.0


def test_csv_fallback_does_not_require_api_key(monkeypatch):
    """When USE_EIA_API is not true, loading the CSV must not require EIA_API_KEY."""
    monkeypatch.delenv("USE_EIA_API", raising=False)
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    import fetch_or_load_eia_data as m

    # FileNotFoundError (CSV missing) confirms the CSV path was taken.
    # ValueError (missing API key) would mean the API path was incorrectly taken.
    with pytest.raises(FileNotFoundError):
        m.fetch_or_load_eia_data(file_path="/nonexistent/path/eia.csv")


def test_api_fetch_uses_pagination_mocked(monkeypatch):
    """fetch_eia_api_data() must paginate correctly and stop when a page returns fewer rows than page_size."""
    import requests

    call_count = [0]

    def mock_get(url, params, timeout):
        call_count[0] += 1
        # First call: returns exactly page_size rows (triggers page 2)
        # Second call: returns 0 rows (ends pagination)
        rows = MOCK_API_ROWS if call_count[0] == 1 else []

        class MockResponse:
            ok = True
            status_code = 200
            def json(self):
                return {"response": {"data": rows}}

        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    config = {
        "api_key":   "test_key_placeholder",
        "route":     DEFAULT_EIA_API_ROUTE,
        "start":     "",
        "end":       "",
        "page_size": len(MOCK_API_ROWS),  # page_size == row count so first page triggers page 2
    }

    df = fetch_eia_api_data(config)

    assert call_count[0] == 2, (
        f"Expected 2 API calls (one full page + one empty). Got: {call_count[0]}"
    )
    assert len(df) == len(MOCK_API_ROWS), (
        f"Expected {len(MOCK_API_ROWS)} rows from the first page. Got: {len(df)}"
    )


def test_no_api_key_in_logs(monkeypatch, capsys):
    """fetch_eia_api_data() must not print the API key in any log output."""
    import requests

    fake_key = "FAKE_SECRET_API_KEY_12345"

    def mock_get(url, params, timeout):
        class MockResponse:
            ok = True
            status_code = 200
            def json(self):
                return {"response": {"data": []}}
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    config = {
        "api_key":   fake_key,
        "route":     DEFAULT_EIA_API_ROUTE,
        "start":     "2026-01-01T00",
        "end":       "2026-01-01T23",
        "page_size": DEFAULT_PAGE_SIZE,
    }

    with pytest.raises(ValueError):
        fetch_eia_api_data(config)

    captured = capsys.readouterr()
    assert fake_key not in captured.out, "API key must not appear in stdout"
    assert fake_key not in captured.err, "API key must not appear in stderr"


def test_api_key_redacted_in_http_error(monkeypatch):
    """RuntimeError raised on HTTP 4xx/5xx must not contain the API key value."""
    import requests

    fake_key = "FAKE_SECRET_API_KEY_99999"

    def mock_get(url, params, timeout):
        class MockResponse:
            ok = False
            status_code = 400
            text = '{"error": "Invalid parameter combination"}'
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    config = {
        "api_key":   fake_key,
        "route":     DEFAULT_EIA_API_ROUTE,
        "start":     "2026-01-01T00",
        "end":       "2026-01-01T23",
        "page_size": DEFAULT_PAGE_SIZE,
    }

    with pytest.raises(RuntimeError) as exc_info:
        fetch_eia_api_data(config)

    err_msg = str(exc_info.value)
    assert fake_key not in err_msg, (
        "API key must not appear in the HTTP error message"
    )
    assert "400" in err_msg, "Error message must include the HTTP status code"
    assert "REDACTED" in err_msg, "Error message must show ***REDACTED*** where api_key was"


def test_redact_sensitive_params_replaces_key():
    """redact_sensitive_params() must replace api_key with ***REDACTED*** and leave other params unchanged."""
    params = [
        ("api_key",   "my_real_secret_key"),
        ("frequency", "hourly"),
        ("data[]",    "value"),
    ]

    redacted = redact_sensitive_params(params)
    redacted_dict = dict(redacted)

    assert redacted_dict["api_key"] == "***REDACTED***", (
        "api_key value must be replaced with ***REDACTED***"
    )
    assert redacted_dict["frequency"] == "hourly", "non-sensitive params must be unchanged"
    assert "my_real_secret_key" not in str(redacted), (
        "Original api_key value must not appear anywhere in redacted output"
    )
