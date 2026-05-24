"""
load_results_to_sql.py

Load the scored California grid metrics into a database.

PostgreSQL is the recommended database for this pipeline. Connection is
configured through the DATABASE_URL environment variable (a standard SQLAlchemy
connection string). If DATABASE_URL is not set, the pipeline falls back to a
local SQLite file at outputs/grid_operations.db for quick local demonstration.

Tables written on each run (if_exists='replace'):
    grid_hourly_metrics        — full hourly scored dataset (all columns)
    grid_stress_scores         — stress index and priority for fast queries
    high_priority_review_queue — only High Review Priority hours (stress_index >= 90)

DATABASE_URL configuration:
    PostgreSQL (recommended for the portfolio pipeline):
        export DATABASE_URL="postgresql+psycopg2://username:password@localhost:5432/california_grid"

    SQLite fallback (no DATABASE_URL set — quick local demo only):
        Writes to: outputs/grid_operations.db

Do not hardcode credentials in this file. Use a .env file (gitignored) loaded
with python-dotenv, or inject DATABASE_URL through the shell environment.

This is step 5 in the California Grid Operations Intelligence Pipeline.
"""

import os
import sqlite3
from contextlib import contextmanager
import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SQLITE_FALLBACK_PATH = os.path.join(BASE_DIR, "outputs", "grid_operations.db")

HOURLY_COLS = [
    "balancing_authority",
    "local_time_pacific",
    "demand_mw",
    "demand_forecast_mw",
    "net_generation_mw",
    "total_interchange_mw",
    "forecast_error_mw",
    "generation_demand_gap_mw",
    "import_pressure_mw",
    "stress_index",
    "review_priority",
    "peak_demand_mw",
]

STRESS_COLS = [
    "balancing_authority",
    "local_time_pacific",
    "demand_mw",
    "stress_index",
    "review_priority",
    "peak_demand_mw",
]


def _build_engine():
    """
    Build a SQLAlchemy engine from DATABASE_URL if set, else SQLite fallback.

    Returns (engine, db_label). Does not log the connection string or credentials.
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print("[sql] Using PostgreSQL database from DATABASE_URL")
        return create_engine(db_url), "postgresql"
    else:
        print("[sql] DATABASE_URL not set — using local SQLite fallback (outputs/grid_operations.db)")
        os.makedirs(os.path.dirname(SQLITE_FALLBACK_PATH), exist_ok=True)
        return create_engine(f"sqlite:///{SQLITE_FALLBACK_PATH}"), "sqlite"


@contextmanager
def _write_connection(engine, db_label):
    """
    Yield a pandas-compatible connection for to_sql().

    SQLite uses a native sqlite3.connect() because SQLAlchemy 2.0 removed the
    Connectable ABC, which causes pandas 2.x to misroute a SQLAlchemy Connection
    to the DBAPI code path and call .cursor() on it — raising AttributeError.
    A raw sqlite3 connection is unambiguous to all pandas versions.

    PostgreSQL uses engine.begin() (SQLAlchemy connection with auto-commit),
    which works correctly with psycopg2 across pandas 1.x and 2.x.
    """
    if db_label == "sqlite":
        conn = sqlite3.connect(SQLITE_FALLBACK_PATH)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    else:
        with engine.begin() as conn:
            yield conn


def load_results_to_sql(df):
    """
    Load the scored grid DataFrame into the configured database.

    Reads DATABASE_URL from the environment:
        - Set  → connects to PostgreSQL (recommended for portfolio use)
        - Unset → falls back to SQLite at outputs/grid_operations.db

    Parameters
    ----------
    df : pd.DataFrame
        Scored California grid DataFrame (output of calculate_grid_stress_index).

    Returns
    -------
    str
        Database backend used: "postgresql" or "sqlite".
    """
    engine, db_label = _build_engine()

    # Serialize timezone-aware timestamp to ISO string for broad database compatibility.
    # PostgreSQL users can ALTER the column to TIMESTAMPTZ after the initial load.
    df_load = df.copy()
    df_load["local_time_pacific"] = df_load["local_time_pacific"].astype(str)

    hourly_available = [c for c in HOURLY_COLS if c in df_load.columns]
    stress_available = [c for c in STRESS_COLS if c in df_load.columns]
    hp = df_load[df_load["review_priority"] == "High Review Priority"]

    with _write_connection(engine, db_label) as conn:
        df_load[hourly_available].to_sql(
            "grid_hourly_metrics", conn, if_exists="replace", index=False
        )
        print(f"[sql] grid_hourly_metrics: {len(df_load):,} rows -> {db_label}")

        df_load[stress_available].to_sql(
            "grid_stress_scores", conn, if_exists="replace", index=False
        )
        print(f"[sql] grid_stress_scores: {len(df_load):,} rows -> {db_label}")

        hp[hourly_available].to_sql(
            "high_priority_review_queue", conn, if_exists="replace", index=False
        )
        print(f"[sql] high_priority_review_queue: {len(hp):,} rows -> {db_label}")

    engine.dispose()
    print(f"[sql] Load complete ({db_label})")
    return db_label


if __name__ == "__main__":
    # Optional: load .env if python-dotenv is installed
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("[sql] .env loaded")
    except ImportError:
        pass

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
    load_results_to_sql(df)
