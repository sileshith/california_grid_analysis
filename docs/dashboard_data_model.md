# Dashboard Data Model

**Project:** California Grid Operational Risk Overview
**Date:** 2026-05-03

---

## 1. Overview

This document describes how the four dashboard-ready datasets relate to each
other, which tool should use each file, and why the data model is structured
this way. It also documents which files are safe to commit to GitHub and which
should remain local only.

---

## 2. Dataset Inventory

| File | Rows | Size | Role |
| --- | --- | --- | --- |
| `california_grid_dashboard_ready.csv` | 13,020 | 1.1 MB | Hourly detail — primary Tableau data source |
| `california_grid_monthly_summary.csv` | 20 | 1.3 KB | Aggregated summary — month-level trends |
| `california_grid_hourly_risk_summary.csv` | 120 | 5.5 KB | Aggregated summary — hour-of-day profiles |
| `california_grid_kpi_summary.csv` | 5 | 724 B | KPI snapshot — one row per balancing authority |
| `cleaned_california_grid_data.csv` | 13,020 | 3.6 MB | Full processed source — 69 columns, pipeline output |

All five files live in `data/processed/`. The raw EIA source file
(`data/raw/EIA930_BALANCE_2026_Jan_Jun.csv`, ~27 MB) is documented in
`data/README.md` but never committed.

---

## 3. Which Dataset Tableau Should Use

**Primary data source:** `california_grid_dashboard_ready.csv`

This file contains the 9 fields that drive all Tableau views: the time series,
the stress index trend, the review priority filter, and the per-authority
comparisons. It is pre-filtered to California only, has clean column names, and
carries no unnecessary EIA source columns.

**Supporting sources for summary views:**

- `california_grid_monthly_summary.csv` — use for month-over-month bar or line
  charts without requiring Tableau to aggregate 13,020 rows at query time
- `california_grid_hourly_risk_summary.csv` — use for the hour-of-day heatmap
  or profile view showing when demand peaks occur across the day
- `california_grid_kpi_summary.csv` — use for KPI cards showing per-authority
  peak demand, average stress, and priority hour counts

Tableau can connect to multiple CSV data sources simultaneously. Connecting
summary tables directly avoids repeated aggregation of the hourly detail file
and keeps calculated fields simple.

---

## 4. Which Dataset Power BI Should Use

**Primary data source:** `california_grid_dashboard_ready.csv`

Power BI can import this file directly as a table. Calculated columns and
measures (average demand, stress index trend, priority counts) can be written
in DAX against this table.

**Recommended approach for a simplified cross-platform version:**

- Import `california_grid_kpi_summary.csv` as a separate table for KPI card
  visuals — this avoids writing complex DAX aggregations for a beginner-level
  demonstration
- Import `california_grid_monthly_summary.csv` for the monthly trend visual
- Use `california_grid_dashboard_ready.csv` for the hourly time series and
  any drill-down views

Because the `.pbix` file is excluded from the repository via `.gitignore`, the
Power BI version is documented here and in the roadmap but not tracked in Git.

---

## 5. Detailed Data vs. Summary Tables

| File | Type | Best used for |
| --- | --- | --- |
| `california_grid_dashboard_ready.csv` | Hourly detail | Time series, drill-down, review queue, full filter interaction |
| `california_grid_monthly_summary.csv` | Summary | Month-over-month trend charts, aggregated bar charts |
| `california_grid_hourly_risk_summary.csv` | Summary | Hour-of-day heatmap, peak-hour profile by authority |
| `california_grid_kpi_summary.csv` | Summary | KPI cards, authority comparison scorecards |

The hourly detail file supports interactive exploration where a reviewer wants
to filter by date, authority, or priority and drill into individual hours. The
summary tables support overview-level views where pre-aggregated values are
sufficient and dashboard performance matters more than row-level access.

---

## 6. Why Summary Tables Improve Dashboard Performance

Tableau and Power BI both build visual queries against their connected data
sources at render time. When a view requires aggregating thousands of rows
(sum of demand by month, count of high-priority hours by authority), the
dashboard tool must scan and compute those values each time the view loads
or a filter changes.

Pre-aggregated summary tables shift that computation from dashboard render
time to Python pipeline time. The result is:

- **Faster initial load** — a 20-row monthly table loads instantly; a 13,020-row
  hourly table requires more work per query
- **Simpler calculated fields** — summary views that connect to pre-aggregated
  tables need fewer or no calculated fields in Tableau or DAX in Power BI
- **More predictable behavior** — pre-computed aggregates eliminate edge cases
  where dashboard-level aggregation logic differs subtly from the intended
  Python calculation
- **Scalability** — if the dataset were extended to a full year or multiple
  years, summary tables would remain small while the hourly detail file grows
  proportionally

For this project the hourly detail file is small enough (1.1 MB) that
performance differences are minor. The summary table structure is built here
to demonstrate dashboard data engineering principles and to prepare the
architecture for future expansion.

---

## 7. Git Commit Recommendations

### Files that should remain ignored (excluded by current .gitignore)

| File | Size | Reason |
| --- | --- | --- |
| `data/raw/EIA930_BALANCE_2026_Jan_Jun.csv` | ~27 MB | Large public source file — download instructions in `data/README.md` |
| `data/processed/cleaned_california_grid_data.csv` | 3.6 MB | Wide pipeline output (69 columns) — reproducible by running the notebook |
| `data/processed/california_grid_dashboard_ready.csv` | 1.1 MB | Derived from the processed file — reproducible, excluded by current `data/processed/*` rule |

All three files are currently excluded by `.gitignore`. They are reproducible:
the raw file can be downloaded from the EIA, and all processed files can be
regenerated by running `notebooks/california_grid_analysis.ipynb` followed
by the Phase 4 data model build step.

### Files that are safe to commit

| File | Size | Reason |
| --- | --- | --- |
| `data/processed/california_grid_monthly_summary.csv` | 1.3 KB | Tiny aggregated table — adds meaningful value for reviewers browsing the repository |
| `data/processed/california_grid_hourly_risk_summary.csv` | 5.5 KB | Tiny aggregated table — same reasoning |
| `data/processed/california_grid_kpi_summary.csv` | 724 B | Five rows — essentially documentation-level data |

These three summary files are small enough that committing them is safe and
useful. A reviewer who clones the repository can immediately see key results
without running the full pipeline. To commit them, their paths would need to
be added as exceptions in `.gitignore` (e.g. `!data/processed/*_summary.csv`).
This is a deliberate decision that the repository owner should make consciously.

---

## 8. How This Supports Dashboard Performance and Scalability

The four-file data model separates concerns across two dimensions:

**Granularity:** The hourly detail file supports row-level filtering and drill-down.
The summary files support overview and trend views without requiring the dashboard
to aggregate thousands of rows.

**Scope:** All files are scoped to California balancing authorities only. No
national or cross-regional data enters the dashboard layer. This was enforced
at the pipeline stage in the notebook.

**Reproducibility:** Every file in this model is derived from publicly available
EIA data through a documented Python pipeline. No manual edits were made to any
CSV file directly. The full derivation chain is:

```
EIA raw download
  -> notebooks/california_grid_analysis.ipynb
     -> data/processed/cleaned_california_grid_data.csv
        -> Phase 4 data model build
           -> california_grid_dashboard_ready.csv
           -> california_grid_monthly_summary.csv
           -> california_grid_hourly_risk_summary.csv
           -> california_grid_kpi_summary.csv
```

If the source data is updated or the pipeline logic changes, all downstream
files can be regenerated from scratch with no manual intervention.

---

*Last updated: 2026-05-03*
