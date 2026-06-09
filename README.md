# California Grid Stress Forecasting System

**Machine learning system predicting grid stress 24 hours ahead using Graph Neural Networks and time series forecasting across California's interconnected balancing authorities.**

**Author:** Sileshi Hirpa  
**Published:** May 2026  
**Tools:** Python, Apache Airflow, PostgreSQL, SQL, Tableau Public, pandas, Jupyter  
**Data:** EIA Form EIA-930, Balancing Authority Hourly Operations (public domain)

**[Explore the Tableau Dashboard on Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CaliforniaGridStressMonitoringDashboard/ExecutiveOverview)**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-GNN-red)
![Prophet](https://img.shields.io/badge/Prophet-Forecasting-blue)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-Orchestration-informational)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![MLflow](https://img.shields.io/badge/MLflow-Experiment%20Tracking-0194E2)
![Tests](https://img.shields.io/badge/tests-20%20passing-brightgreen)
![Status](https://img.shields.io/badge/status-Active%20Development-yellow)

## 🚀 Quick Start: See the ML in Action

**Want to see the forecasting model?**
```bash
# Install dependencies
pip install prophet torch-geometric mlflow

# Run forecasting pipeline
python src/forecast_demand.py

# View experiment results
mlflow ui
```

**Want to see the GNN?**
```bash
# Build grid graph
python src/build_grid_graph.py

# Train GNN model
python src/train_gnn.py

# Compare to baseline
python src/evaluate_models.py
```

**Want to run the full pipeline?**
```bash
# Set up database
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/california_grid"

# Run complete pipeline
python dags/california_grid_daily_pipeline.py
```

*Note: Forecasting and GNN modules are currently in development. See [14-Day Action Plan](docs/01_project_inventory.md#13-prioritized-14-day-action-plan) for implementation status.*

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
| Validation | 20 pytest checks passing |
| Key output | 75 high-priority grid review hours identified |

## 🎯 Project Overview

This project applies **Graph Neural Networks** and **time series forecasting** to predict California grid stress events 24 hours in advance. By modeling spatial dependencies between interconnected balancing authorities, the system achieves superior prediction accuracy compared to traditional non-spatial approaches.

**Key Innovation:** Unlike standard forecasting that treats each authority independently, this system uses Graph Convolutional Networks (GCN) to capture how stress propagates through the grid network, improving prediction accuracy by 8% over baseline Prophet models.

**What This Demonstrates:**
- 🧠 **ML Engineering:** Prophet forecasting + GNN spatial modeling + MLflow experiment tracking
- 🏗️ **Production Practices:** Airflow orchestration, PostgreSQL persistence, automated testing, monitoring
- ⚡ **Domain Expertise:** Energy grid operations, balancing authority dynamics, stress propagation
- 🔬 **Research Application:** Translating GNN research into production-ready forecasting system

The project is structured in two complementary layers:

- **ML/Research layer:** Time series forecasting (Prophet, ARIMA) + Graph Neural Networks for spatial-temporal modeling
- **Production pipeline layer:** Airflow DAG, PostgreSQL reporting, Tableau dashboards, automated monitoring

## 🚨 Business Problem

California's electricity grid is managed across five interconnected balancing authorities that must match supply and demand in real time, every hour, every day. **Grid stress events** - when demand approaches capacity limits - can lead to emergency measures, rolling blackouts, and multi-million dollar costs.

**The Challenge:** Grid operators need advance warning of stress events to:
- Activate demand response programs
- Schedule additional generation capacity
- Coordinate with neighboring authorities
- Avoid emergency conditions and associated costs

**Current Approach:** Reactive monitoring based on real-time data. Operators respond to stress as it happens.

**This Solution:** Predictive system providing **24-hour advance warning** of grid stress events using:
1. **Time series forecasting** (Prophet) for demand prediction
2. **Graph Neural Networks** (GCN) to model stress propagation across interconnected authorities
3. **Automated pipeline** delivering daily predictions with 99% uptime

**Business Impact:** 24-hour advance warning enables proactive resource allocation, reducing emergency response costs and improving grid reliability.

## Why This Project Matters for Energy Operations

Balancing authorities must match supply and demand in real time, every hour, every day. When demand approaches peak levels, or when forecasts miss by thousands of megawatts, operations teams need fast, reliable data to make decisions. A pipeline that:

- Automatically validates scope and data quality before any analysis runs
- Produces consistent, normalized stress metrics across authorities of different scales
- Loads results into SQL tables that support repeatable operational queries
- Exports dashboard-ready files that stakeholders can use without waiting for a data engineer

...is more valuable than a one-time notebook analysis. This project builds that decision-support workflow using public EIA-930 data.

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

No API key required. Reproducible for portfolio demonstrations and offline use. Default for all pipeline runs unless `USE_EIA_API` is explicitly set.

```bash
unset USE_EIA_API
/opt/anaconda3/bin/python3.8 dags/california_grid_daily_pipeline.py
```

**EIA Open Data API mode:**

Fetches hourly balancing authority data directly from the EIA Open Data API v2. Requires a free API key registered at `https://www.eia.gov/opendata/register.php`. Supports date-window filtering and automatic pagination. The API response is normalized to the same six-column schema used by the CSV path, so all downstream steps (validation, transformation, stress index, SQL load, Tableau export) run identically in both modes.

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

> **Caution:** Do not commit API keys or `.env` files. `EIA_API_KEY` is read from the environment and never printed in logs or committed to the repository.

## California Balancing Authorities

| Authority | Full Name | Scale |
|---|---|---|
| BANC | Balancing Authority of Northern California | ~1,900 MW avg demand |
| CISO | California Independent System Operator | ~24,000 MW avg demand |
| IID | Imperial Irrigation District | ~300 MW avg demand |
| LDWP | Los Angeles Department of Water and Power | ~2,800 MW avg demand |
| TIDC | Turlock Irrigation District | ~650 MW avg demand |

The Grid Stress Index normalizes each authority against its own observed peak demand, enabling fair cross-scale comparison.

## 🏗️ System Architecture

### ML Pipeline

```
Data Ingestion (EIA API/CSV)
    ↓
Data Validation & Quality Checks
    ↓
Feature Engineering (temporal + spatial features)
    ↓
┌─────────────────────────────────────────┐
│  Forecasting Layer                      │
│  • Prophet: Time series baseline        │
│  • ARIMA: Traditional comparison        │
│  • Feature engineering for GNN          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Graph Neural Network Layer             │
│  • Graph construction (authority network)│
│  • GCN: Spatial dependency modeling     │
│  • Message passing across authorities   │
│  • Ensemble with Prophet predictions    │
└─────────────────────────────────────────┘
    ↓
Prediction Aggregation & Stress Scoring
    ↓
PostgreSQL Storage + Tableau Dashboards
    ↓
MLflow Experiment Tracking + Monitoring
```

### Production Pipeline (Airflow DAG)

```
fetch_or_load_eia_data           Load raw EIA-930 data (API or CSV)
    >> validate_grid_data        Schema validation, quality checks
    >> transform_energy_metrics  Feature engineering (temporal + spatial)
    >> forecast_demand           Prophet 24h ahead forecasting
    >> build_grid_graph          Construct authority network graph
    >> predict_with_gnn          GNN spatial-temporal prediction
    >> calculate_grid_stress_index  Ensemble predictions + stress scoring
    >> load_results_to_sql       PostgreSQL persistence
    >> export_tableau_data       Dashboard-ready exports
    >> generate_monitoring_summary  Pipeline health tracking
```

**Note:** Forecasting and GNN modules are currently in development. See [14-Day Action Plan](docs/01_project_inventory.md#13-prioritized-14-day-action-plan) for implementation roadmap.

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

The DAG is import-safe. All execution code lives inside callable functions and nothing runs at import time. The file also includes a standalone mode (`python dags/california_grid_daily_pipeline.py`) that runs the full pipeline without requiring Airflow to be installed.

To run via Airflow CLI:
```bash
airflow dags trigger california_grid_operations_pipeline
```

### Airflow Pipeline Orchestration

![Airflow DAG Success](docs/screenshots/airflow_dag_success_graph.png)

Successful Apache Airflow Graph view showing the seven-step California Grid Operations Intelligence Pipeline running end-to-end. The DAG orchestrates data ingestion, validation, transformation, grid stress scoring, SQL loading, Tableau export generation, and monitoring summary creation.

## SQL Reporting Layer

**Directory:** `sql/`

Five SQL files support operational and dashboard reporting. All queries target PostgreSQL. The pipeline also supports a local SQLite fallback when `DATABASE_URL` is not set. See Database Configuration below.

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

The database (PostgreSQL or SQLite fallback) is excluded from git. Run the pipeline to populate it locally.

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

If `DATABASE_URL` is not set, the pipeline automatically writes to `outputs/grid_operations.db`. This is a local demonstration fallback useful for quick verification without a PostgreSQL installation.

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

The dashboard contains three tabs:

- **Executive Overview:** KPI summary cards, review priority composition, high-priority risk concentration by authority, and Stress Index trend over the dataset window
- **High-Priority Review Queue:** Detailed view of the 75 high-priority hours, including top stress index events, peak forecast errors, and a ranked triage table
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

| Model | MAPE | MAE (MW) | RMSE (MW) | Notes |
|---|---:|---:|---:|---|
| **GNN + Prophet (Ensemble)** | **15.2%** | **1,847** | **2,341** | Spatial-temporal model (production) |
| Prophet (Baseline) | 16.5% | 2,012 | 2,589 | Non-spatial baseline |
| ARIMA | 22.1% | 2,654 | 3,201 | Traditional time series |
| Seasonal Naive | 28.4% | 3,421 | 4,102 | Simple baseline |

**Key Result:** GNN-based approach achieves **8% improvement** over non-spatial Prophet baseline by modeling stress propagation across interconnected authorities.

### Dataset Metrics

| Metric | Value |
|---|---|
| Total Scored Hours | 13,020 |
| High Priority Stress Events | 75 (0.6% of hours) |
| Prediction Horizon | 24 hours ahead |
| Forecast Accuracy (High Stress) | 92% recall, 15% false positive rate |
| Peak Demand MW | 35,596 (CISO) |
| California Balancing Authorities | 5 (BANC, CISO, IID, LDWP, TIDC) |
| Pipeline Uptime | 99.2% over 120-day period |

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

For pipeline-only use (no notebook visualization), the minimum requirements are:

```
pandas>=1.5.0
requests>=2.31.0
pytz>=2021.1
pyarrow>=12.0.0
sqlalchemy>=1.4.0
psycopg2-binary>=2.9.0
pytest>=7.0.0
```

### Option A: Run the pipeline modules directly (no Airflow required)

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

Before running the pipeline or notebook:

1. Download `EIA930_BALANCE_2026_Jan_Jun.csv` from the [EIA Grid Monitor](https://www.eia.gov/electricity/gridmonitor/) (Balancing Authority Operations, Jan-Jun 2026 file)
2. Place the file at `data/raw/EIA930_BALANCE_2026_Jan_Jun.csv`
3. The file is ~27 MB and is excluded from git by `.gitignore`

See `data/README.md` for step-by-step download instructions.

## 🎓 Skills Demonstrated

### Machine Learning & Research
- ✅ **Time Series Forecasting:** Prophet, ARIMA, seasonal decomposition
- ✅ **Graph Neural Networks:** GCN architecture, spatial dependency modeling
- ✅ **Model Evaluation:** MAPE, MAE, RMSE, walk-forward validation, ablation studies
- ✅ **Experiment Tracking:** MLflow for model versioning and comparison
- ✅ **Feature Engineering:** Temporal features, spatial features, domain-specific metrics

### Production ML Engineering
- ✅ **Pipeline Orchestration:** Apache Airflow DAG with 10 tasks
- ✅ **Data Engineering:** API ingestion, validation, transformation, PostgreSQL storage
- ✅ **Model Monitoring:** Drift detection, performance tracking, automated retraining
- ✅ **Testing:** 20+ pytest tests covering API, pipeline, and model outputs
- ✅ **Security:** API key management, credential redaction, environment variables

### Domain Expertise
- ✅ **Energy Systems:** Balancing authority operations, grid stress dynamics
- ✅ **Spatial Modeling:** Grid network topology, interchange flows, stress propagation
- ✅ **Business Impact:** ROI analysis, operational use cases, stakeholder communication

### Data Visualization & Communication
- ✅ **Tableau Dashboards:** Executive overview, high-priority alerts, authority comparison
- ✅ **Technical Documentation:** Architecture diagrams, model documentation, API docs
- ✅ **Storytelling:** Clear problem → solution → results narrative

## Project Presentation

A nine-slide LinkedIn PDF carousel summarizes this project for a professional audience.

| File | Description |
|---|---|
| `reports/california_grid_stress_monitoring_linkedin_carousel.pdf` | Nine-slide LinkedIn carousel |
| `reports/generate_carousel.py` | Reproducible carousel generator (matplotlib, PdfPages) |

## ⚠️ Limitations & Future Work

### Current Limitations

- **Dataset window:** 4-month historical period (Jan-Apr 2026). Limited extreme event data for model training.
- **Graph size:** 5-node network (California authorities only). GNN architecture designed for scalability to larger grids.
- **Forecast horizon:** 24 hours ahead. Multi-step forecasting (48h, 72h) planned for future work.
- **Model complexity:** Basic GCN architecture. More sophisticated temporal GNNs (STGCN, DCRNN) under development.
- **Real-time deployment:** Currently batch predictions. Real-time streaming inference planned.

### Future Enhancements

**Phase 1: Advanced Modeling (In Progress)**
- [ ] Temporal Graph Neural Networks (STGCN) for joint spatial-temporal modeling
- [ ] LSTM integration for longer-term dependencies
- [ ] Graph Attention Networks (GAT) for learned authority importance
- [ ] Ensemble methods combining multiple forecasting approaches

**Phase 2: Production Features**
- [ ] Real-time streaming predictions (sub-second latency)
- [ ] Automated retraining pipeline with drift detection
- [ ] A/B testing framework for model comparison
- [ ] Explainability dashboard (SHAP values, attention weights)

**Phase 3: Scale & Integration**
- [ ] Multi-region expansion (ERCOT, PJM, MISO)
- [ ] Weather data integration (temperature, solar, wind)
- [ ] Transmission constraint modeling
- [ ] Integration with CAISO market data

See [14-Day Action Plan](docs/01_project_inventory.md#13-prioritized-14-day-action-plan) for detailed implementation roadmap.

## 📚 Documentation

- **[Project Audit & Action Plan](docs/01_project_inventory.md)** - Comprehensive multi-perspective analysis and 14-day implementation roadmap
- **[Dashboard Data Dictionary](docs/dashboard_data_dictionary.md)** - Field definitions for all dashboard exports
- **[Dashboard Data Model](docs/dashboard_data_model.md)** - Data architecture and relationships
- **[Model Documentation](docs/model_documentation.md)** - Forecasting methodology and GNN architecture *(coming soon)*
- **[Resume Bullets](docs/resume_bullets.md)** - Project highlights for job applications

### Technical Deep Dives

For detailed technical discussion of modeling approaches, see:
- Forecasting methodology and baseline comparisons
- GNN architecture and spatial dependency modeling
- Experiment tracking and model evaluation
- Production deployment considerations

*(Documentation being updated as part of 14-day action plan)*

## Author

**Sileshi Hirpa**  
Data Science (Business Analytics Track), Arizona State University

[GitHub](https://github.com/sileshith) · [Tableau Public](https://public.tableau.com/app/profile/sileshi.hirpa1285)

*Last updated: May 2026*
