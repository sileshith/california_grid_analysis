-- authority_comparison.sql
-- California Grid Operations Intelligence Pipeline
--
-- Purpose:
--   One-row-per-authority summary of key operational metrics for side-by-side
--   comparison. Supports the Authority Comparison tab in the Tableau dashboard
--   and executive-level cross-authority reporting.
--
-- Balancing authorities covered:
--   BANC  — Balancing Authority of Northern California
--   CISO  — California Independent System Operator (largest)
--   IID   — Imperial Irrigation District
--   LDWP  — Los Angeles Department of Water and Power
--   TIDC  — Turlock Irrigation District
--
-- Note on cross-authority comparison:
--   Authorities operate at very different MW scales. CISO manages tens of
--   thousands of MW; IID and TIDC operate at hundreds of MW. avg_stress_index
--   normalizes each authority against its own observed peak demand, enabling
--   fair cross-scale comparison. Raw MW values are NOT directly comparable
--   across authorities at different scales.
--
-- Database: PostgreSQL (recommended); also compatible with SQLite fallback.

SELECT
    balancing_authority,

    -- Volume metrics
    COUNT(*)                                                                    AS total_hours,
    ROUND(AVG(demand_mw)::NUMERIC, 1)                                           AS avg_demand_mw,
    ROUND(MAX(demand_mw)::NUMERIC, 1)                                           AS peak_demand_mw,
    ROUND(MIN(demand_mw)::NUMERIC, 1)                                           AS min_demand_mw,

    -- Supply and interchange metrics
    ROUND(AVG(net_generation_mw)::NUMERIC, 1)                                   AS avg_net_generation_mw,
    ROUND(AVG(total_interchange_mw)::NUMERIC, 1)                                AS avg_interchange_mw,

    -- Stress metrics (normalized — valid for cross-authority comparison)
    ROUND(AVG(stress_index)::NUMERIC, 2)                                        AS avg_stress_index,
    ROUND(MAX(stress_index)::NUMERIC, 2)                                        AS peak_stress_index,

    -- Forecast accuracy
    ROUND(AVG(ABS(forecast_error_mw))::NUMERIC, 1)                             AS avg_abs_forecast_error_mw,
    ROUND(MAX(ABS(forecast_error_mw))::NUMERIC, 1)                             AS max_abs_forecast_error_mw,

    -- Review priority distribution (counts)
    SUM(CASE WHEN review_priority = 'High Review Priority'   THEN 1 ELSE 0 END) AS high_priority_hours,
    SUM(CASE WHEN review_priority = 'Medium Review Priority' THEN 1 ELSE 0 END) AS medium_priority_hours,
    SUM(CASE WHEN review_priority = 'Low Review Priority'    THEN 1 ELSE 0 END) AS low_priority_hours,

    -- Review priority distribution (percentages)
    ROUND(
        (100.0 * SUM(CASE WHEN review_priority = 'High Review Priority' THEN 1 ELSE 0 END)
        / COUNT(*))::NUMERIC, 2
    )                                                                           AS pct_high_priority,
    ROUND(
        (100.0 * SUM(CASE WHEN review_priority = 'Medium Review Priority' THEN 1 ELSE 0 END)
        / COUNT(*))::NUMERIC, 2
    )                                                                           AS pct_medium_priority

FROM
    grid_hourly_metrics
GROUP BY
    balancing_authority
ORDER BY
    avg_stress_index DESC;
