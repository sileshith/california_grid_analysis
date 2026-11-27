# Component port inventory

The verified release bundle HEAD is `afa56acaef5e42093c9ad57c4b057586f91906c5`. It is inspected through the temporary ref `refs/release-prep/bundle-source`. Files are copied individually. No histories are merged and no frozen or published metric files are copied from the bundle.

| Component | Exact source paths | Dependencies | Replacements on release line | Verification |
| --- | --- | --- | --- | --- |
| Demo and Makefile | `src/demo.py`, `Makefile` | Existing standalone pipeline, pandas, NumPy, pytest, SQLAlchemy | None | Isolated demo and full fixture tests |
| Interval store | `src/interval_store.py` | Existing EIA adapter, frozen quality field map, pandas, SQLAlchemy | None | Transaction recovery, stale replay, revisions, interval rejection |
| Forecast release status | `src/forecast_status.py` | pandas, SQLAlchemy, existing authority list | None | DST targets, missing and timely fallback |
| Event validation | `src/event_validation.py`, `data/events/ciso_events.json` | pandas, saved hourly parquet, documented event catalog | None | Equal budgets, event coverage, recomputed release metrics |
| Interval DAG | `dags/grid_interval_operations.py` | Airflow, pendulum, interval store and forecast status | None | DAG import and topology in the orchestration environment |
| Compose | `docker-compose.yml` | Docker, PostgreSQL, Airflow image, application dependencies | None | Configuration inspection. Docker unavailable locally |
| CI | `.github/workflows/grid-release.yml` | Python, PostgreSQL service, test requirements | None | Local equivalents. Hosted CI unverified |
| Publication | `src/publish_report.py` | Metrics JSON, predictions, matplotlib, pandas | None initially. Its output replaces `README.md` and creates `docs/report.md` | Adapt to current metrics, sensitivity evidence, figures and PDF build |
| Contract tests | `tests/test_release_contract.py` | All preceding Python components | None | Focused cases followed by integrated suite |

The bundle dependency pins are inspected but not copied wholesale. The current environment is recorded separately and release dependencies will be tested. The report publisher requires substantial adaptation to preserve the frozen headline and label post-freeze checks. The original publisher contains assertions that must not be adopted without current evidence. Existing tests and the historical pipeline remain on the release line. Component test results are recorded in the implementation audit after execution.
