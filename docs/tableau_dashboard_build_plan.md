# Tableau Dashboard Build Plan

**Dashboard title:** California Grid Reliability Monitor
**Project:** California Grid Operational Risk Overview
**Date:** 2026-05-03
**Tool:** Tableau Public (desktop-first layout)
**Primary data source:** `data/processed/california_grid_dashboard_ready.csv`

---

## 1. Target Audience

This dashboard is built for a technical or semi-technical reviewer who needs
to monitor California electricity grid demand behavior and quickly identify
periods that may warrant closer operational attention. The intended audience
includes:

- Data visualization engineers reviewing the portfolio project
- Energy analysts or operations staff performing routine demand review
- Hiring managers or interviewers assessing dashboard design and data literacy

The dashboard assumes the reviewer understands basic electricity grid concepts
(demand, generation, interchange) but does not require deep utility-sector
expertise to navigate.

---

## 2. Business Questions the Dashboard Answers

| Question | View that answers it |
| --- | --- |
| When did California grid demand reach its highest levels? | Hourly Demand Pulse |
| Which balancing authorities operate closest to their observed peak demand? | Risk Leaderboard |
| How does actual demand compare to net generation over time? | Adequacy View |
| Which specific hours deserve the closest operational review? | Review Queue |
| What is the overall stress profile for each balancing authority? | KPI Cards |

---

## 3. Data Sources

| Data source | File | Role in dashboard |
| --- | --- | --- |
| Hourly detail | `california_grid_dashboard_ready.csv` | Primary source for all time-series, filters, and row-level views |
| Monthly summary | `california_grid_monthly_summary.csv` | Month-level trend charts (optional secondary connection) |
| Hourly risk summary | `california_grid_hourly_risk_summary.csv` | Hour-of-day heatmap (optional secondary connection) |
| KPI summary | `california_grid_kpi_summary.csv` | KPI card values (optional secondary connection for performance) |

For a single-source build, all views can be driven from
`california_grid_dashboard_ready.csv` alone. The summary files are available
as secondary connections if dashboard performance becomes a concern at larger
data scales.

---

## 4. Dashboard Layout

**Canvas size:** 1200 × 800 pixels (desktop-first, screenshot-friendly)
**Structure:** Single dashboard with four horizontal zones

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: Dashboard title + date range label + BA filter     │
├───────────┬───────────┬───────────┬─────────────────────────┤
│  KPI Card │  KPI Card │  KPI Card │       KPI Card          │
│  Peak     │  Avg      │  High     │  % High Priority        │
│  Demand   │  Stress   │  Priority │  Hours (selected BA)    │
├─────────────────────────────────────────────────────────────┤
│  Zone 1: Hourly Demand Pulse (line chart, full width)       │
├─────────────────────────────────────────────────────────────┤
│  Zone 2: Adequacy View (line chart, full width)             │
├───────────────────────────────┬─────────────────────────────┤
│  Zone 3: Risk Leaderboard     │  Zone 4: Review Queue       │
│  (horizontal bar chart)       │  (ranked table or bar)      │
└───────────────────────────────┴─────────────────────────────┘
```

**Filter panel:** Balancing Authority, Review Priority, and Month filters
are placed above the KPI cards or in a left-side filter panel, accessible
at all times.

---

## 5. KPI Cards

Four KPI cards appear at the top of the dashboard. Each card updates when
the Balancing Authority filter is applied.

| Card | Field | Calculation | Format |
| --- | --- | --- | --- |
| Peak Demand | `peak_demand_mw` | MAX of `peak_demand_mw` for selected BA | `#,##0 MW` |
| Average Stress Index | `stress_index` | AVG of `stress_index` for selected BA and date range | `0.0%` or `0.00` |
| High Priority Hours | `review_priority` | COUNT of rows where `review_priority = "High Review Priority"` | Integer |
| % High Priority | `review_priority` | High Priority Hours / Total Hours × 100 | `0.00%` |

---

## 6. Visual Specifications

### View 1 — Hourly Demand Pulse

| Property | Specification |
| --- | --- |
| Chart type | Line chart |
| X axis | `local_time_pacific` (continuous, date/time) |
| Y axis | `demand_mw` |
| Color | `balancing_authority` (one line per authority) |
| Filter | Responds to Balancing Authority and Month filters |
| Title | "Hourly Demand by Balancing Authority" |
| Annotation | Optional reference line at each authority's `peak_demand_mw` |

This view answers: *When did demand spike, and for which authority?*

---

### View 2 — Adequacy View

| Property | Specification |
| --- | --- |
| Chart type | Dual-line or area chart |
| X axis | `local_time_pacific` (continuous) |
| Y axis | `demand_mw` (primary) and `net_generation_mw` (secondary, same axis) |
| Color | Demand line in one color; generation line in a contrasting color |
| Filter | Responds to Balancing Authority filter (recommended: single BA at a time) |
| Title | "Demand vs. Net Generation Over Time" |
| Tooltip | Show `total_interchange_mw` to explain the gap between demand and generation |

This view answers: *Was local generation sufficient, or did imports fill the gap?*

---

### View 3 — Risk Leaderboard

| Property | Specification |
| --- | --- |
| Chart type | Horizontal bar chart |
| Rows | `balancing_authority` |
| Column / length | AVG(`stress_index`) |
| Color | Encode by `review_priority` category or by stress index gradient |
| Sort | Descending by average stress index |
| Filter | Responds to Month filter |
| Title | "Average Stress Index by Balancing Authority" |
| Reference line | Optional: dashed line at 75 (Medium threshold) and 90 (High threshold) |

This view answers: *Which authority operates closest to its observed peak demand on average?*

---

### View 4 — Review Queue

| Property | Specification |
| --- | --- |
| Chart type | Bar chart (ranked) or highlighted table |
| Rows | Individual hours sorted by `stress_index` descending |
| Columns shown | `local_time_pacific`, `balancing_authority`, `demand_mw`, `stress_index`, `review_priority` |
| Color | Encode rows by `review_priority` |
| Filter | Responds to all filters; default view shows High and Medium priority only |
| Row limit | Display top 20 rows (configurable via filter) |
| Title | "Review Queue — Hours by Priority" |

This view answers: *Which specific hours should be reviewed first?*

---

### Optional View — Hour-of-Day Heatmap

| Property | Specification |
| --- | --- |
| Chart type | Heatmap (crosstab) |
| Rows | `balancing_authority` |
| Columns | `hour_of_day` (derived from `local_time_pacific`, 0–23) |
| Color | AVG(`stress_index`) using a sequential color palette |
| Data source | `california_grid_hourly_risk_summary.csv` (120 rows) or calculated from detail |
| Title | "Average Stress Index by Hour of Day" |

This view answers: *At what hours of the day does demand stress peak?*

---

## 7. Filters

| Filter | Field | Type | Scope |
| --- | --- | --- | --- |
| Balancing Authority | `balancing_authority` | Multi-select checkbox | All views |
| Review Priority | `review_priority` | Single-select or multi-select | All views |
| Month | `local_time_pacific` (month level) | Dropdown or slider | All views |
| Date Range | `local_time_pacific` | Date range picker | Hourly Demand Pulse and Adequacy View |

**Filter interaction guidance:**
- The Balancing Authority filter should be applied globally across all views so
  that KPI cards, the leaderboard, and the review queue all reflect the same scope.
- Default state: all five California balancing authorities selected, full date range.

---

## 8. Tooltip Guidance

Tooltips provide context that does not fit on the chart face. Configure custom
tooltips on each view:

| View | Tooltip fields to include |
| --- | --- |
| Hourly Demand Pulse | `local_time_pacific`, `balancing_authority`, `demand_mw`, `stress_index`, `review_priority` |
| Adequacy View | `local_time_pacific`, `demand_mw`, `net_generation_mw`, `total_interchange_mw` |
| Risk Leaderboard | `balancing_authority`, AVG `stress_index`, `peak_demand_mw`, count of high priority hours |
| Review Queue | All nine dashboard-ready fields |

Use plain-language labels in tooltips rather than raw field names. For example:
- `demand_mw` → "Demand (MW)"
- `stress_index` → "Stress Index (% of Peak)"
- `review_priority` → "Review Priority"

---

## 9. Design Standards

### Color palette (colorblind-accessible)

| Use | Color | Hex |
| --- | --- | --- |
| High Review Priority | Dark orange-red | `#D55E00` |
| Medium Review Priority | Amber | `#E69F00` |
| Low Review Priority | Steel blue | `#0072B2` |
| Demand line | Dark blue | `#003F5C` |
| Generation line | Teal | `#2F9C95` |
| Background | White | `#FFFFFF` |
| Grid lines | Light grey | `#E5E5E5` |

This palette is drawn from the Okabe-Ito colorblind-safe set and avoids
red-green combinations that are problematic for viewers with common color
vision deficiencies.

### Typography

| Element | Recommendation |
| --- | --- |
| Dashboard title | Bold, 18–20pt |
| View titles | Bold, 13–14pt |
| Axis labels | Regular, 10–11pt |
| Tooltip text | Regular, 10pt |
| KPI card values | Bold, 24–28pt |
| KPI card labels | Regular, 10pt |

### General layout rules

- Remove chart borders and background shading from individual views.
- Use light grey grid lines at low opacity rather than bold axis ticks.
- Align all view titles to the left edge.
- Avoid legends inside the chart area when axis labels or direct labels
  can substitute.
- Do not use dual Y-axes on the same chart. If two measures require
  comparison, use a shared axis only if the units are the same.

---

## 10. Accessibility Notes

- Use the colorblind-safe palette defined in Section 9.
- All KPI cards and view titles must use plain-language descriptions, not
  field names or abbreviations.
- Tooltips must be readable at default browser zoom (100%).
- Export screenshots at a minimum of 1200 pixels wide so text remains
  legible when embedded in a portfolio page or LinkedIn project card.
- Avoid encoding information through color alone. Use labels, position,
  or shape as secondary encodings wherever possible.
- Check final dashboard contrast using a tool such as the WebAIM Contrast
  Checker before publishing.

---

## 11. Portfolio Export Checklist

Before publishing to Tableau Public and adding the link to the README:

- [ ] All five California balancing authorities present in data
- [ ] Date range label visible on dashboard (e.g. "Jan–Apr 2026")
- [ ] All four KPI cards display correct values
- [ ] Balancing Authority filter applies globally to all views
- [ ] Tooltips are configured on all views with plain-language field labels
- [ ] Color palette matches the colorblind-accessible standard in Section 9
- [ ] Dashboard title reads "California Grid Reliability Monitor"
- [ ] Dashboard exported as a screenshot at 1200px wide minimum
- [ ] Screenshot saved to `assets/Dashboard_riskOverview.png` (replace or add)
- [ ] Tableau Public link updated in `README.md` if the workbook is republished
- [ ] Data source connection points to `california_grid_dashboard_ready.csv`
  (not the raw 69-column file)
- [ ] No sensitive or internal data included — EIA public data only

---

*Last updated: 2026-05-03*
