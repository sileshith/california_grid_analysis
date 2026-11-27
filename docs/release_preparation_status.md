# Release preparation status

Preparation stopped at the operator-data download gate. OASIS returned HTTP 429 (Too Many Requests) on the summer day-ahead request after returning the spring day-ahead and actual reports. No cross-source comparison or storage-adjusted holdout result is established.

## Requested downloads

Use CAISO OASIS, System Demand, CAISO Demand Forecast. Request both Day Ahead (DAM) and Actuals (ACTUAL), with the CAISO total area. Keep all returned rows and columns. These are the official query names and process identifiers documented in the [CAISO OASIS FAQ](https://www.caiso.com/documents/oasis-frequently-asked-questions.pdf). The UTC end bounds below are exclusive.

The exact parameters, target paths, and hashes of completed downloads are in [the request manifest](../verification/oasis_download_requests.json). Raw ZIP files remain ignored.

- DAM, `20250407T07:00-0000` to `20250414T07:00-0000`. Downloaded. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20250407T07%3A00-0000&enddatetime=20250414T07%3A00-0000&version=1&market_run_id=DAM&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_DAM_20250407_20250414.zip`.
- ACTUAL, `20250407T07:00-0000` to `20250414T07:00-0000`. Downloaded. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20250407T07%3A00-0000&enddatetime=20250414T07%3A00-0000&version=1&market_run_id=ACTUAL&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_ACTUAL_20250407_20250414.zip`.
- DAM, `20250707T07:00-0000` to `20250714T07:00-0000`. Download required. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20250707T07%3A00-0000&enddatetime=20250714T07%3A00-0000&version=1&market_run_id=DAM&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_DAM_20250707_20250714.zip`.
- ACTUAL, `20250707T07:00-0000` to `20250714T07:00-0000`. Download required. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20250707T07%3A00-0000&enddatetime=20250714T07%3A00-0000&version=1&market_run_id=ACTUAL&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_ACTUAL_20250707_20250714.zip`.
- DAM, `20251006T07:00-0000` to `20251013T07:00-0000`. Download required. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20251006T07%3A00-0000&enddatetime=20251013T07%3A00-0000&version=1&market_run_id=DAM&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_DAM_20251006_20251013.zip`.
- ACTUAL, `20251006T07:00-0000` to `20251013T07:00-0000`. Download required. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20251006T07%3A00-0000&enddatetime=20251013T07%3A00-0000&version=1&market_run_id=ACTUAL&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_ACTUAL_20251006_20251013.zip`.
- DAM, `20251201T08:00-0000` to `20251208T08:00-0000`. Download required. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20251201T08%3A00-0000&enddatetime=20251208T08%3A00-0000&version=1&market_run_id=DAM&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_DAM_20251201_20251208.zip`.
- ACTUAL, `20251201T08:00-0000` to `20251208T08:00-0000`. Download required. [Download report](https://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&startdatetime=20251201T08%3A00-0000&enddatetime=20251208T08%3A00-0000&version=1&market_run_id=ACTUAL&resultformat=6). Save as `data/raw/operator_checks/SLD_FCST_ACTUAL_20251201_20251208.zip`.

## Header inspection

The available bulk file has battery and storage columns. Their exact names and the inspected file hash are in [the header record](../verification/eia_storage_headers.json). The inspected file falls outside the holdout. A generation field alone does not establish a charging-load correction. No formula or sensitivity result has been asserted.

## Source discrepancies

A read-only tree inspection of the protected review repository at `046c15b` found `.github/workflows/verify.yml`, `Makefile`, and `src/demo.py`. It found no docker-compose, event-validation, interval-store, or interval-DAG files. A corrected source commit is needed before porting those components. The review repository was not modified.

The specified `literature_review_source.md` was not found in the checkout or Downloads. Its exact source is needed before editing or reference verification.

## Remaining work

Operator diagnostics, sensitivity scoring, component ports, literature verification, publication documents, notebook updates, hygiene verification, employer PDF, and final clean-clone validation remain unfinished. No full-suite test count, zero-skip claim, clean hygiene result, or publication preview is reported.

## Replay gate

Fresh-clone scoring completed but the full JSON byte comparison failed. Only Prophet authority metrics differed. All headline values and other fields matched. The published JSON was not changed. The exact differences and tested environment are recorded in [the replay result](../verification/replay_result.json). The original scoring runtime and optimizer randomness need investigation before replay can be marked verified.
