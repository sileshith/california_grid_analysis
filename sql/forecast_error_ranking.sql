-- forecast_error_ranking.sql
-- California Grid Operations Intelligence Pipeline
--
-- Purpose:
--   Rank hours by absolute forecast error to identify periods of poor forecast
--   accuracy. Supports operational review of balancing authority forecast performance.
--
-- Forecast error interpretation:
--   forecast_error_mw = demand_mw - demand_forecast_mw
--   Positive (+): demand EXCEEDED the forecast (under-forecasting — may require
--                 unplanned imports or emergency reserves)
--   Negative (-): demand FELL BELOW the forecast (over-forecasting — may result
--                 in excess generation or curtailment)
--
-- Window functions used:
--   RANK() OVER (ORDER BY ...)              — overall rank across all authorities
--   RANK() OVER (PARTITION BY ... ORDER BY) — rank within each balancing authority
--
-- Database: PostgreSQL (recommended).
--   Window functions (RANK, PARTITION BY) are native in PostgreSQL.
--   Also compatible with SQLite 3.25+ (2018) which added window function support.

SELECT
    balancing_authority,
    local_time_pacific,
    ROUND(demand_mw::NUMERIC, 1)                                        AS demand_mw,
    ROUND(demand_forecast_mw::NUMERIC, 1)                               AS demand_forecast_mw,
    ROUND(forecast_error_mw::NUMERIC, 1)                                AS forecast_error_mw,
    ROUND(ABS(forecast_error_mw)::NUMERIC, 1)                           AS abs_forecast_error_mw,
    CASE
        WHEN forecast_error_mw > 0 THEN 'Under-Forecast'
        WHEN forecast_error_mw < 0 THEN 'Over-Forecast'
        ELSE 'Exact'
    END                                                                 AS error_direction,
    ROUND(stress_index::NUMERIC, 2)                                     AS stress_index,
    review_priority,
    RANK() OVER (
        ORDER BY ABS(forecast_error_mw) DESC
    )                                                                   AS error_rank_overall,
    RANK() OVER (
        PARTITION BY balancing_authority
        ORDER BY ABS(forecast_error_mw) DESC
    )                                                                   AS error_rank_within_authority
FROM
    grid_hourly_metrics
WHERE
    demand_forecast_mw IS NOT NULL
    AND forecast_error_mw IS NOT NULL
ORDER BY
    abs_forecast_error_mw DESC
LIMIT 100;
