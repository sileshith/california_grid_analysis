# California Grid Stress Monitoring Dashboard

**Author:** Sileshi Hirpa  
**Date:** April–May 2026  
**Tools:** Python, pandas, Plotly, Jupyter Notebook, Tableau Public  
**Data:** EIA Form EIA-930, Balancing Authority Hourly Operations

---

## Summary

A public-data analytics project that transforms raw EIA-930 balancing authority data into a structured California grid stress analysis and an interactive Tableau Public dashboard. The project demonstrates an end-to-end analytical workflow: data ingestion and scope validation, feature engineering, review-priority classification, dashboard-ready data modeling, and interactive dashboard delivery.

**[Explore the California Grid Stress Monitoring Dashboard on Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CaliforniaGridStressMonitoringDashboard/ExecutiveOverview)**

---

## Business Problem

California's electricity grid is managed across five balancing authorities responsible for matching supply and demand in real time. Understanding when and where demand approaches observed peak levels — and how that relates to forecast accuracy, local generation capacity, and interchange — supports reliability-oriented grid analysis and operational review.

**Analytical question:** How can hourly EIA-930 balancing authority data be prepared, validated, and visualized so that a reviewer can quickly identify periods that may deserve additional operational attention?

This project answers that question through a structured Python pipeline, a custom Grid Stress Index, a review-priority classification system, and an interactive three-tab Tableau dashboard.

---

## Data Source

| Field | Detail |
|---|---|
| Source | EIA Form EIA-930, Balancing Authority Hourly Operations |
| Publisher | U.S. Energy Information Administration (public domain) |
| Time period | January–April 2026 |
| Raw file | `EIA930_BALANCE_2026_Jan_Jun.csv` (~27 MB) |
| Scope | California balancing authorities only: BANC, CISO, IID, LDWP, TIDC |
| Hourly records after filtering | 13,020 |

Raw and processed data files are excluded from this repository. See `data/README.md` for download and reproduction instructions.

---

## California Balancing Authorities

| Authority | Description |
|---|---|
| BANC | Balancing Authority of Northern California |
| CISO | California ISO — the largest authority, covering most of the state |
| IID | Imperial Irrigation District |
| LDWP | Los Angeles Department of Water and Power |
| TIDC | Turlock Irrigation District |

California's five balancing authorities operate at very different scales. CISO manages demand at tens of thousands of megawatts; IID and TIDC operate at hundreds of megawatts. The Grid Stress Index normalizes each authority against its own observed peak demand, enabling fair comparison across scales.

---

## Methods

1. **Data ingestion and inspection** — Load raw EIA-930 CSV; review structure, column names, and row counts before any transformation
2. **Column standardization and cleaning** — Rename fields to snake_case, remove null records on required columns, deduplicate on authority and timestamp
3. **Scope validation** — Identify and correct a misleading early visualization caused by non-California records before filtering to California-only balancing authorities
4. **Timestamp conversion** — Convert UTC timestamps to Pacific Time (PST/PDT-aware) using `tz_convert("America/Los_Angeles")`
5. **Feature engineering** — Compute forecast error, generation gap, and import pressure as operational context fields
6. **Grid Stress Index** — Calculate `(demand_mw / peak_demand_mw) × 100` per authority, where the peak denominator is derived from the January–April 2026 dataset window
7. **Review-priority classification** — Classify each hourly record as High (Stress Index ≥ 90), Medium (≥ 75), or Low (< 75) using named threshold constants
8. **Dashboard data model export** — Export four purpose-built CSV files for Tableau (detail, monthly summary, hourly risk summary, KPI summary)
9. **Tableau dashboard publication** — Three-tab interactive dashboard published to Tableau Public

---

## Key Metrics

| Metric | Value |
|---|---|
| Total Scored Hours | 13,020 |
| High Review Priority Hours | 75 |
| Average Stress Index | 48.62 |
| Peak Demand MW | 35,596 (CISO) |
| Peak Stress Index | 100.0 |
| Largest Forecast Error MW (High Priority) | 9,555 |

---

## Interactive Tableau Dashboard

**[Explore the California Grid Stress Monitoring Dashboard on Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CaliforniaGridStressMonitoringDashboard/ExecutiveOverview)**

The dashboard contains three tabs:

- **Executive Overview** — KPI summary cards, review priority composition, high-priority risk concentration by balancing authority, and Stress Index trend over the full dataset window
- **High-Priority Review Queue** — Detailed view of the 75 high-priority hours, including peak Stress Index events, top forecast error records, and a ranked review table
- **Authority Comparison** — Side-by-side comparison of average Stress Index, forecast error, demand vs. net generation, and total interchange by balancing authority

### Dashboard Screenshots

#### Executive Overview
![Executive Overview](outputs/dashboard_screenshots/executive_overview.png)

#### High-Priority Review Queue
![High-Priority Review Queue](outputs/dashboard_screenshots/high_priority_review_queue.png)

#### Authority Comparison
![Authority Comparison](outputs/dashboard_screenshots/authority_comparison.png)

---

## Dashboard Data Model

The pipeline exports four purpose-built files for Tableau. Separating detail and summary layers keeps dashboard queries fast and makes the architecture extensible to multi-year datasets.

| File | Rows | Columns | Role |
|---|---:|---:|---|
| `california_grid_dashboard_ready.csv` | 13,020 | 9 | Hourly detail for time-series charts, filters, and review tables |
| `california_grid_monthly_summary.csv` | 20 | 11 | Month-level trend by balancing authority |
| `california_grid_hourly_risk_summary.csv` | 120 | 10 | Hour-of-day demand and stress profile |
| `california_grid_kpi_summary.csv` | 5 | 12 | KPI summary — one row per balancing authority |

All four files are generated by the notebook pipeline and excluded from version control. See `data/README.md` for reproduction instructions.

---

## Scope Validation: Why It Matters

One of the most important steps in the notebook is the scope validation check performed before any California-specific analysis begins. An initial visualization of the raw file ran without error but produced a misleading view because the EIA-930 source file includes balancing authorities from across the United States.

This reflects a core analytical principle: a chart can be technically correct and still answer the wrong question if the data scope does not match the business problem. The notebook documents this discovery explicitly and shows how filtering to California-only records changes the interpretation.

---

## Repository Structure

```
california-grid-analysis/
├── assets/
│   ├── Dashboard_riskOverview.png              # Legacy dashboard preview
│   └── PGE_One_Slide_Summary.pdf               # One-slide project summary
├── data/
│   ├── raw/
│   │   └── .gitkeep                            # Raw data excluded; see data/README.md
│   ├── processed/
│   │   └── .gitkeep                            # Processed files excluded; run notebook to regenerate
│   └── README.md                               # Data sources and reproduction instructions
├── docs/
│   ├── dashboard_data_dictionary.md            # Field definitions for all dashboard files
│   ├── dashboard_data_model.md                 # Data model architecture
│   ├── tableau_dashboard_build_plan.md         # Tableau build specification
│   └── visualization_engineering_roadmap.md   # Future enhancement notes
├── notebooks/
│   └── california_grid_analysis.ipynb          # Full analytical pipeline
├── outputs/
│   └── dashboard_screenshots/                  # Tableau Public dashboard screenshots
│       ├── executive_overview.png
│       ├── high_priority_review_queue.png
│       └── authority_comparison.png
├── tableau/
│   └── WB1_California_Grid_Stress_Executive_Dashboard.twb   # Tableau workbook
├── .gitignore
├── README.md
└── requirements.txt
```

---

## How to Reproduce

### Requirements

```
pandas>=1.2.0
numpy>=1.20.0
plotly>=5.0.0
notebook>=6.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Steps

1. **Download raw data** — Follow `data/README.md` to download `EIA930_BALANCE_2026_Jan_Jun.csv` from the EIA Grid Monitor and place it at `data/raw/EIA930_BALANCE_2026_Jan_Jun.csv`.
2. **Run the notebook** — Open and run `notebooks/california_grid_analysis.ipynb` from top to bottom.
3. **Outputs generated:**
   - `data/processed/california_grid_dashboard_ready.csv`
   - `data/processed/california_grid_monthly_summary.csv`
   - `data/processed/california_grid_hourly_risk_summary.csv`
   - `data/processed/california_grid_kpi_summary.csv`
4. **View the published dashboard** — [Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CaliforniaGridStressMonitoringDashboard/ExecutiveOverview)

---

## Limitations and Disclaimer

- **Dataset window:** The analysis covers January–April 2026 only. The Stress Index denominator is the observed peak demand within this window, not a multi-year historical record. Values reflect relative demand behavior during this period and should not be interpreted as comparisons against all-time peaks.
- **Grid Stress Index is a custom analytical indicator:** The Stress Index is a review-prioritization tool built for this portfolio project. It is not a formal operational risk score and does not replicate any utility or grid operator methodology.
- **Public data only:** This project uses public EIA-930 data. It does not represent any utility's internal operational systems, proprietary data pipelines, enterprise risk models, or reliability procedures.
- **No real-time connection:** The dataset is static. The pipeline does not refresh automatically as new EIA data becomes available.
- **No reliability event modeling:** This project identifies periods of elevated demand relative to observed peak. It does not model the probability or consequence of reliability events.

---

## Portfolio Positioning

This project demonstrates skills applicable to data science, business analytics, energy analytics, operations analytics, risk analytics, and decision-support roles:

- **Data preparation and validation** — Scope discovery and correction, time-zone-aware timestamp handling, field standardization, and reproducible pipeline design
- **Feature engineering** — Custom metric design (Grid Stress Index), review-priority classification, forecast error and generation gap analysis
- **Time-series analysis** — Hourly demand patterns, day-of-week profiles, monthly trend summaries across multiple balancing authorities
- **Dashboard data modeling** — Layered export architecture separating hourly detail from pre-aggregated summary tables
- **Tableau dashboard design** — Multi-tab interactive dashboard with KPI cards, filtered review queues, and cross-authority comparisons published to Tableau Public
- **Analytical communication** — Clear documentation of methodology, dataset limitations, and interpretation caveats throughout the notebook and README

---

## Author

**Sileshi Hirpa**  
Data Science (Business Analytics Track) — Arizona State University

[GitHub](https://github.com/sileshith) · [Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285)

---

*Last updated: May 2026*
