# Power BI Beginner Build Plan

**Dashboard title:** California Grid Reliability Monitor — Power BI Version
**Project:** California Grid Operational Risk Overview
**Date:** 2026-05-03
**Tool:** Power BI Desktop (free) + Power BI Service (optional publish)
**Skill level:** Beginner — designed for someone with Tableau experience who is new to Power BI

---

## 1. Purpose and Scope

This document is a beginner-level build guide for creating a simplified
Power BI version of the California Grid Reliability Monitor. The goal is
to demonstrate that the same data model and analytical questions can be
addressed across different BI platforms, not to replicate every feature
of the Tableau dashboard.

**Intended workflow:**

```
Data source (CSV files)
  -> Power BI Desktop (import + build interactive report visuals)
    -> Report page / dashboard (interactive filters, slicers, drill-through)
      -> Optional: Publish to Power BI Service for a shareable web link
```

The primary deliverable is an interactive Power BI report (`.pbix` file)
that a reviewer can open and interact with locally, or view as a published
web report via Power BI Service. Screenshots and PDF exports are portfolio
preview assets only — they are not the main deliverable.

This version is intentionally simplified. It uses pre-aggregated summary
tables where possible to reduce the need for complex DAX, and it focuses
on the most important views rather than building a full feature-equivalent
dashboard.

**What this plan does not claim:**

- Advanced Power BI expertise
- Production-ready enterprise dashboard patterns
- Full feature parity with the Tableau version

**What this plan demonstrates:**

- Ability to import a clean data model into Power BI
- Ability to build an interactive report with filters and slicers
- Ability to write beginner DAX measures
- Transferable dashboard thinking across BI platforms

---

## 2. Interactive Report vs. Portfolio Screenshot

| Artifact | Format | Purpose |
| --- | --- | --- |
| `.pbix` file | Power BI Desktop binary | Primary deliverable — the real interactive report |
| Published web link | Power BI Service URL | Optional — shareable interactive version |
| Screenshot (PNG) | Image file | Portfolio preview for GitHub README, website, LinkedIn |
| PDF export | PDF file | Portfolio preview for documents and applications |

The interactive report is the version a technical reviewer would open
to explore the data — filtering by balancing authority, drilling into
individual hours, reading tooltips. Screenshots and PDFs exist to give
a non-interactive preview in contexts where Power BI cannot be embedded,
such as a GitHub README or a LinkedIn project card.

The `.pbix` file is excluded from GitHub via `.gitignore`. Portfolio
screenshots are saved to the `assets/` folder and committed as lightweight
image files.

---

## 3. Files to Import

Import the following files from `data/processed/` into Power BI Desktop
using Get Data > Text/CSV:

| File | Rows | Purpose in Power BI |
| --- | --- | --- |
| `california_grid_dashboard_ready.csv` | 13,020 | Primary table for all detailed visuals |
| `california_grid_kpi_summary.csv` | 5 | KPI card values per balancing authority |
| `california_grid_monthly_summary.csv` | 20 | Monthly trend chart |
| `california_grid_hourly_risk_summary.csv` | 120 | Hour-of-day profile chart |

These files are local only (not committed to GitHub). See `data/README.md`
for instructions on regenerating them from the notebook.

---

## 4. Data Import Steps

### Step 1 — Open Power BI Desktop

Download and install Power BI Desktop (free from Microsoft) if not already
installed.

### Step 2 — Import the primary table

1. Click **Home > Get Data > Text/CSV**
2. Navigate to `data/processed/california_grid_dashboard_ready.csv`
3. In the preview, confirm the column names match the data dictionary
4. Click **Load** (not Transform, unless column types need adjustment)
5. Rename the table to `GridDetail` in the Fields pane

### Step 3 — Import summary tables

Repeat the import process for:

- `california_grid_kpi_summary.csv` — rename table to `KPISummary`
- `california_grid_monthly_summary.csv` — rename table to `MonthlySummary`
- `california_grid_hourly_risk_summary.csv` — rename table to `HourlyRisk`

### Step 4 — Check column types

After importing, open each table in **Transform Data (Power Query)** and
confirm:

| Column | Expected type |
| --- | --- |
| `local_time_pacific` | Date/Time (or Text — see note below) |
| `demand_mw` | Decimal Number |
| `stress_index` | Decimal Number |
| `balancing_authority` | Text |
| `review_priority` | Text |
| `peak_demand_mw` | Decimal Number |
| `year_month` | Text (YYYY-MM format) |
| `hour_of_day` | Whole Number |

**Note on timestamps:** Power BI may struggle with timezone-aware datetime
strings (e.g. `2026-03-15 14:00:00-07:00`). If `local_time_pacific` does
not parse correctly as a date/time, set its type to Text in Power Query and
use it as a label axis. For time-series sorting, create a calculated column
in DAX (see Section 6) or use a plain date field derived from the value.

### Step 5 — Do not create relationships between tables

For this beginner version, each table is used independently by different
visuals. Avoid creating relationships in the Model view unless you have
experience with Power BI data models. Using each summary table as a
standalone source for its corresponding visual is simpler and avoids
unintended filter propagation.

---

## 5. Required Visuals

### Visual 1 — KPI Cards (four cards)

**Source table:** `KPISummary`

Create four Card visuals, one for each of the following fields:

| Card | Field | Format |
| --- | --- | --- |
| Peak Demand | `peak_demand_mw` | `#,##0 "MW"` |
| Average Stress Index | `avg_stress_index` | `0.0` |
| High Priority Hours | `high_priority_hours` | Integer |
| % High Priority | `pct_high_priority` | `0.00"%"` |

Add a Slicer visual connected to `KPISummary[balancing_authority]` so that
the cards update when an authority is selected.

---

### Visual 2 — Monthly Demand Trend (line chart)

**Source table:** `MonthlySummary`

| Property | Setting |
| --- | --- |
| Visual type | Line chart |
| X axis | `year_month` |
| Y axis | `avg_demand_mw` |
| Legend | `balancing_authority` |
| Title | "Average Monthly Demand by Balancing Authority" |

Sort the X axis by `year_month` alphabetically to preserve chronological order.

---

### Visual 3 — Hour-of-Day Risk Profile (line or bar chart)

**Source table:** `HourlyRisk`

| Property | Setting |
| --- | --- |
| Visual type | Line chart or clustered bar chart |
| X axis | `hour_of_day` |
| Y axis | `avg_stress_index` |
| Legend | `balancing_authority` |
| Title | "Average Stress Index by Hour of Day" |

This shows which hours of the day tend to produce the highest demand stress
for each balancing authority.

---

### Visual 4 — Risk Leaderboard (bar chart)

**Source table:** `KPISummary`

| Property | Setting |
| --- | --- |
| Visual type | Clustered bar chart |
| Y axis | `balancing_authority` |
| X axis | `avg_stress_index` |
| Sort | Descending by `avg_stress_index` |
| Title | "Average Stress Index by Balancing Authority" |

---

### Visual 5 — Review Queue (table)

**Source table:** `GridDetail`

| Property | Setting |
| --- | --- |
| Visual type | Table |
| Columns | `local_time_pacific`, `balancing_authority`, `demand_mw`, `stress_index`, `review_priority` |
| Sort | `stress_index` descending |
| Title | "Review Queue — Highest Stress Hours" |

Add a Slicer for `review_priority` so the reviewer can filter to High
or Medium priority rows only.

---

## 6. Suggested DAX Measures

The following DAX measures can be added to the `GridDetail` table. These
are beginner-level measures using standard aggregation functions.

**Average Demand (MW)**

```dax
Avg Demand MW =
AVERAGE(GridDetail[demand_mw])
```

**Total High Priority Hours**

```dax
High Priority Hours =
COUNTROWS(
    FILTER(GridDetail, GridDetail[review_priority] = "High Review Priority")
)
```

**Percent High Priority**

```dax
Pct High Priority =
DIVIDE(
    [High Priority Hours],
    COUNTROWS(GridDetail),
    0
) * 100
```

**Average Stress Index**

```dax
Avg Stress Index =
AVERAGE(GridDetail[stress_index])
```

**Forecast Error (where forecast is available)**

```dax
Avg Forecast Error MW =
AVERAGEX(
    FILTER(GridDetail, NOT ISBLANK(GridDetail[demand_forecast_mw])),
    GridDetail[demand_mw] - GridDetail[demand_forecast_mw]
)
```

These five measures cover the main KPI cards and summary aggregations.
More advanced DAX patterns (time intelligence, running totals, rank
functions) are outside the scope of this beginner version.

---

## 7. Slicers

Add the following Slicer visuals to the report page:

| Slicer | Source table | Field | Type |
| --- | --- | --- | --- |
| Balancing Authority | `GridDetail` | `balancing_authority` | Dropdown or tile |
| Review Priority | `GridDetail` | `review_priority` | Dropdown |
| Month | `MonthlySummary` | `year_month` | Dropdown |

Because the tables in this beginner build are not related in the data
model, a slicer connected to one table will not automatically filter
visuals built from a different table. For this version, apply filters
within each visual's Filters pane individually, or use slicers only on
visuals that share the same source table. Building a proper related data
model with a shared date and authority table is listed as a future
improvement in Section 10.

---

## 8. Design Guidance

Apply these settings manually or via a custom theme JSON file to align
the Power BI report with the color choices used in the Tableau version:

| Element | Recommendation |
| --- | --- |
| High Review Priority color | `#D55E00` (dark orange-red) |
| Medium Review Priority color | `#E69F00` (amber) |
| Low Review Priority color | `#0072B2` (steel blue) |
| Background | White |
| Canvas background | Light grey (`#F5F5F5`) |
| Report page size | 1280 x 720 pixels (16:9, standard) |
| Font | Segoe UI (Power BI default — acceptable) |

**Formatting tips for a clean beginner layout:**

- Turn off gridlines on all charts.
- Remove chart border shadows.
- Use the card visual's Callout value setting to increase KPI number size.
- Add a text box for the dashboard title at the top of the page.
- Use consistent spacing between visuals (10–15px gap).

---

## 9. Export, Publishing, and Portfolio Assets

### Primary deliverable — the interactive report

The Power BI report is built and saved as a `.pbix` file in Power BI
Desktop. This is the main deliverable. A reviewer with Power BI Desktop
installed can open it, interact with all slicers and filters, and explore
the data.

Save the file locally. Do not commit it to GitHub. The `.pbix` format is
already excluded from version control by `.gitignore`.

### Optional — publish to Power BI Service

1. Sign in with a free Microsoft account at powerbi.com
2. In Power BI Desktop, click **Home > Publish**
3. Select **My Workspace**
4. After publishing, copy the report URL
5. Add the link to `README.md` alongside the Tableau Public link so both
   interactive versions are accessible to portfolio reviewers

**Note:** A free Power BI account supports publishing to My Workspace.
The published report is viewable via web link. Embedding in external
sites requires a Pro or Premium license.

### Portfolio preview assets (screenshots and PDF)

Screenshots and PDF exports are secondary assets used in contexts where
Power BI cannot be embedded — a GitHub README, a personal website, or a
LinkedIn project card.

To export a screenshot:

1. Arrange the report canvas to show the most informative view
2. Use your OS screenshot tool or Power BI's **File > Export > Export to PDF**
3. Save the image to `assets/` (e.g. `assets/PowerBI_Dashboard_Preview.png`)
4. Commit the image to GitHub as part of the portfolio assets

Screenshots are committed to GitHub; the `.pbix` file is not.

---

## 10. Future Improvements

The following improvements are outside the scope of this beginner version
and are documented here as next steps if the Power BI build is extended:

- **Build a proper date table** using DAX (`CALENDAR` function) and relate
  it to `GridDetail` to enable time-intelligence measures such as
  month-over-month change.
- **Create a data model with relationships** between `GridDetail` and the
  summary tables so that a single Balancing Authority slicer filters all
  visuals simultaneously.
- **Add conditional formatting** to the Review Queue table so that High
  priority rows are highlighted automatically.
- **Use a custom theme JSON file** to enforce the colorblind-accessible
  palette consistently across all visuals.
- **Add a Decomposition Tree or Key Influencers visual** to demonstrate
  Power BI's built-in AI visuals for exploratory analysis.
- **Publish and link the report** in `README.md` alongside the Tableau
  Public link, making both interactive dashboard versions accessible to
  portfolio reviewers.

---

*Last updated: 2026-05-03*
