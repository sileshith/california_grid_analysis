# California Grid Operations Analytics upgrade roadmap

## Purpose and release sequence

The first release serves two readers. A forecasting analyst needs to decide whether a locally trained model merits further use. A reporting analyst needs to know which hours to review and why revisions change that list. Phase 5 addresses a later decision about using a composite score to prioritize a limited review budget.

## Business questions and hypotheses

### RQ1. Does a local model improve next-day demand forecasts enough to merit further use?

**Decision.** A forecasting analyst must decide whether to advance the model selected on validation to a shadow trial, where its forecasts are recorded alongside the existing forecasts. The primary reference is the authority’s published day-ahead forecast. The previous-week seasonal forecast provides a secondary reference that a reviewer can reproduce.

**Primary hypothesis.** For each authority and delivery day, compute candidate and operator MAE on identical eligible target hours. Average daily MAEs across the same eligible days, giving each day equal weight, then divide the candidate average by the operator average for each authority. The primary statistic G is the geometric mean of the five ratios. Test G ≥ 1 against G < 1. Each authority has equal weight on the log-ratio scale. Publish the ratios, paired MW differences, peak-hour losses and coverage for each authority. An operator denominator of zero makes the ratio undefined. Flag perfect candidate forecasts separately and withhold log-based inference for zero ratios. Disclose any unavailable authority and withhold the five-authority headline if its inputs are incomplete.

**Uncertainty and decision.** Resample paired moving blocks of consecutive delivery days, keeping both methods, all hours and all authorities together. Recompute the entire statistic in each replicate. Specify eligible days, handling of calendar gaps, block length, seed, replicate count and confidence level before opening the holdout. Choose block length using development data and report a block-length sensitivity check. With too few independent blocks report descriptive results only. A daily Diebold–Mariano comparison with HAC standard errors is an optional authority-specific sensitivity check on paired MW losses. Apply Holm correction if making five authority-specific significance claims.

Freeze the candidate, issue time, coverage rule, peak-hour criteria and minimum worthwhile proportional improvement m before final scoring. Advance to shadow testing if the one-sided upper confidence bound is below 1 − m and the coverage and peak-hour criteria hold. If the intended user cannot justify a margin, report performance and leave adoption open.

### RQ2. Which hours should an analyst revisit when EIA revises demand?

**Decision.** A dashboard analyst needs to explain why a previously flagged hour leaves the retrospective queue or a different hour enters it. Apply the existing 90%-of-peak rule separately to reported and adjusted demand, recomputing each authority’s peak on identical eligible hours. Publish both peak values and the exact timestamps entering, leaving and remaining in the queue.

**Sequential attribution.** Compare reported demand with its reported peak, adjusted demand with the same reported peak, then adjusted demand with its adjusted peak. Record entered and exited UTC hours at both steps. The decomposition depends on the specified order. In BANC the flag counts are 2, 0 and 3. The original 9,770 MW observation was revised to 2,296 MW. The adjusted series peaks at 3,243 MW on a different date.

**Descriptive question.** The fixed snapshot permits an exact comparison of membership. Report counts and the share of distinct flagged hours whose membership changes, with the union of both queues as the denominator. If both queues are empty, report zero flags and an undefined share. The observed BANC change is a reproducibility example. A later snapshot can show whether the pattern recurs.

### Phase 5 follow-up. At the same review workload, does the composite capture more documented CISO alert days?

**Decision and hypothesis.** An analyst choosing between the demand-only rule and the 50/30/20 composite needs to know what the added inputs buy. Define gain as composite event-day recall minus demand-only event-day recall. The null is gain ≤ 0 and the alternative is gain > 0. Before inspecting evaluation labels, specify the event catalog, eligible days, daily aggregation, review budget and tie handling. Rank the same eligible CISO days under each rule and review the same number of days. Report documented events captured by both rules, by each alone and by neither. If few distinct events occur, give counts and describe the uncertainty. At fixed K reviewed days, precision is captured event days divided by K, while recall divides the same count by all eligible documented event days. With no eligible documented event days, recall is undefined. For a paired recall comparison, exact McNemar inference uses the discordant detections among documented event days only, when independent units are defensible. Group multi-day incidents by episode for a sensitivity analysis and favor a named-case table when events are sparse or dependent.

## How the DAT 490 procedures transfer

| Course stage | Evidence in the Quad Analytics final report | Grid implementation |
|---|---|---|
| Project plan and literature review | The team defined the publisher, stakeholders, questions, measures and inference limits. | Write two analysis questions, identify a user decision for each and document what the EIA data can establish. Use an operator forecast and a seasonal baseline as reference points. |
| EDA and methodology | The team recorded 98,885 monetary reconciliation flags and calculated 676,368 possible nominal area-hour cells. Eligibility depended on the measure. | Audit published, adjusted, missing and observed zero demand separately. Publish the number of eligible authority-hours for each result. |
| Analysis | RQ1 used a constant training-median benchmark, chronological partitions, validation MAE for model selection and an untouched test. Grouped permutation importance used a fixed 8,000-row validation sample. | Predeclare issue time, baselines and MAE. Select models on validation. Assess peak-hour errors and group related lag features if interpretation is needed. |
| Visualization and robustness | RQ2 corrected local spatial tests for multiple comparisons, masked thin financial-map samples and reported interaction tests. | Show eligible counts, replicate findings in a later period and distinguish exploratory results from release metrics. For hourly data account for dependence across consecutive hours or days. |
| Ethics, challenges and recommendations | The team discussed limits, operational safeguards and fallback behavior. The production safeguards were recommendations. | Declare the cost of unnecessary reviews and missed events. Record the fallback source and publication status. Demonstrate recovery before claiming operational readiness. |

The syllabus establishes the sequence of deliverables. The team report establishes which analytical procedures were used. A taxi-specific dollar tolerance, 60-second duration rule, or 100-trip minimum should not become a grid threshold by analogy.

## Phase 0. Establish the measurement contract and baseline

1. Record the repository revision, input checksum, file size, retrieval date if known, fields, UTC coverage, authority list, dependency versions and execution mode. Store secrets outside manifests. Identify the local snapshot and API extracts independently.
2. Give each measure a definition, unit, sign, time basis, source version, eligibility rule, denominator, missing-value treatment and owner script. Distinguish reported demand, adjusted demand, authority forecast and model forecast.
3. Preserve the current CSV-to-SQLite result as a regression reference. Mark inconsistent historical model summaries as superseded. Remove the unsupported uptime claim from release material. Use the existing DAG, SQL modules, Tableau workbook and tests as starting points.
4. Record the approved questions and date the evaluation specification before the new holdout is examined. For RQ1, fix the target demand version, authority weighting, confidence level, block length, coverage rule and practical decision criteria. For RQ2, fix the snapshot, eligibility and rounding rule. Record later changes with their reasons and label resulting analyses exploratory.

**Completion check.** Another reviewer can identify the exact input and reproduce 13,020 scored authority-hours and 75 original flags on this snapshot. New inputs get their own manifest and expected results.

## Phase 1. Build the hourly quality audit and reproduce the queue

1. Extend ingestion and transformation to retain reported, adjusted and imputed fields when supplied, together with source and revision information. Expose unavailable fields in API mode as missing. Keep raw records before deduplication so conflicting duplicates remain auditable.
2. Align authority-hour records to a complete UTC hour-ending calendar. Derive Pacific display times afterward, retaining the UTC key and offset. Distinguish absent records, null measurements and observed zeros. Cover the spring gap and repeated autumn hour in small tests.
3. Produce per-authority coverage, duplicates, conflicting revisions, zero and extreme values, and reported-to-adjusted differences. Flags may overlap. Publish counts of affected unique hours and per-rule counts.
4. With positive interchange meaning export, compute the balance residual in MW as demand minus (net generation minus net interchange). Compare fields of the same vintage and adjustment status. If any required field is missing, label the check unevaluable. Document tolerance and sensitivity. Values derived from the same inputs may agree by construction.
5. Recalculate the existing 90%-of-observed-peak rule under each demand version. Publish peak, eligible hours, entered, exited, retained and queue count by authority. Inspect BANC's peak, LDWP's 94 MW observation and March 8 zeros without assigning causes from their values alone.
6. Keep the retrospective peak rule as a reference. Evaluate a prior-period percentile as a separate candidate, with a specified lookback, warm-up and decision threshold. A score based on a prior percentile may exceed 100%. Preserve the separate composite with weights of 0.50 demand, 0.30 import reliance and 0.20 forecast shock.

**Completion check.** For the audited snapshot, 75 reported-demand flags and 76 adjusted-demand flags share 73 hours. BANC contributes both exits and all three entries. Other authorities retain the same flags. The composite is evaluated separately.

## Phase 2. Build the day-ahead benchmark

1. Proposed issue time is noon Pacific on the preceding day. Define the delivery day by Pacific hour-ending intervals, map to UTC keys and explicitly test 23-, 24- and 25-hour delivery days. Build an issue calendar and record each target's horizon.
2. Declare availability for each predictor. Join observations by publication or known availability time at or before issuance. Exclude later adjustments from historical predictors unless a vintage proves they were available. For a snapshot without publication history, label the result a retrospective simulation and document assumed release delays. Score against a declared actual-demand version and repeat against the other version for sensitivity.
3. Start with the current snapshot for integration. Once history is acquired, choose dated training, validation and final test windows after a coverage audit. Use rolling forecast origins during development. Keep all authorities on the same calendar splits. Fit preprocessing on training history. Use validation only for early stopping, feature selection and model choice, then freeze the specification before final scoring.
4. Compare the same-local-hour previous-week forecast, a moving-average baseline built at issue time, Prophet, LightGBM and the authority's day-ahead forecast. Define a DST policy for the seasonal lookup. Label a previous-day same-hour forecast eligible only when its observation was available at issuance. Benchmark the authority forecast on rows where it exists and distinguish eventual publication from availability as a model input.
5. Persist one prediction per run, method, authority, issue UTC time and target UTC time. Record model version, training cutoff, source snapshot, forecast MW, fallback status and reason. Join actuals by version during evaluation. A common evaluation identifier must link runs from the competing methods.
6. Use the RQ1 five-authority relative MAE summary as primary and publish per-authority MAE in MW alongside it. Add RMSE, signed bias (forecast minus actual), matched sample count and coverage of all intended targets. Report improvement in MAE relative to a named reference. Report a relative percentage only when the reference MAE is positive. Distinguish pooled hourly and equally weighted authority summaries. For WAPE use sum of absolute errors divided by sum of absolute actuals. State the zero-denominator rule. Report authority-level MAE on peak hours identified by an authority-specific training-period 99th percentile. Include counts and, where sample size permits, paired uncertainty intervals using blocks of delivery days.
7. Write held-out predictions and a machine-generated metric summary. Produce per-authority actual-versus-forecast plots, residuals by local hour, peak-hour errors and operator comparisons. Declare plot limits independently of metric eligibility.

**Completion check.** Modifying values published after issue time cannot change the issued forecasts. Validation drives tuning. All headline comparisons share target keys, publish coverage, and can be recalculated from the prediction rows. Model rank is an outcome.

## Phase 3. Publish a reproducible portfolio release

1. Make forecasting consume the validated hourly table. Tableau and reporting are downstream consumers. Generate the README tables, Tableau exports and a short analyst report from the same versioned predictions and queue results.
2. Provide one documented offline command for a fixture run with no API credentials. Separate core and forecasting dependencies, and pin a tested environment. Include an optional full-data command and the exact prerequisites.
3. Add CI for the fixture pipeline and published data contracts. Exercise existing tests plus targeted cases for input revisions, missing hours, DST, issue-time leakage, matched denominators and snapshot-specific queue membership. Generate outputs before checking them. Treat unexpected skips in the required CI job as failures.
4. Start the README with two findings, the period, units and denominators. Show the strengths and limitations of both studies. Describe each verified execution path precisely. Keep the executive summary employer-neutral.
5. Review the publication as an analyst would. Select one BANC queue entry and one forecast error, trace each to source observations, recompute the decision and reconcile it with the dashboard.

**Completion check.** From a fresh checkout, one command exercises the required suite. A reviewer can trace both published findings without access to the author's workstation.

## Phase 4. Demonstrate repeatable daily operations

1. Use Airflow's logical data interval for bounded retrieval. Archive the response or immutable reference with retrieval time, paging metadata and checksum. Retry transient failures, and distinguish an empty interval from a successful complete ingest.
2. Stage each run in shared, run-specific storage. Load version history and update the current hourly view in a transaction, keyed by authority and UTC hour. Publish only after validation. Replace full-table reloads and fixed worker-local temporary paths.
3. Issue forecasts on their own schedule after required inputs pass freshness checks. On failure use a fallback only if it is verified available at issue time. Otherwise record a stale or unavailable status. Keep model and fallback performance separate.
4. Track last successful interval, freshness, missing hours, revisions, forecast coverage and model error once actuals arrive. For operational alerting specify the threshold, owner, response and recovery procedure. Measure uptime only after defining the monitored service, interval, numerator and denominator.
5. Exercise PostgreSQL and the scheduler with a real backfill, overlapping intervals, a repeated day and an injected failure between staging and publication. Retain the last complete published version. Record duration, row counts and outcomes without credentials.

**Completion check.** Replaying an unchanged interval yields identical business rows; late revisions remain traceable; a failed partial load never becomes visible; the next successful scheduled run recovers. Label live API, scheduled Airflow and PostgreSQL paths verified only after executing them.

## Phase 5. Validate the stress measures before extending the model

1. Acquire enough history to cover a summer and an independent evaluation period. Record source vintages. Match CAISO event labels to CISO and to their documented effective periods. Day-level labels support day-level conclusions; other authorities need applicable labels.
2. Compare a historical-peak or percentile rule with the composite at the same review workload. Use only prior information to set thresholds and normalize features. Report events captured, missed events, alerts without a matched event, review hours, precision and recall with underlying counts. Distinguish observed overlaps from formal negatives where the event catalog is incomplete.
3. Check stability across seasons, reported versus adjusted data and reasonable predeclared thresholds. If events are sparse, show the actual cases and limit conclusions. Weather is a later forecasting experiment using weather forecasts issued by the model cutoff.
4. Treat cross-authority dependence as an optional research appendix. Account for daily seasonality, assess stationarity, adjust for multiple testing and repeat on matched forecast targets. Corrected significance alone does not establish forecast benefit.
5. Document the decision to retain, revise or retire each rule, including operational consequences of missed events and unnecessary reviews.

**Completion check.** A reader can distinguish retrospective high demand, a historical association with a documented alert, and evidence for prospective use.

## Repository handoff

| Existing area | Proposed responsibility |
|---|---|
| data/README.md and docs/dashboard_data_dictionary.md | Provenance, hourly keys, units, feature availability and data versions |
| src/validate_grid_data.py and src/transform_energy_metrics.py | Quality ledger, UTC calendar, source-field preservation and reconciliation |
| src/calculate_grid_stress_index.py | Separate peak queue and composite; versioned normalization |
| src/baseline_forecasts.py, src/lightgbm_forecast.py, src/prophet_forecast.py and src/compare_models.py | Shared issue calendar, fitting, saved predictions and matched scoring |
| src/load_results_to_sql.py, sql/ and dags/california_grid_daily_pipeline.py | Incremental staging, transactional publishing, retries, run history and recovery |
| src/export_tableau_data.py, tableau/, tests/ and future CI workflow | Published views, fixture tests and release checks |

## Publication structure

Keep the README to a concise overview, decision questions, generated findings, reproduction command and report link. Use docs/report.md for the business questions, related work and benchmarks, provenance, quality audit, methodology, results, limitations, ethics, monitoring and references. Target half a page for related work and two to three pages for methodology. Introduce the literature where it motivates a design choice. CRISP-DM can supply a short lifecycle map from business understanding through deployment, followed by explicit monitoring and recovery. A separate framework chapter is optional.

## Related work and benchmarks

- Hyndman and Athanasopoulos, *Forecasting: Principles and Practice*, third edition. Use the seasonal naive method and forecast accuracy chapters to define the reproducible reference. [Textbook](https://otexts.com/fpp3/)
- Hong, Pinson and Fan (2014), *Global Energy Forecasting Competition 2012*. Use for benchmark design and load-forecasting context. [Article](https://doi.org/10.1016/j.ijforecast.2013.07.001)
- Diebold and Mariano (1995), *Comparing Predictive Accuracy*. Use for comparisons of dependent loss differences. The primary geometric-mean ratio uses the block bootstrap specified above. [Paper](https://users.ssc.wisc.edu/~behansen/718/DieboldMariano1995.pdf)
- Hong and Fan (2016), *Probabilistic electric load forecasting: A tutorial review*. Cite when discussing a future probabilistic extension. [Article](https://doi.org/10.1016/j.ijforecast.2015.11.011)
