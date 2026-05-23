-- create_tables.sql
-- California Grid Operations Intelligence Pipeline
--
-- PostgreSQL schema definitions for the grid operations database.
-- This is the recommended database for the pipeline.
--
-- To initialize a PostgreSQL database and run this script:
--   createdb california_grid
--   psql california_grid < sql/create_tables.sql
--
-- Connection string pattern (set as environment variable — do not commit credentials):
--   export DATABASE_URL="postgresql+psycopg2://username:password@localhost:5432/california_grid"
--
-- Note on pandas.to_sql():
--   The load_results_to_sql.py module uses pandas to_sql(if_exists='replace'),
--   which creates tables automatically with inferred types. This schema file serves
--   as the authoritative reference for column types and indexes, and can be used
--   for manual database setup or schema documentation.
--
-- SQLite fallback note:
--   When DATABASE_URL is not set, the pipeline falls back to SQLite at
--   outputs/grid_operations.db. SQLite uses TEXT instead of TIMESTAMPTZ,
--   INTEGER PRIMARY KEY AUTOINCREMENT instead of BIGSERIAL, and
--   datetime('now') instead of NOW(). That fallback is for quick local
--   demonstration only and does not require this script.

-- ============================================================
-- Table: grid_hourly_metrics
-- Full hourly scored dataset — the core operational table.
-- One row per balancing authority per hour.
-- ============================================================
CREATE TABLE IF NOT EXISTS grid_hourly_metrics (
    id                        BIGSERIAL    PRIMARY KEY,
    balancing_authority       VARCHAR(10)  NOT NULL,
    local_time_pacific        TEXT         NOT NULL,   -- ISO 8601 with timezone offset (e.g. "2026-03-15 14:00:00-07:00")
    demand_mw                 NUMERIC(10, 1),
    demand_forecast_mw        NUMERIC(10, 1),
    net_generation_mw         NUMERIC(10, 1),
    total_interchange_mw      NUMERIC(10, 1),
    forecast_error_mw         NUMERIC(10, 1),          -- demand_mw - demand_forecast_mw
    generation_demand_gap_mw  NUMERIC(10, 1),          -- demand_mw - net_generation_mw
    import_pressure_mw        NUMERIC(10, 1),          -- generation_demand_gap_mw clipped at 0
    stress_index              NUMERIC(6, 2),            -- (demand_mw / peak_demand_mw) * 100
    review_priority           VARCHAR(30),              -- High / Medium / Low Review Priority
    peak_demand_mw            NUMERIC(10, 1),           -- observed peak for this authority (dataset window)
    created_at                TIMESTAMPTZ  DEFAULT NOW()
);

-- ============================================================
-- Table: grid_stress_scores
-- Lightweight stress index table — fast queries for dashboard filters.
-- ============================================================
CREATE TABLE IF NOT EXISTS grid_stress_scores (
    id                   BIGSERIAL   PRIMARY KEY,
    balancing_authority  VARCHAR(10) NOT NULL,
    local_time_pacific   TEXT        NOT NULL,
    demand_mw            NUMERIC(10, 1),
    stress_index         NUMERIC(6, 2),
    review_priority      VARCHAR(30),
    peak_demand_mw       NUMERIC(10, 1)
);

-- ============================================================
-- Table: high_priority_review_queue
-- Hours with stress_index >= 90 (High Review Priority).
-- Supports the triage tab in the Tableau dashboard.
-- ============================================================
CREATE TABLE IF NOT EXISTS high_priority_review_queue (
    id                        BIGSERIAL    PRIMARY KEY,
    balancing_authority       VARCHAR(10)  NOT NULL,
    local_time_pacific        TEXT         NOT NULL,
    demand_mw                 NUMERIC(10, 1),
    demand_forecast_mw        NUMERIC(10, 1),
    net_generation_mw         NUMERIC(10, 1),
    total_interchange_mw      NUMERIC(10, 1),
    forecast_error_mw         NUMERIC(10, 1),
    generation_demand_gap_mw  NUMERIC(10, 1),
    import_pressure_mw        NUMERIC(10, 1),
    stress_index              NUMERIC(6, 2),
    review_priority           VARCHAR(30),
    peak_demand_mw            NUMERIC(10, 1)
);

-- ============================================================
-- Table: daily_monitoring_summary
-- One row per pipeline run — operational tracking log.
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_monitoring_summary (
    id                        BIGSERIAL    PRIMARY KEY,
    pipeline_run_date         DATE         NOT NULL,
    total_scored_hours        INTEGER,
    high_priority_hours       INTEGER,
    average_stress_index      NUMERIC(6, 2),
    peak_demand_mw            NUMERIC(10, 1),
    highest_stress_authority  VARCHAR(10),
    largest_forecast_error_mw NUMERIC(10, 1),
    source_file               TEXT,
    run_status                VARCHAR(20),
    created_at                TIMESTAMPTZ  DEFAULT NOW()
);

-- ============================================================
-- Indexes for common query patterns
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_hourly_authority ON grid_hourly_metrics(balancing_authority);
CREATE INDEX IF NOT EXISTS idx_hourly_priority  ON grid_hourly_metrics(review_priority);
CREATE INDEX IF NOT EXISTS idx_hourly_time      ON grid_hourly_metrics(local_time_pacific);
CREATE INDEX IF NOT EXISTS idx_stress_authority ON grid_stress_scores(balancing_authority);
CREATE INDEX IF NOT EXISTS idx_hp_authority     ON high_priority_review_queue(balancing_authority);
CREATE INDEX IF NOT EXISTS idx_hp_stress        ON high_priority_review_queue(stress_index);
