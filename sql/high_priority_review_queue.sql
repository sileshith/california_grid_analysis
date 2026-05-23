-- high_priority_review_queue.sql
-- California Grid Operations Intelligence Pipeline
--
-- Purpose:
--   Return all hours classified as High Review Priority (stress_index >= 90),
--   ranked by stress index for operational triage.
--   Feeds the High-Priority Review Queue tab in the Tableau dashboard.
--
-- Interpretation:
--   Each row represents a single hour where demand reached at least 90% of
--   the observed peak for that balancing authority. These are the hours that
--   deserve first-pass operational review.
--
-- Sort order:
--   stress_index DESC — highest-stress hours appear first
--   demand_mw DESC    — tie-breaker by absolute demand level
--
-- Database: PostgreSQL (recommended); also compatible with SQLite fallback.

SELECT
    balancing_authority,
    local_time_pacific,
    ROUND(demand_mw::NUMERIC, 1)                AS demand_mw,
    ROUND(demand_forecast_mw::NUMERIC, 1)       AS demand_forecast_mw,
    ROUND(net_generation_mw::NUMERIC, 1)        AS net_generation_mw,
    ROUND(total_interchange_mw::NUMERIC, 1)     AS total_interchange_mw,
    ROUND(forecast_error_mw::NUMERIC, 1)        AS forecast_error_mw,
    ROUND(generation_demand_gap_mw::NUMERIC, 1) AS generation_demand_gap_mw,
    ROUND(import_pressure_mw::NUMERIC, 1)       AS import_pressure_mw,
    ROUND(stress_index::NUMERIC, 2)             AS stress_index,
    review_priority,
    ROUND(peak_demand_mw::NUMERIC, 1)           AS peak_demand_mw
FROM
    grid_hourly_metrics
WHERE
    review_priority = 'High Review Priority'
ORDER BY
    stress_index DESC,
    demand_mw DESC;
