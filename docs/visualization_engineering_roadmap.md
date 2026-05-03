# Data Visualization Engineering Roadmap

**Project:** California Grid Reliability Analysis  
**Purpose:** Portfolio-ready grid reliability dashboard with attention to data visualization engineering standards

---

## 1. Current Project Scope

This project is being developed as a portfolio-ready data analytics and business intelligence project focused on California electricity grid reliability. The current scope includes:

- **Python-based data preparation:** full data pipeline in Jupyter Notebook covering ingestion, cleaning, feature engineering, and export to dashboard-ready CSV files
- **Clean processed dataset for dashboarding:** a filtered, validated, and enriched California-only dataset exported from the notebook and ready for use in BI tools
- **Tableau as the primary dashboard tool:** the main visualization layer demonstrating KPI design, time-series analysis, heatmaps, and operational risk filters
- **Power BI as a simplified cross-platform BI version:** a beginner-level Power BI dashboard created to demonstrate transferable dashboard thinking across platforms, not to claim advanced Power BI expertise
- **GitHub-ready documentation and reproducibility:** clean repository structure with documented data sources, requirements, and workflow steps so any reviewer can reproduce the analysis

---

## 2. Engineering Principles Considered

The following data visualization engineering principles have informed the design decisions in this project, even where they are not yet fully implemented:

- **Performance and scalability:** raw data files are excluded from the repository; the dashboard uses a preprocessed, lightweight CSV to reduce load time and avoid rendering delays
- **Dashboard rendering efficiency:** the notebook outputs large interactive charts that are stripped before GitHub commit, keeping the repository fast to clone and rendering-friendly
- **Interactive filtering and drill-down design:** Tableau filters are designed around operationally meaningful dimensions (year, month, season, risk level, peak hour) that mirror how a grid analyst would investigate data
- **Accessibility and readable visual design:** risk classifications use clearly labeled categories rather than ambiguous numeric thresholds; color choices are planned to avoid confusion between similar-looking states
- **Responsive layout for different screen sizes:** the dashboard is designed desktop-first with screenshot-friendly dimensions for portfolio and website presentation
- **Clean data pipeline before visualization:** all field renaming, timestamp conversion, scope filtering, and feature engineering are completed in the notebook before any data enters Tableau or Power BI

---

## 3. What This Project Does Now

The project currently implements the following practices:

- Uses processed, dashboard-ready CSV files instead of feeding raw data directly into Tableau or Power BI
- Separates raw data, processed data, summary outputs, notebooks, documentation, and visual assets into clearly named directories
- Excludes large raw and processed CSV files from the GitHub repository using `.gitignore`, while documenting exactly how to reproduce them
- Strips large Plotly HTML outputs from the notebook before committing, so GitHub can render the notebook
- Organizes documentation, assets, and notebook outputs for portfolio and website use

---

## 4. Future Enhancements

The following improvements are planned as next steps and are not yet implemented:

- **Tableau dashboard publication:** finalized dashboard on Tableau Public with KPI cards, time-series trend lines, hour-by-day-of-week heatmap, and season filters
- **Power BI beginner version:** completed Power BI file with matching KPI measures using DAX, risk level slicer, and comparable visual layout
- **Precomputed summary tables:** monthly aggregate table, hourly risk summary, and KPI snapshot table to support faster dashboard loading at scale
- **Aggregation and downsampling techniques:** for any future version handling multi-year datasets, applying time-bucketing or pre-aggregation before import
- **Accessibility improvements:** color contrast checks using WCAG guidelines, clear axis labels, and alternative text for all chart images
- **Responsive dashboard screenshots:** multiple screenshot exports at different resolutions for use on a personal website and LinkedIn project card
- **Optional web dashboard prototype using React or D3.js:** if pursued in the future, this would demonstrate custom data visualization engineering beyond BI tools — not currently implemented and would only be claimed once built
- **Possible Mapbox integration:** geographic choropleth showing grid stress by balancing authority service territory — not currently implemented

---

*Last updated: 2026-05-03*
