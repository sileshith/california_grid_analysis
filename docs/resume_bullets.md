# Resume Bullets — California Grid Operations Intelligence Pipeline

**Project:** California Grid Operations Intelligence Pipeline  
**Target role:** Tesla Energy Services Transformation & Analytics Internship  
**Skills demonstrated:** Python, Apache Airflow, PostgreSQL, SQL, Tableau, REST API ingestion, ELT pipeline design, data validation, operational monitoring

---

## Primary Resume Bullets

Use these on your resume under a **Projects** section. Pick 2–3 that best match the specific job description.

---

**1. Pipeline and orchestration (Airflow, ELT, PostgreSQL)**

> Built an Airflow-orchestrated California grid operations analytics pipeline using Python, PostgreSQL, SQL reporting, and Tableau-ready exports to process EIA-930 hourly balancing authority data and monitor demand pressure, forecast error, generation-demand gaps, and interchange reliance across CISO, BANC, IID, LDWP, and TIDC.

---

**2. PostgreSQL reporting layer**

> Developed PostgreSQL-based reporting queries for daily grid stress summaries, high-priority review queues, peak demand monitoring, forecast error ranking with window functions, and cross-authority comparisons across California balancing authorities; pipeline connects via DATABASE_URL for environment-based credential management.

---

**3. ELT pipeline conversion**

> Converted a notebook-based California grid stress analysis into a production-style ELT workflow with modular Python scripts, data validation, automated Grid Stress Index calculation, PostgreSQL database loading, Tableau-ready CSV exports, and a pipeline monitoring summary for operational tracking.

---

## Optional Supporting Bullets

Use these to fill in additional detail or adapt for specific job descriptions.

---

**4. EIA API ingestion**

> Added EIA Open Data API ingestion option with environment-based API key handling, pagination, date-window parameters, schema normalization, and local CSV fallback for reproducible execution; API response is normalized to the same schema as the existing pipeline so all downstream validation, transformation, and PostgreSQL loading steps run identically in both modes.

---

**5. Feature engineering**

> Engineered operational grid metrics — forecast error, generation-demand gap, and import pressure — from EIA-930 balancing authority data and built a normalized Grid Stress Index enabling fair comparison across California authorities operating at scales ranging from ~500 MW (IID/TIDC) to ~35,000 MW (CISO).

---

**6. Data validation and testing**

> Implemented a data validation layer and pytest test suite for the California grid pipeline, checking required column presence, California authority scope, stress index bounds, review priority classification, and output file generation before any downstream consumer receives data.

---

**7. Dashboard and stakeholder output**

> Designed and published a three-tab interactive Tableau dashboard on Tableau Public for California grid stress monitoring, including an executive KPI overview, high-priority triage queue, and authority comparison view; supported by a layered CSV data model (hourly detail, monthly summary, hourly risk profile, KPI snapshot).

---

## LinkedIn Project Description

> **California Grid Operations Intelligence Pipeline**  
> An Airflow-orchestrated ELT pipeline analyzing California grid reliability using EIA-930 hourly balancing authority data. Built modular Python pipeline stages (fetch, validate, transform, score, load, export, monitor), EIA Open Data API ingestion with pagination and schema normalization, PostgreSQL-based SQL reporting views for operational triage, and a three-tab Tableau dashboard. Demonstrates energy analytics skills in Python, Airflow, PostgreSQL, SQL, REST APIs, and Tableau aligned with grid operations support roles.  
> Tools: Python · Apache Airflow · PostgreSQL · SQL · EIA Open Data API · Tableau Public · pandas · pytest · requests

---

## GitHub Repository Description (one line)

> Airflow-orchestrated California grid operations analytics pipeline: Python ELT, EIA Open Data API ingestion, PostgreSQL SQL reporting, and Tableau-ready exports from EIA-930 balancing authority data.

---

*Last updated: May 2026*
