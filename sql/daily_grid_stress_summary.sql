-- daily_grid_stress_summary.sql
-- California Grid Operations Intelligence Pipeline
--
-- Purpose:
--   Aggregate hourly grid metrics into a daily stress summary by balancing authority.
--   Supports the Executive Overview tab in the Tableau dashboard and
--   ad hoc operational reporting.
--
-- Output fields:
--   balancing_authority   — BANC, CISO, IID, LDWP, TIDC
--   report_date           — calendar date (YYYY-MM-DD)
--   total_hours           — hourly records for that day
--   avg_demand_mw         — mean hourly demand
--   peak_demand_mw        — highest single-hour demand
--   avg_stress_index      — mean stress index for the day
--   max_stress_index      — peak stress index hour
--   high_priority_hours   — count of hours with stress_index >= 90
--   medium_priority_hours — count of hours with stress_index >= 75 and < 90
--   low_priority_hours    — count of hours with stress_index < 75
--
-- Database: PostgreSQL (recommended)
-- local_time_pacific is stored as TEXT in ISO 8601 format (e.g. "2026-03-15 14:00:00-07:00").
-- LEFT(local_time_pacific, 10) extracts the YYYY-MM-DD portion and is compatible
-- with both PostgreSQL and the SQLite fallback.
--
-- PostgreSQL users can optionally cast to DATE:
--   CAST(LEFT(local_time_pacific, 10) AS DATE) AS report_date

SELECT
    balancing_authority,
    LEFT(local_time_pacific, 10)                                        AS report_date,
    COUNT(*)                                                            AS total_hours,
    ROUND(AVG(demand_mw)::NUMERIC, 1)                                   AS avg_demand_mw,
    ROUND(MAX(demand_mw)::NUMERIC, 1)                                   AS peak_demand_mw,
    ROUND(AVG(stress_index)::NUMERIC, 2)                                AS avg_stress_index,
    ROUND(MAX(stress_index)::NUMERIC, 2)                                AS max_stress_index,
    SUM(CASE WHEN review_priority = 'High Review Priority'   THEN 1 ELSE 0 END) AS high_priority_hours,
    SUM(CASE WHEN review_priority = 'Medium Review Priority' THEN 1 ELSE 0 END) AS medium_priority_hours,
    SUM(CASE WHEN review_priority = 'Low Review Priority'    THEN 1 ELSE 0 END) AS low_priority_hours
FROM
    grid_hourly_metrics
GROUP BY
    balancing_authority,
    LEFT(local_time_pacific, 10)
ORDER BY
    report_date DESC,
    balancing_authority;
