# Data Visualization Engineering Readiness Review

**Project:** California Grid Operational Risk Overview  
**Reviewer:** Internal — Phase 3 Engineering Audit  
**Date:** 2026-05-03  
**Branch reviewed:** main

---

## 1. Purpose of This Review

This document audits the California Grid Reliability Dashboard project against
data visualization engineering standards. It evaluates the data pipeline,
notebook quality, visualization stack, repository hygiene, and engineering
completeness. The goal is to identify what is working well and what needs
attention before this project is presented as a portfolio artifact for
data visualization, business intelligence, operational analytics, or
public-impact analytics roles.

---

## 2. Project Inventory

| Artifact | Location | Status |
| --- | --- | --- |
| Raw EIA-930 data | `data/raw/EIA930_BALANCE_2026_Jan_Jun.csv` | Local only, excluded via `.gitignore` |
| Processed dataset | `data/processed/cleaned_california_grid_data.csv` | Local only, excluded via `.gitignore` |
| Analysis notebook | `notebooks/california_grid_analysis.ipynb` | Committed, outputs stripped |
| Backup notebook (with outputs) | `notebooks/california_grid_analysis_with_outputs_backup.ipynb` | Local only, excluded via `.gitignore` |
| Dashboard screenshot | `assets/Dashboard_riskOverview.png` | Committed |
| One-slide summary PDF | `assets/PGE_One_Slide_Summary.pdf` | Committed |
| Visualization roadmap | `docs/visualization_engineering_roadmap.md` | Committed |
| Data access guide | `data/README.md` | Committed |
| Requirements file | `requirements.txt` | Committed |
| Project README | `README.md` | Committed |
| Directory placeholders | `data/raw/.gitkeep`, `data/processed/.gitkeep`, `outputs/.gitkeep`, `docs/.gitkeep` | Committed |

The `.gitignore` correctly excludes raw and processed CSV files, output tables,
packaged BI files (`.pbix`, `.twbx`, `.hyper`), the backup notebook, and
standard Python/macOS artifacts. Directory structure is preserved via
`.gitkeep` files so the intended layout is clear to any reviewer who clones
the repository.

---

## 3. Data Pipeline Assessment

### 3.1 Pipeline Stages (Notebook Steps 1–20)

The notebook implements a linear pipeline covering all expected stages for
a visualization-ready export:

| Stage | Step | Assessment |
| --- | --- | --- |
| Library imports | Step 1 | Clean — four focused libraries |
| File path configuration | Step 2 | Uses relative paths; `os.makedirs` ensures output folders exist at runtime |
| Data loading | Step 3 | Uses `low_memory=False`, prints shape and column list |
| Column renaming | Step 4 | Renames 8 key fields to snake_case |
| Cleaning (nulls, duplicates, types) | Step 5 | Drops on 3 key fields, deduplicates on BA + timestamp |
| UTC → Pacific Time conversion | Step 5 | Correct use of `tz_convert("America/Los_Angeles")` |
| Scope validation | Steps 7–9 | Strong: investigates unexpected chart, identifies multi-region scope issue, filters to California-only |
| Feature engineering | Step 15 | Stress Index formula clearly defined and documented |
| Review classification | Step 16 | Three-tier categorical label |
| Export | Step 20 | Saves processed CSV and summary table to correct directories |

**Pipeline strengths:**
The scope validation workflow (Steps 7–9) is the strongest section of the
notebook. The author explicitly documents that the first chart looked
misleading, investigates the root cause, and corrects it before continuing.
This reflects the kind of analytical discipline expected in visualization
engineering and operational analytics roles — a chart can run without error
and still be wrong if the data scope does not match the business question.

**Pipeline gaps:**

1. **Notebook idempotency.** Step 15 includes an explicit
   `drop_columns(errors="ignore")` workaround to prevent duplicate merge
   columns from appearing when cells are re-run out of order. A fully
   idempotent notebook would not require this workaround. The fix is to
   consolidate the peak-demand calculation and merge into a single clean
   cell that operates on the original filtered dataframe without
   accumulating state from prior runs.

2. **Wide export — no slim dashboard-ready file.** The processed CSV exports
   all 65+ EIA source columns. The Tableau dashboard and all notebook
   visualizations use approximately 9 of them: `balancing_authority`,
   `local_time_pacific`, `demand_mw`, `demand_forecast_mw`,
   `net_generation_mw`, `total_interchange_mw`, `stress_index`,
   `review_priority`, and `peak_demand_mw`. Adding a second export containing
   only those 9 columns would reduce the Tableau data source size, improve
   dashboard load performance, and demonstrate dashboard-oriented data
   engineering thinking.

3. **Hardcoded review thresholds.** The priority cutoffs (90 for High, 75
   for Medium) are embedded directly in the `label_stress()` function body.
   Promoting them to named constants at the top of the notebook
   (`HIGH_REVIEW_THRESHOLD = 90`) makes the logic easier to read, easier to
   adjust, and easier to explain in a technical interview.

4. **Stress Index window dependency.** The peak demand denominator is derived
   from the Jan–Jun 2026 dataset window only, not from a full historical
   record. This is documented in the notebook and the README, which is the
   correct approach. A brief inline comment in the export step flagging this
   window dependency explicitly would help a downstream reviewer understand
   the metric's scope at the point of use.

---

## 4. Repository and Engineering Hygiene

### 4.1 What Is Working

- **Data files are excluded from Git.** Raw and processed CSVs are excluded
  via `.gitignore`. The `data/README.md` documents the exact EIA download
  page, file name, time period, and local path so any reviewer can reproduce
  the data independently.
- **Directory structure is committed via `.gitkeep` files.** All four key
  directories (`data/raw/`, `data/processed/`, `outputs/`, `docs/`) have
  `.gitkeep` files committed. A reviewer who clones the repository sees the
  intended layout immediately, without needing to run any setup script.
- **Notebook outputs are stripped before committing.** The primary notebook
  has been cleaned of Plotly HTML outputs. This keeps the repository
  lightweight and allows GitHub to render the notebook. The backup notebook
  with full outputs is kept local only and excluded via `.gitignore`.
- **BI-tool package files are excluded.** The `.gitignore` excludes `.pbix`
  (Power BI), `.twbx` (Tableau packaged workbook), and `.hyper` (Tableau
  extract) files. These files are large, binary, and better accessed through
  their respective published platforms.
- **Clean directory separation.** `data/raw/`, `data/processed/`, `outputs/`,
  `notebooks/`, `docs/`, and `assets/` are clearly separated and consistently
  named.
- **Tableau dashboard is published and linked.** The interactive result is
  accessible on Tableau Public, and the README provides a direct link. The
  dashboard screenshot in `assets/` serves as a fallback view.

### 4.2 Minor Issues

| Issue | Severity | Detail |
| --- | --- | --- |
| Requirements not pinned | Low | `requirements.txt` uses minimum version specifiers (`pandas>=1.2.0`). Acceptable for portfolio work, but adding a comment noting the tested environment versions would help a reviewer confirm compatibility. |

---

## 5. Visualization Stack Assessment

### 5.1 Libraries and Tools

| Tool | Role | Status |
| --- | --- | --- |
| Plotly Express | In-notebook interactive charts | Active — 5 chart types implemented |
| Tableau Public | Primary dashboard product | Published and linked |
| Power BI | Simplified cross-platform BI version | Planned — documented in roadmap as future enhancement |
| pandas | Data transformation | Core pipeline dependency |
| numpy | Numeric operations | Used in merge and statistical steps |

### 5.2 Chart Types Implemented

| Chart | Step | Purpose |
| --- | --- | --- |
| Line chart (full dataset) | Step 7 | Diagnostic — intentionally misleading to motivate scope validation |
| Line chart (California only, single series) | Step 11 | Corrected scope view |
| Line chart (multi-series by balancing authority) | Step 12 | Combined comparison across all 5 authorities |
| Faceted line chart (panel view) | Step 13 | Per-authority readability |
| Bar chart (top 10 review hours) | Step 18 | Ranked stress summary with hover context |

The deliberate inclusion of the misleading first chart followed by its
documented correction is a strong portfolio choice. It shows that the author
treats charts as hypotheses to investigate, not outputs to accept.

### 5.3 Chart Engineering Notes

**Strengths:**
- Axis labels and titles are present on all charts.
- Hover data is configured on the bar chart to expose demand, peak, priority,
  and interchange context.
- The panel chart uses `for_each_annotation` to clean auto-generated facet
  labels.
- Color encoding is applied by balancing authority across comparison charts.

**Gaps:**
- No consistent figure size or theme applied across all charts. Different
  `width` and `height` values appear in Step 18 but are absent from earlier
  charts. A shared layout template or `plotly.io.templates.default` setting
  would improve visual consistency.
- No color palette is formally defined. Documenting the color choices and
  checking them against WCAG contrast guidelines — already noted as a planned
  improvement in `visualization_engineering_roadmap.md` — would strengthen
  the accessibility story.

### 5.4 Tableau as Primary Dashboard Layer

The Tableau Public dashboard is the primary visual deliverable. Based on the
dashboard screenshot and the README, it includes:

- **Hourly Demand Pulse** — time-series view of demand movement
- **Adequacy View** — demand compared against net generation context
- **Risk Leaderboard** — average stress behavior across balancing authorities
- **Review Queue** — hours organized into priority groupings

These four views map directly to the notebook's analytical workflow. The
notebook functions as the engineering and preparation layer; the Tableau
dashboard functions as the presentation and decision-support layer. This
separation is a sound architecture for a portfolio demonstrating visualization
engineering principles.

### 5.5 Power BI as Future Cross-Platform Version

The visualization roadmap documents Power BI as a planned simplified
cross-platform version. This is an appropriate addition to the portfolio:
it demonstrates awareness that different organizations use different BI
platforms, and it shows that the author can translate analytical thinking
across tools. The roadmap correctly frames Power BI as a beginner-level
demonstration of transferable dashboard thinking — not a claim of advanced
Power BI expertise. The `.gitignore` already excludes `.pbix` files, so the
repository is structurally ready for this addition when it is built.

---

## 6. Documentation Assessment

| Document | Quality | Notes |
| --- | --- | --- |
| `README.md` | Strong | Covers business question, methods, workflow, key outputs, limitations, and future improvements. Tableau link is present. |
| `data/README.md` | Strong | Exact download instructions, file name, time period, and local path for reproducibility. |
| `docs/visualization_engineering_roadmap.md` | Strong | Clearly separates implemented features from planned ones. Avoids claiming unbuilt capabilities. |
| Notebook markdown cells | Good | Each step has an explanation cell. Language is clear and interview-ready. |
| Data dictionary | Missing | No formal field glossary for the dashboard-relevant columns. The 9 fields that flow from the processed CSV into Tableau are not listed or defined in any single document. |

**Recommendation:** Add a short field glossary to `data/README.md` listing the
9 columns used in the dashboard layer, their original EIA source names, and
their meaning. This closes the gap between the wide processed CSV (65+ columns)
and the narrow visualization layer, and gives any reviewer immediate clarity
about what the dashboard is measuring.

---

## 7. Summary of Key Findings

### Strengths

1. **Scope validation is documented as a workflow correction, not hidden.**
   The notebook shows the misleading first chart, investigates it, and
   corrects it. This is strong evidence of analytical discipline relevant to
   data visualization, BI, and operational analytics roles.
2. **Data reproducibility is fully documented.** Any reviewer can download the
   raw EIA file, run the notebook, and regenerate all processed outputs.
3. **Repository structure is clean and self-explanatory.** `.gitkeep` files,
   a clear `.gitignore`, and named directories make the layout understandable
   before reading a single line of code.
4. **Clean separation between pipeline and dashboard layers.** The notebook
   prepares data; Tableau presents it. No raw data enters the dashboard tool.
5. **The roadmap document distinguishes implemented features from planned ones.**
   This avoids overstating capabilities — a credibility-building choice for
   any technical portfolio.
6. **Stress Index is defined, documented, and its limitations are explicitly
   stated** across the notebook, the README, and the roadmap.
7. **Power BI is positioned as a future cross-platform addition**, not claimed
   as a completed deliverable. The repository is already structured to support
   this addition.

### Gaps Requiring Attention

| Priority | Finding | Action |
| --- | --- | --- |
| High | No slim dashboard-ready export | Add a second CSV export with only the 9 dashboard columns |
| High | No data dictionary | Add field glossary to `data/README.md` |
| Medium | Hardcoded review thresholds | Promote cutoffs to named constants at top of notebook |
| Medium | Notebook not fully idempotent | Replace Step 15 workaround with clean single-pass merge |
| Low | Requirements not version-pinned | Add tested version comment to `requirements.txt` |

---

## 8. Readiness Assessment

| Dimension | Status | Notes |
| --- | --- | --- |
| Data pipeline completeness | Ready | End-to-end workflow runs and exports correctly |
| Scope validation | Ready | Documented investigation and correction |
| Repository hygiene | Ready | `.gitignore`, `.gitkeep`, clean directory layout all in place |
| Notebook engineering | Mostly ready | Idempotency fix and named constants recommended |
| Visualization coverage | Ready | Five chart types, panel and combined views, Tableau dashboard |
| Documentation | Mostly ready | Data dictionary is the remaining gap |
| Portfolio presentation | Ready | README, roadmap, Tableau link, and screenshot are in place |

**Overall:** The project is portfolio-ready with targeted improvements. The two
highest-priority items before sharing are the slim dashboard export and the
data dictionary. The idempotency fix and named threshold constants are secondary
improvements that strengthen the engineering story without blocking use.

---

*Review completed: 2026-05-03*
