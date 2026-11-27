# Measurement definitions

The historical reference uses reported measurements from the bulk file identified in the [manifest](../data/manifest/eia930-9b0b83506002.json). A scored row represents one authority and one UTC hour ending. Local display uses America/Los_Angeles. The transformation removes missing authority or demand and keeps the first duplicate authority/timestamp. Observed zeros remain. Raw row counts include all authorities in the file. A scored-hour count includes only eligible California records. The Phase 1 audit will preserve duplicate and exclusion evidence.

Here D is reported demand, F is the authority forecast, N is reported net generation and I is reported total interchange. All four are hourly values in MW. Positive interchange denotes exports. Adjusted source fields and imputation indicators are distinct from these values.

| Measure | Definition, unit and eligible denominator | Historical handling and implementation |
|---|---|---|
| Mean reported demand | Sum of D divided by scored authority-hours, MW | Per authority across the snapshot, including zeros. Implemented in verify_snapshot. |
| Forecast error | D − F, MW. Positive means the operator underforecast. Absolute error is its magnitude. | Missing F leaves the MW measures missing. Implemented in transform_energy_metrics. |
| Forecast shock | Absolute error divided by D, fraction capped at one | Historical transform substitutes zero for missing ratios or zero demand. This is a scoring convention. Exclude missing forecasts from accuracy evaluation. |
| Generation gap and import pressure | D − N in MW and its positive part respectively | Missing N propagates. Import pressure here is a demand-generation difference. |
| Net import and import reliance | −I in MW and positive net imports divided by D, capped at one | Historical ratio substitutes zero for missing ratios. Implemented in transform_energy_metrics. |
| Normalized demand | (D − minimum D) divided by the authority's full-window range, clipped to [0, 1] | Constant range maps to zero. Historical full-window normalization is retrospective. |
| Peak-relative index and priority | 100 × D / authority peak D, rounded to two decimals before classification | High begins at 90, medium at 75. High-priority count is the number of eligible rows classified high. Verified snapshot has positive authority peaks. A zero peak has no meaningful ratio. Implemented in calculate_grid_stress_index. |
| Composite and level | 0.50 × normalized demand + 0.30 × clipped import reliance + 0.20 × clipped forecast shock, rounded to four decimals | Unitless. High begins at 0.75, elevated at 0.50, moderate at 0.25. Separate from queue membership. Implemented in calculate_grid_stress_index. |
| Queue membership change | Entered = adjusted-only, exited = reported-only, retained = intersection. Changed share = (entered + exited) / union | RQ2 uses the same eligible authority-hours and declares the peak at each step. Empty union yields an undefined share. Phase 1 ownership is the quality-audit workflow. |
| Benchmark losses | MAE is mean absolute error in MW. RMSE is the square root of mean squared error. Model bias is mean forecast minus actual, in MW. WAPE is sum of absolute errors / sum of absolute actuals. | Only paired eligible observations. Missing required inputs make a pair ineligible. A zero WAPE denominator yields an undefined ratio. Phase 2 scoring belongs in compare_models. See the evaluation design for daily and authority weighting. |
