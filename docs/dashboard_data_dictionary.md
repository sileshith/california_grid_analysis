# Dashboard Data Dictionary

**Project:** California Grid Operational Risk Overview
**Date:** 2026-05-03
**Source data:** EIA Form EIA-930, Balancing Authority Hourly Operations, Jan–Apr 2026
**Scope:** California balancing authorities only — BANC, CISO, IID, LDWP, TIDC

---

## How to Read This Dictionary

Each field entry includes:

- **Field name** — the exact column name in the CSV file
- **Data type** — the storage type (string, float, integer, datetime)
- **Description** — what the field represents
- **Example value** — a representative value from the dataset
- **Tableau role** — Dimension or Measure
- **Power BI role** — Column (attribute) or Measure (calculated aggregate)
- **Origin** — Raw (from EIA source), Engineered (calculated in notebook), or Aggregated (computed during summary table build)

---

## Section 1: Dashboard-Ready Hourly Detail Fields

**File:** `data/processed/california_grid_dashboard_ready.csv`
**Rows:** 13,020 **Columns:** 9

These are the only fields needed to power the Tableau dashboard and any
Power BI detailed view. All other EIA source columns are excluded from this file.

---

### balancing_authority

| Attribute | Value |
| --- | --- |
| Data type | String |
| Description | The NERC-assigned code identifying the California balancing authority responsible for the recorded hourly operations. Five values appear in this dataset. |
| Example value | `CISO` |
| Tableau role | Dimension |
| Power BI role | Column |
| Origin | Raw |

**Balancing authority reference:**

| Code | Name |
| --- | --- |
| BANC | Balancing Authority of Northern California |
| CISO | California Independent System Operator |
| IID | Imperial Irrigation District |
| LDWP | Los Angeles Department of Water and Power |
| TIDC | Turlock Irrigation District |

---

### local_time_pacific

| Attribute | Value |
| --- | --- |
| Data type | Datetime (timezone-aware, America/Los_Angeles) |
| Description | The end-of-hour timestamp in Pacific Time (PST/PDT). Derived from the source UTC timestamp using `tz_convert("America/Los_Angeles")`. Transitions between UTC-8 (winter) and UTC-7 (summer) are handled automatically. |
| Example value | `2026-03-15 14:00:00-07:00` |
| Tableau role | Dimension (date/time hierarchy) |
| Power BI role | Column (date table or continuous axis) |
| Origin | Engineered (converted from UTC source field) |

---

### demand_mw

| Attribute | Value |
| --- | --- |
| Data type | Float |
| Description | Actual electricity demand reported for the balancing authority at the end of the hour, in megawatts. This is the primary operational metric used throughout the dashboard. |
| Example value | `28452.0` |
| Tableau role | Measure |
| Power BI role | Measure |
| Origin | Raw |

---

### demand_forecast_mw

| Attribute | Value |
| --- | --- |
| Data type | Float |
| Description | The demand forecast value for the hour, in megawatts. Produced by the balancing authority before the hour. Used to calculate forecast error when compared against `demand_mw`. Note: 285 records (approximately 2%) have null forecast values in the source data. |
| Example value | `27900.0` |
| Tableau role | Measure |
| Power BI role | Measure |
| Origin | Raw |

---

### net_generation_mw

| Attribute | Value |
| --- | --- |
| Data type | Float |
| Description | Total net electricity generation within the balancing authority at the end of the hour, in megawatts. Includes all generation sources. A value lower than `demand_mw` indicates that imports from neighboring regions helped meet demand. |
| Example value | `24110.0` |
| Tableau role | Measure |
| Power BI role | Measure |
| Origin | Raw |

---

### total_interchange_mw

| Attribute | Value |
| --- | --- |
| Data type | Float |
| Description | Net energy flow across the balancing authority's transmission boundary, in megawatts. Positive values indicate net exports; negative values indicate net imports. One record has a null value in the source data. |
| Example value | `-4342.0` |
| Tableau role | Measure |
| Power BI role | Measure |
| Origin | Raw |

---

### stress_index

| Attribute | Value |
| --- | --- |
| Data type | Float (0–100, rounded to 2 decimal places) |
| Description | A simple review-prioritization indicator calculated as `(demand_mw / peak_demand_mw) × 100`. Expresses current demand as a percentage of the highest observed demand for that balancing authority within the Jan–Apr 2026 dataset window. A value near 100 means the hour is at or near observed peak demand. **Important limitation:** peak demand is derived from this dataset window only, not from a full historical record. Values should be interpreted as relative indicators within this dataset, not against all-time peaks. |
| Example value | `82.34` |
| Tableau role | Measure |
| Power BI role | Measure |
| Origin | Engineered |

---

### review_priority

| Attribute | Value |
| --- | --- |
| Data type | String (categorical, 3 values) |
| Description | A categorical label derived from `stress_index` to organize hours into review tiers. Thresholds are defined in the notebook. |
| Example value | `High Review Priority` |
| Tableau role | Dimension |
| Power BI role | Column |
| Origin | Engineered |

**Priority tier reference:**

| Label | Stress Index Range | Hours in Dataset |
| --- | --- | --- |
| High Review Priority | >= 90 | 75 |
| Medium Review Priority | >= 75 and < 90 | 762 |
| Low Review Priority | < 75 | 12,183 |

---

### peak_demand_mw

| Attribute | Value |
| --- | --- |
| Data type | Float |
| Description | The highest `demand_mw` value observed for the given balancing authority across the full Jan–Apr 2026 dataset. This is the denominator in the `stress_index` formula. It is constant for all rows sharing the same `balancing_authority` value. |
| Example value | `35596.0` |
| Tableau role | Measure |
| Power BI role | Measure |
| Origin | Engineered (derived via groupby max over the dataset window) |

---

## Section 2: Monthly Summary Fields

**File:** `data/processed/california_grid_monthly_summary.csv`
**Rows:** 20 (5 balancing authorities x 4 months) **Columns:** 11

| Field | Type | Description | Origin |
| --- | --- | --- | --- |
| `balancing_authority` | String | Balancing authority code | Raw |
| `year_month` | String | Calendar month in `YYYY-MM` format (e.g. `2026-01`) | Aggregated |
| `avg_demand_mw` | Float | Mean hourly demand for the month, in MW | Aggregated |
| `max_demand_mw` | Float | Highest single-hour demand in the month, in MW | Aggregated |
| `min_demand_mw` | Float | Lowest single-hour demand in the month, in MW | Aggregated |
| `avg_stress_index` | Float | Mean stress index value for the month | Aggregated |
| `max_stress_index` | Float | Highest stress index value recorded in the month | Aggregated |
| `total_hours` | Integer | Count of hourly records in the month | Aggregated |
| `high_priority_hours` | Integer | Count of hours classified as High Review Priority | Aggregated |
| `medium_priority_hours` | Integer | Count of hours classified as Medium Review Priority | Aggregated |
| `low_priority_hours` | Integer | Count of hours classified as Low Review Priority | Aggregated |

---

## Section 3: Hourly Risk Summary Fields

**File:** `data/processed/california_grid_hourly_risk_summary.csv`
**Rows:** 120 (5 balancing authorities x 24 hours) **Columns:** 10

| Field | Type | Description | Origin |
| --- | --- | --- | --- |
| `balancing_authority` | String | Balancing authority code | Raw |
| `hour_of_day` | Integer | Hour of day in Pacific Time, 0–23 | Aggregated |
| `avg_demand_mw` | Float | Mean demand for this hour of day across all days, in MW | Aggregated |
| `max_demand_mw` | Float | Highest demand observed at this hour of day, in MW | Aggregated |
| `avg_stress_index` | Float | Mean stress index for this hour of day | Aggregated |
| `max_stress_index` | Float | Highest stress index at this hour of day | Aggregated |
| `total_observations` | Integer | Number of daily observations at this hour | Aggregated |
| `high_priority_count` | Integer | Count of High Review Priority observations at this hour | Aggregated |
| `medium_priority_count` | Integer | Count of Medium Review Priority observations at this hour | Aggregated |
| `low_priority_count` | Integer | Count of Low Review Priority observations at this hour | Aggregated |

---

## Section 4: KPI Summary Fields

**File:** `data/processed/california_grid_kpi_summary.csv`
**Rows:** 5 (one per balancing authority) **Columns:** 12

| Field | Type | Description | Origin |
| --- | --- | --- | --- |
| `balancing_authority` | String | Balancing authority code | Raw |
| `peak_demand_mw` | Float | Observed peak demand for the dataset window, in MW | Engineered |
| `avg_demand_mw` | Float | Mean hourly demand across the full dataset window, in MW | Aggregated |
| `avg_stress_index` | Float | Mean stress index across the full dataset window | Aggregated |
| `total_hours` | Integer | Total hourly records for this authority in the dataset | Aggregated |
| `date_range_start` | String | Earliest timestamp in the dataset for this authority | Aggregated |
| `date_range_end` | String | Latest timestamp in the dataset for this authority | Aggregated |
| `high_priority_hours` | Integer | Total hours classified as High Review Priority | Aggregated |
| `medium_priority_hours` | Integer | Total hours classified as Medium Review Priority | Aggregated |
| `low_priority_hours` | Integer | Total hours classified as Low Review Priority | Aggregated |
| `pct_high_priority` | Float | High priority hours as a percentage of total hours | Aggregated |
| `pct_medium_priority` | Float | Medium priority hours as a percentage of total hours | Aggregated |

---

## Notes on Data Quality

- `demand_forecast_mw` has 285 null values (~2% of records). These reflect gaps in the EIA source data and are retained as null in the dashboard-ready file.
- `total_interchange_mw` has 1 null value. Retained as null.
- All other fields in the dashboard-ready file are complete with no null values.
- `stress_index` values of exactly 0.0 reflect hours where `demand_mw` was reported as 0 MW for that balancing authority.
- `stress_index` values of exactly 100.0 identify the peak-demand hour(s) for each balancing authority within the dataset window.

---

*Last updated: 2026-05-03*
