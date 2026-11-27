# Evaluation design

Recorded November 26, 2026. This Phase 0 document specifies the design. The executable specification and final holdout freeze belong to Phase 2.

## RQ1. Day-ahead forecasting

Would a local model improve upon the authority forecast enough for a shadow trial? Issue at noon Pacific for the next Pacific delivery day. Represent issue and hour-ending target timestamps in UTC. Include the actual local delivery intervals on clock-change days. Use only predictors available by issue time. Treat the archived authority forecast as a retrospective benchmark unless its historical publication time can be established. Use EIA-adjusted demand as the proposed retrospective target, with reported demand as sensitivity. Publish data coverage for both. Later revisions cannot enter issue-time predictors without vintage evidence.

Select the candidate on chronological development data. Fit preprocessing and tune boosting rounds before the final holdout. Compare to the published authority forecast, a previous-week local-hour baseline and an issue-time moving average. Include Prophet and LightGBM in the full benchmark. Store paired predictions and the observed coverage before exclusions.

For each common eligible day and authority, average absolute errors on identical eligible target hours. For each authority divide the candidate's mean daily MAE by the operator's mean daily MAE, giving days equal weight. Compute G as the geometric mean of the five authority ratios. The null is G ≥ 1. Keep the hourly MW errors, ratios, coverage and peak-hour errors by authority. A zero operator denominator or unavailable authority precludes the five-authority headline. Report zero candidate errors explicitly and omit log-based inference when it is undefined.

Use paired moving blocks of delivery days, jointly across authorities, recomputing G within each replicate. Plan a one-sided 95% upper bound. Before scoring, archive dated splits, source vintages, candidate, target fields, release-delay assumptions, exact eligibility and coverage thresholds, block length, sensitivity settings, seed, replicates and code revision. Select block length from development data. Tag the executable specification before final scoring. Deterministic replay uses the same frozen inputs.

Minimum worthwhile proportional improvement m: **open for Sileshi**. Advance to shadow testing only if the bound clears 1 − m and the prespecified coverage and peak-hour criteria hold. Without m report comparative performance and leave adoption open.

## RQ2. Revision of a retrospective review queue

Compare only shared authority-hours with observed reported and adjusted demand in the same snapshot. Use first-record handling for the historical reproduction and document conflicting duplicates in the audit. Apply the two-decimal, 90%-of-peak rule at each step. Compare reported demand/reported peak, adjusted demand/reported peak, then adjusted demand/adjusted peak. Count and identify retained, entered and exited hours at both transitions. A later version of the bulk file is a separate input. This fixed-snapshot comparison is descriptive.
