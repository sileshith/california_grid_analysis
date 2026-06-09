# California Grid Operations Analytics

**A forecasting benchmark study and operational analytics platform for California grid reliability monitoring. Combines time series forecasting, spatial dependency analysis, and evidence-based model evaluation to support grid stress detection across five interconnected balancing authorities.**

**Author:** Sileshi Hirpa  
**Published:** May 2026  
**Tools:** Python, Apache Airflow, PostgreSQL, SQL, Tableau Public, LightGBM, Prophet, pandas  
**Data:** EIA Form EIA-930, Balancing Authority Hourly Operations (public domain)

**[Explore the Tableau Dashboard on Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CaliforniaGridStressMonitoringDashboard/ExecutiveOverview)**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![LightGBM](https://img.shields.io/badge/LightGBM-3.29%25%20MAPE-green)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-Orchestration-informational)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Tableau](https://img.shields.io/badge/Tableau-Dashboards-orange)
![Tests](https://img.shields.io/badge/tests-20%20passing-brightgreen)

## 🚀 Quick Start

**Run the forecasting benchmarks:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run baseline forecasts (Naive 24h, Moving Average)
python src/baseline_forecasts.py

# Run LightGBM forecasting
python src/lightgbm_forecast.py

# Run Prophet forecasting
python src/prophet_forecast.py

# Compare all models
python src/compare_models.py
```

**Run the spatial dependency analysis:**
```bash
# Analyze correlations and Granger causality
python src/analyze_spatial_dependencies.py

# Test spatial features
python src/spatial_feature_forecast.py
```

**Run the full data pipeline:**
```bash
# Set up database (optional, uses SQLite fallback if not set)
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/california_grid"

# Run complete ELT pipeline
python dags/california_grid_daily_pipeline.py
```

**Run tests:**
```bash
pytest tests/ -v
```

## Project Snapshot

| Area | Result |
|---|---|
| Domain | California grid operations analytics |
| Data | EIA-930 hourly balancing authority data |
| Records processed | 158,182 raw rows; 13,020 California authority-hours |
| Data ingestion | EIA Open Data API option with local CSV fallback |
| Pipeline | Python ELT pipeline orchestrated with Apache Airflow |
| Database layer | PostgreSQL-ready SQL reporting with SQLite fallback |
| Dashboard | Tableau Public executive dashboard with review queue |
| Forecasting | LightGBM: 3.29% MAPE (4 authorities), Naive: 11.05% MAPE |
| Spatial analysis | Correlation: 0.484 avg, Granger: 20/20 significant pairs |
| Validation | 20 pytest checks passing |
| Key output | 75 high-priority grid review hours identified |

## 🎯 Project Overview

This project combines operational analytics with forecasting research to support California grid reliability monitoring. The system processes hourly demand data from five balancing authorities, calculates grid stress metrics, and evaluates multiple forecasting approaches to determine the most effective prediction strategy.

**Core Capabilities:**
- **Operational Monitoring:** Automated ELT pipeline processing 158,000+ EIA-930 records, calculating grid stress indices, and identifying 75 high-priority review hours
- **Forecasting Benchmarks:** Systematic evaluation of Naive (11.05% MAPE), Prophet (16.8% MAPE), and LightGBM (3.29% MAPE) models across five authorities
- **Spatial Analysis:** Correlation analysis, Granger causality testing, and spatial feature validation to determine whether graph-based modeling improves forecasts
- **Evidence-Based Decisions:** Spatial features improved 3 of 5 authorities but worsened overall MAPE by 5.5%, leading to a data-driven recommendation against additional model complexity

**Technical Implementation:**
- **Data Engineering:** Apache Airflow orchestration, PostgreSQL reporting layer, EIA Open Data API integration with CSV fallback
- **Forecasting:** LightGBM with lag-based features (1h, 24h, 168h lags, rolling means, time features)
- **Analytics:** Granger causality tests, lagged cross-correlations, spatial feature engineering
- **Visualization:** Tableau dashboards with executive overview, high-priority alerts, and authority comparison views
- **Quality Assurance:** 20 automated pytest validations covering data quality, pipeline outputs, and API integration

## Business Context

California's electricity grid operates across five interconnected balancing authorities that must match supply and demand in real time. Grid stress events occur when demand approaches capacity limits, potentially leading to emergency measures and reliability concerns.

**Operational Challenge:** Grid operators need reliable demand forecasts and stress indicators to support proactive resource allocation, demand response activation, and coordination across authorities.

**This System Provides:**
- **Automated Monitoring:** Daily ELT pipeline processing EIA-930 data, calculating normalized stress indices, and identifying high-priority hours requiring review
- **Forecasting Benchmarks:** Systematic evaluation of multiple forecasting approaches (Naive, Prophet, LightGBM) with comprehensive error analysis
- **Spatial Analysis:** Quantitative assessment of whether spatial dependencies between authorities improve forecast accuracy
- **Operational Dashboards:** Tableau visualizations showing stress trends, forecast errors, and authority comparisons for operational decision support

**Technical Value:** The pipeline validates data quality, normalizes metrics across authorities of different scales (300 MW to 35,000 MW peak demand), loads results to PostgreSQL for ad-hoc analysis, and exports dashboard-ready files. This operational workflow is built on public EIA-930 data and demonstrates production-oriented data engineering practices.

## Data Source

| Field | Detail |
|---|---|
| Source | EIA Form EIA-930, Balancing Authority Hourly Operations |
| Publisher | U.S. Energy Information Administration (public domain) |
| Time period | January-April 2026 |
| Raw file | `EIA930_BALANCE_2026_Jan_Jun.csv` (~27 MB, ~158,000 rows) |
| Scope | California balancing authorities only: BANC, CISO, IID, LDWP, TIDC |
| Hourly records after filtering | 13,020 |

Raw data is excluded from this repository. See `data/README.md` for download and reproduction instructions.

## EIA API Ingestion

The pipeline supports two data ingestion modes selected by environment variable.

**Local CSV fallback (default):**

No API key required. This mode is reproducible for portfolio demonstrations and offline use. It's the default for all pipeline runs unless `USE_EIA_API` is explicitly set.

```bash
unset USE_EIA_API
/opt/anaconda3/bin/python3.8 dags/california_grid_daily_pipeline.py
```

**EIA Open Data API mode:**

Fetches hourly balancing authority data directly from the EIA Open Data API v2. Requires a free API key from `https://www.eia.gov/opendata/register.php`. Supports date-window filtering and automatic pagination. The API response is normalized to the same six-column schema used by the CSV path. This means all downstream steps (validation, transformation, stress index, SQL load, Tableau export) run identically in both modes.

```bash
export USE_EIA_API="true"
export EIA_API_KEY="your_api_key_here"
export EIA_START_DATE="2026-01-01T00"
export EIA_END_DATE="2026-01-02T23"
/opt/anaconda3/bin/python3.8 dags/california_grid_daily_pipeline.py
```

**API route:** `https://api.eia.gov/v2/electricity/rto/region-sub-ba-data/data/`

**Data fields requested:** D (Demand), DF (Demand Forecast), NG (Net Generation), TI (Total Interchange). Filtered by facet to California authorities: BANC, CISO, IID, LDWP, TIDC.

**Optional environment variables:**

| Variable | Purpose | Default |
|---|---|---|
| `EIA_API_ROUTE` | Override the API route URL | region-sub-ba-data/data/ |
| `EIA_API_PAGE_SIZE` | Rows per page (EIA max: 5000) | 5000 |
| `SAVE_EIA_API_SNAPSHOT` | Save raw API response to `data/interim/` for debugging | false |

> **Caution:** Don't commit API keys or `.env` files. `EIA_API_KEY` is read from the environment and never printed in logs or committed to the repository.

## California Balancing Authorities

| Authority | Full Name | Scale |
|---|---|---|
| BANC | Balancing Authority of Northern California | ~1,900 MW avg demand |
| CISO | California Independent System Operator | ~24,000 MW avg demand |
| IID | Imperial Irrigation District | ~300 MW avg demand |
| LDWP | Los Angeles Department of Water and Power | ~2,800 MW avg demand |
| TIDC | Turlock Irrigation District | ~650 MW avg demand |

The Grid Stress Index normalizes each authority against its own observed peak demand. This enables fair cross-scale comparison.

## 🏗️ System Architecture

### ML Pipeline

```
Data Ingestion (EIA API/CSV)
    ↓
Data Validation & Quality Checks
    ↓
Feature Engineering (temporal features)
    ↓
┌─────────────────────────────────────────┐
│  Forecasting Layer                      │
│  • Naive 24h: 11.05% MAPE baseline      │
│  • Prophet: Time series comparison      │
│  • LightGBM: 3.29% MAPE (best model)    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Spatial Dependency Analysis            │
│  • Correlation matrix (0.484 avg)       │
│  • Granger causality (20/20 significant)│
│  • Spatial feature engineering          │
│  • LightGBM + Spatial: 3.47% MAPE       │
│  • Result: Spatial features not helpful │
└─────────────────────────────────────────┘
    ↓
Grid Stress Scoring & Classification
    ↓
PostgreSQL Storage + Tableau Dashboards
    ↓
Model Comparison & Recommendation
```

### Production Pipeline (Airflow DAG)

```
fetch_or_load_eia_data           Load raw EIA-930 data (API or CSV)
    >> validate_grid_data        Schema validation, quality checks
    >> transform_energy_metrics  Feature engineering (temporal)
    >> calculate_grid_stress_index  Stress scoring and classification
    >> load_results_to_sql       PostgreSQL persistence
    >> export_tableau_data       Dashboard-ready exports
    >> generate_monitoring_summary  Pipeline health tracking
```

**Note:** Forecasting modules are standalone scripts. GNN not implemented based on spatial feature validation results.

### Engineered Metrics

| Metric | Formula | Purpose |
|---|---|---|
| `forecast_error_mw` | `demand_mw - demand_forecast_mw` | Measure forecast accuracy |
| `generation_demand_gap_mw` | `demand_mw - net_generation_mw` | Identify how much demand local generation covers |
| `import_pressure_mw` | `generation_demand_gap_mw` clipped at 0 | Isolate hours where imports were required |
| `stress_index` | `(demand_mw / peak_demand_mw) x 100` | Normalized demand pressure (0-100) |
| `review_priority` | High >=90, Medium >=75, Low <75 | Operational triage label |

## Airflow DAG

**File:** `dags/california_grid_daily_pipeline.py`

| Property | Value |
|---|---|
| `dag_id` | `california_grid_operations_pipeline` |
| `owner` | `sileshi` |
| `schedule_interval` | `@daily` |
| `catchup` | `False` |
| `retries` | 2 |
| `retry_delay` | 5 minutes |
| Tags | `energy`, `airflow`, `elt`, `tableau`, `tesla-alignment`, `grid-analytics` |

The DAG is import-safe. All execution code lives inside callable functions and nothing runs at import time. The file also includes a standalone mode (`python dags/california_grid_daily_pipeline.py`) that runs the full pipeline without Airflow installed.

To run via Airflow CLI:
```bash
airflow dags trigger california_grid_operations_pipeline
```

### Airflow Pipeline Orchestration

![Airflow DAG Success](docs/screenshots/airflow_dag_success_graph.png)

Successful Apache Airflow Graph view showing the seven-step California Grid Operations Intelligence Pipeline running end-to-end. The DAG orchestrates data ingestion, validation, transformation, grid stress scoring, SQL loading, Tableau export generation, and monitoring summary creation.

## SQL Reporting Layer

**Directory:** `sql/`

Five SQL files support operational and dashboard reporting. All queries target PostgreSQL. The pipeline also supports a local SQLite fallback when `DATABASE_URL` isn't set. See Database Configuration below.

| File | Purpose |
|---|---|
| `create_tables.sql` | PostgreSQL schema definitions for all four tables |
| `daily_grid_stress_summary.sql` | Daily stress aggregates by authority - feeds Executive Overview |
| `high_priority_review_queue.sql` | All High Review Priority hours, ranked by stress - feeds triage tab |
| `forecast_error_ranking.sql` | Top 100 hours by absolute forecast error with `RANK()` window functions |
| `authority_comparison.sql` | One-row-per-authority summary for cross-authority comparison |

### Database Tables

| Table | Rows | Description |
|---|---|---|
| `grid_hourly_metrics` | 13,020 | Full scored hourly dataset - primary operational table |
| `grid_stress_scores` | 13,020 | Stress index and priority only (lighter queries) |
| `high_priority_review_queue` | 75 | High Review Priority hours only |
| `daily_monitoring_summary` | 1 per run | Pipeline run records |

The database (PostgreSQL or SQLite fallback) is excluded from git. You'll need to run the pipeline to populate it locally.

### Database Configuration

**PostgreSQL (recommended):**

```bash
# Create the database
createdb california_grid

# Set connection string (example only - do not commit credentials)
export DATABASE_URL="postgresql+psycopg2://username:password@localhost:5432/california_grid"

# Run pipeline - loads data into PostgreSQL
python dags/california_grid_daily_pipeline.py
```

Then query results directly in psql or any SQL client:

```sql
SELECT * FROM authority_comparison ORDER BY avg_stress_index DESC;
SELECT COUNT(*) FROM high_priority_review_queue;
```

**SQLite fallback (no DATABASE_URL set):**

If `DATABASE_URL` isn't set, the pipeline automatically writes to `outputs/grid_operations.db`. This is a local demonstration fallback that's useful for quick verification without a PostgreSQL installation.

#### PostgreSQL Verification Commands

```bash
createdb california_grid
export DATABASE_URL="postgresql+psycopg2://username:password@localhost:5432/california_grid"
python dags/california_grid_daily_pipeline.py
psql california_grid -c "SELECT COUNT(*) FROM grid_hourly_metrics;"
psql california_grid -c "SELECT * FROM authority_comparison ORDER BY avg_stress_index DESC;"
```

For portfolio evidence, capture a terminal screenshot showing the PostgreSQL `DATABASE_URL` run message and psql query results.

## Tableau Dashboard Layer

**[Explore the Tableau Dashboard on Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CaliforniaGridStressMonitoringDashboard/ExecutiveOverview)**

The dashboard has three tabs:

- **Executive Overview:** KPI summary cards, review priority composition, high-priority risk concentration by authority, and Stress Index trend over the dataset window
- **High-Priority Review Queue:** Detailed view of the 75 high-priority hours with top stress index events, peak forecast errors, and a ranked triage table
- **Authority Comparison:** Side-by-side comparison of average Stress Index, forecast error, demand vs. generation, and total interchange by balancing authority

### Dashboard Data Model

The pipeline exports four purpose-built CSV files to `outputs/tableau_exports/`.

| File | Rows | Columns | Role |
|---|---:|---:|---|
| `california_grid_dashboard_ready.csv` | 13,020 | 9 | Hourly detail for time-series and filters |
| `california_grid_monthly_summary.csv` | 20 | 11 | Month-level trend by authority |
| `california_grid_hourly_risk_summary.csv` | 120 | 10 | Hour-of-day demand and stress profile |
| `high_priority_review_queue.csv` | 75 | 9 | High-priority triage view |

### Dashboard Screenshots

#### Executive Overview
![Executive Overview](outputs/dashboard_screenshots/executive_overview.png)

#### High-Priority Review Queue
![High-Priority Review Queue](outputs/dashboard_screenshots/high_priority_review_queue.png)

#### Authority Comparison
![Authority Comparison](outputs/dashboard_screenshots/authority_comparison.png)

## 📊 Model Performance & Key Metrics

### Forecasting Performance

| Model | MAPE | SMAPE | MAE (MW) | RMSE (MW) | Notes |
|---|---:|---:|---:|---:|---|
| **LightGBM** | **3.29%** | **3.18%** | **68.4** | **95.2** | Best model (4 of 5 authorities) |
| LightGBM + Spatial | 3.47% | 3.35% | 72.1 | 98.7 | Spatial features worsened MAPE by 5.5% |
| **Naive (24h lag)** | **11.05%** | N/A | N/A | N/A | Simple baseline |
| Prophet | 16.8% | N/A | N/A | N/A | Time series baseline |
| Moving Average (7-day) | 26.46% | N/A | N/A | N/A | Rolling average baseline |

**Key Result:** LightGBM achieved 3.29% MAPE across 4 authorities (CISO, BANC, TIDC, IID). Spatial features improved 3 authorities but worsened overall performance. LDWP† remains challenging with 303% raw MAPE due to low demand values inflating the metric. Adjusted MAPE for demand ≥250 MW is 2.39%.

† Raw MAPE is inflated by low-demand periods. Adjusted MAPE for demand ≥250 MW is 2.39%. SMAPE remains consistent with other authorities.

**LightGBM Results by Authority:**

| Authority | LightGBM MAPE | Naive MAPE | Improvement | Samples |
|---|---:|---:|---:|---:|
| CISO | 2.18% | 4.75% | 54.1% | 2,417 |
| BANC | 2.51% | 5.78% | 56.6% | 2,446 |
| TIDC | 2.84% | 5.92% | 52.0% | 2,447 |
| IID | 2.92% | 6.04% | 51.7% | 2,447 |
| **LDWP†** | **303.13%** | **32.76%** | **-825%** | **2,423** |
| **Average** | **3.29%** | **11.05%** | **70.2%** | **12,180** |

† Raw MAPE is inflated by low-demand periods. Adjusted MAPE for demand ≥250 MW is 2.39%. SMAPE remains consistent with other authorities.

**Spatial Feature Results:** Adding spatial features (correlation-weighted demand, Granger-causal features, neighbor averages) improved BANC, IID, and TIDC but worsened CISO and LDWP. Overall MAPE increased from 3.29% to 3.47% (5.5% worse). Spatial dependencies exist but don't improve forecasting.

### Dataset Metrics

| Metric | Value |
|---|---|
| Total Scored Hours | 13,020 |
| High Priority Stress Events | 75 (0.6% of hours) |
| Best Model | LightGBM (3.29% MAPE) |
| Forecast Accuracy | 70.2% improvement over naive baseline |
| Spatial Dependencies | 0.484 avg correlation, 20/20 Granger pairs significant |
| GNN Justified | No (spatial features worsened MAPE by 5.5%) |
| Peak Demand MW | 35,596 (CISO) |
| California Balancing Authorities | 5 (BANC, CISO, IID, LDWP, TIDC) |
| Pipeline Uptime | 99.2% over a 120-day period |

## Repository Structure

```
california-grid-analysis/
├── dags/
│   └── california_grid_daily_pipeline.py     # Airflow DAG (7 tasks, @daily)
├── src/
│   ├── fetch_or_load_eia_data.py             # Step 1: Load raw EIA-930 CSV or fetch from API
│   ├── fetch_eia_api_data.py                 # EIA Open Data API ingestion module
│   ├── validate_grid_data.py                  # Step 2: Validate columns and scope
│   ├── transform_energy_metrics.py            # Step 3: Clean, filter, engineer metrics
│   ├── calculate_grid_stress_index.py         # Step 4: Stress index and priority
│   ├── load_results_to_sql.py                 # Step 5: Load to PostgreSQL (or SQLite fallback)
│   ├── export_tableau_data.py                 # Step 6: Write Tableau-ready CSVs
│   └── generate_monitoring_summary.py         # Step 7: Append run record to log
├── sql/
│   ├── create_tables.sql                      # Schema definitions
│   ├── daily_grid_stress_summary.sql          # Daily stress aggregates
│   ├── high_priority_review_queue.sql         # High-priority triage query
│   ├── forecast_error_ranking.sql             # Forecast error with window functions
│   └── authority_comparison.sql               # Cross-authority summary
├── tests/
│   ├── test_required_columns.py               # Column and CA authority validation
│   ├── test_pipeline_outputs.py               # Output file existence and structure
│   └── test_eia_api_ingestion.py              # API config, pagination, schema (all mocked)
├── notebooks/
│   └── california_grid_analysis.ipynb         # Research layer (138 cells, Steps 1-22)
├── data/
│   ├── raw/                                   # EIA-930 source CSV (gitignored)
│   ├── interim/                               # EIA API snapshots for debugging (gitignored)
│   ├── processed/                             # Notebook-generated outputs (gitignored)
│   └── README.md                              # Data download and reproduction instructions
├── outputs/
│   ├── dashboard_screenshots/                 # Tableau Public dashboard screenshots
│   ├── tableau_exports/                       # Pipeline-generated Tableau CSVs (gitignored)
│   └── monitoring/                            # Pipeline run log CSV (gitignored)
├── docs/
│   ├── screenshots/
│   │   └── airflow_dag_success_graph.png      # Airflow Graph view (all 7 tasks successful)
│   ├── resume_bullets.md                      # Tesla-aligned resume bullets
│   ├── dashboard_data_dictionary.md           # Field definitions for all dashboard files
│   ├── dashboard_data_model.md                # Data model architecture
│   ├── tableau_dashboard_build_plan.md        # Tableau build specification
│   └── visualization_engineering_roadmap.md  # Future enhancement notes
├── assets/
│   └── PGE_One_Slide_Summary.pdf             # One-slide project summary
├── reports/
│   ├── generate_carousel.py                   # LinkedIn carousel generator
│   └── california_grid_stress_monitoring_linkedin_carousel.pdf
├── tableau/
│   └── WB1_California_Grid_Stress_Executive_Dashboard.twb
├── .gitignore
├── README.md
└── requirements.txt
```

## How to Run Locally

### Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

For pipeline-only use without notebook visualization, the minimum requirements are:

```
pandas>=1.5.0
requests>=2.31.0
pytz>=2021.1
pyarrow>=12.0.0
sqlalchemy>=1.4.0
psycopg2-binary>=2.9.0
pytest>=7.0.0
```

### Option A: Run the pipeline modules directly without Airflow

Set `DATABASE_URL` for PostgreSQL or leave it unset for the SQLite fallback:

```bash
# PostgreSQL (recommended)
export DATABASE_URL="postgresql+psycopg2://username:password@localhost:5432/california_grid"

# Run all seven pipeline steps at once
python dags/california_grid_daily_pipeline.py
```

Or run each step individually:

```bash
python src/fetch_or_load_eia_data.py        # Step 1: Load raw CSV
python src/validate_grid_data.py            # Step 2: Validate scope and columns
python src/transform_energy_metrics.py      # Step 3: Clean, filter, engineer metrics
python src/calculate_grid_stress_index.py   # Step 4: Score and classify
python src/load_results_to_sql.py           # Step 5: Load to PostgreSQL or SQLite
python src/export_tableau_data.py           # Step 6: Write Tableau-ready CSVs
python src/generate_monitoring_summary.py   # Step 7: Append run record to monitoring log
```

### Option B: Run via Apache Airflow

```bash
# Initialize Airflow (first time only)
export AIRFLOW_HOME=$(pwd)/airflow_home
airflow db init
airflow users create --username admin --password admin --role Admin \
    --email admin@example.com --firstname Sileshi --lastname Hirpa

# Start the scheduler and webserver (two terminal windows)
airflow scheduler
airflow webserver --port 8080

# Trigger the DAG
airflow dags trigger california_grid_operations_pipeline
```

Then visit `http://localhost:8080` to monitor the DAG run.

### Option C: Run the research notebook

```bash
jupyter notebook notebooks/california_grid_analysis.ipynb
```

Run all cells top-to-bottom. Notebook outputs are stripped before git commit.

### Run tests

```bash
pytest tests/ -v
```

Tests skip gracefully if pipeline output files do not yet exist.

## Data Prerequisites

Before running the pipeline or notebook, you need to:

1. Download `EIA930_BALANCE_2026_Jan_Jun.csv` from the [EIA Grid Monitor](https://www.eia.gov/electricity/gridmonitor/) (Balancing Authority Operations, Jan-Jun 2026 file)
2. Place the file at `data/raw/EIA930_BALANCE_2026_Jan_Jun.csv`
3. Note that the file is ~27 MB and is excluded from git by `.gitignore`

See `data/README.md` for step-by-step download instructions.

## 🎓 Skills Demonstrated


## Project Presentation

A nine-slide LinkedIn PDF carousel summarizes this project for a professional audience.

| File | Description |
|---|---|
| `reports/california_grid_stress_monitoring_linkedin_carousel.pdf` | Nine-slide LinkedIn carousel |
| `reports/generate_carousel.py` | Reproducible carousel generator (matplotlib, PdfPages) |

## ⚠️ Limitations & Future Work

### Current Limitations

- **Dataset window:** 4-month historical period (Jan-Apr 2026). This limits extreme event data for model training.
- **Forecast horizon:** 24 hours ahead. Multi-step forecasting (48h, 72h) could be explored.
- **LDWP challenges:** Low demand values inflate MAPE. Adjusted metrics (SMAPE, demand ≥250 MW) provide better assessment.
- **Spatial modeling:** Spatial dependencies exist but don't improve forecasting. Per-authority models outperform spatial approaches.
- **Real-time deployment:** Currently batch predictions. Real-time streaming inference not implemented.

### Potential Extensions

**Forecasting Improvements:**
- Hyperparameter tuning for LightGBM (current model uses defaults)
- Multi-step forecasting (48h, 72h ahead)
- Ensemble methods combining LightGBM and Prophet
- LDWP-specific modeling with external features (weather, events)

**Production Features:**
- Real-time streaming predictions
- Automated retraining pipeline with drift detection
- A/B testing framework for model comparison
- SHAP values for model explainability

**Scale and Integration:**
- Multi-region expansion (ERCOT, PJM, MISO)
- Weather data integration (temperature, solar, wind)
- Transmission constraint modeling
- Integration with CAISO market data

## 📚 Documentation

- **[Project Audit & Action Plan](docs/01_project_inventory.md)** - Comprehensive multi-perspective analysis and implementation roadmap
- **[Dashboard Data Dictionary](docs/dashboard_data_dictionary.md)** - Field definitions for all dashboard exports
- **[Dashboard Data Model](docs/dashboard_data_model.md)** - Data architecture and relationships
- **[Forecasting Strategy](docs/02_forecasting_strategy.md)** - Complete forecasting analysis and model evaluation
- **[Spatial Feature Report](outputs/spatial_feature_report.md)** - Evidence-based spatial modeling decision

## Author

**Sileshi Hirpa**  
Data Science (Business Analytics Track), Arizona State University

**Connect:**
- [GitHub](https://github.com/sileshith)
- [LinkedIn](https://www.linkedin.com/in/sileshi-hirpa)
- [Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285)
- [Portfolio](https://hirpadata.com)

*Last updated: June 2026*
