# California Grid Operational Risk Overview

A portfolio project developed for the **Data Visualization Engineer Intern** role at **Pacific Gas and Electric Company (PG&E)**.

## Project Overview

This project demonstrates a beginner-to-intermediate data visualization workflow built around **California balancing authority electricity demand data**. The goal was to transform raw operational data into clear visual products that support **grid reliability monitoring** and **risk-informed decision making**.

The project combines two complementary artifacts:

- **Analysis Artifact:** a Jupyter Notebook that documents the full analytical workflow, including data cleaning, validation of California-only scope, UTC-to-Pacific time conversion, and engineering of a custom **Stress Index**
- **Visualization Artifact:** an interactive Tableau dashboard designed to monitor periods when demand approaches observed peak levels and may deserve closer operational review

## Why this project matters

PG&E’s mission depends on safe, reliable service supported by careful data interpretation. This project was designed to reflect that mindset by emphasizing:

- **Grid Reliability:** highlighting periods when electricity demand moves close to observed peak demand
- **Risk-Informed Decision Making:** organizing high-priority hours into readable charts and review tables
- **Data Quality:** validating scope, fixing misleading charts, and documenting workflow corrections
- **Visualization Clarity:** improving readability through combined views, panel views, and ranked summaries

## Business Question

How can California grid demand data be prepared and visualized so that a reviewer can quickly identify periods that may deserve additional operational attention?

## Methods Used

- Python
- pandas
- Plotly
- Jupyter Notebook
- Tableau Public

## Analytical Workflow

The notebook demonstrates the following workflow:

1. Load and inspect the raw dataset  
2. Rename and standardize important columns  
3. Clean missing and duplicate records  
4. Convert UTC timestamps to Pacific Time  
5. Validate that the dataset matches the California project scope  
6. Filter to California balancing authorities only  
7. Build comparative demand visualizations  
8. Engineer a simple **Stress Index**:

   **Stress Index = (Current Demand / Peak Demand for that Balancing Authority) × 100**

9. Classify hours into review-priority categories  
10. Summarize the top review hours in table and chart form  

## Key Outputs

### 1. Jupyter Notebook
The notebook shows the full analytical process, including data preparation, chart refinement, and interpretation.

### 2. Tableau Public Dashboard
The dashboard provides an interactive view of grid demand behavior, adequacy trends, and review-priority summaries.
![Dashboard Preview](assets/Dashboard_riskOverview.png)

**Dashboard link:**  
[Interactive Tableau Dashboard](https://public.tableau.com/app/profile/sileshi.hirpa1285/viz/CAGridOperationalRiskReliabilityDashboard/riskOverview#1) 

## Dashboard Highlights

The Tableau dashboard includes:

- **Hourly Demand Pulse:** tracks demand movement over time
- **Adequacy View:** compares demand against net generation context
- **Risk Leaderboard:** compares average stress behavior across California balancing authorities
- **Review Queue:** organizes hours into review-priority groupings for faster interpretation

## What I learned

This project helped me strengthen skills in:

- data cleaning and transformation in Python
- time-series visualization
- debugging misleading charts
- improving dashboard readability
- using data to support operational review
- presenting results in a structured and professional format

## Limitations

This project uses public data and a custom learning metric for review prioritization. It does **not** represent PG&E’s internal systems, formal enterprise risk models, or internal safety frameworks.

## Future Improvements

Planned next steps include:

- adding forecast error analysis
- improving anomaly detection logic
- refining the Stress Index methodology
- extending the dashboard into a more formal monitoring product
- integrating additional utility reliability context

## Author

**Sileshi Hirpa**  
Data Science Student  
Portfolio project prepared for the **PG&E Data Visualization Engineer Intern** opportunity