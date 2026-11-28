# Implementation audit

## Local verification

Fresh local clone tested source commit `eb6bec0c08a909328c2cd74561271c393d9d5f0f` in the recorded installed release environment.

The configured full suite ran 48 tests with 0 failures, 0 errors and 0 skips. The isolated demo also completed its fixture suite.

The report build returned 0 and produced 14 US Letter pages. The results notebook executed top to bottom. Hygiene returned 0 and lint returned 0.

Strict replay returned 1. Its byte comparison remains failed. Published metrics are unchanged: True.

The replay audit ran two same-environment frozen fits. They matched each other, while Prophet authority metrics differed from the publication. Every other JSON field matched exactly. The cause remains unresolved. See [freeze scope](freeze_scope.md).

## Individual component ports

The [component inventory](component_port_plan.md) was recorded before copying. The verified bundle HEAD is `afa56acaef5e42093c9ad57c4b057586f91906c5`. Each component was ported individually with the full source SHA in its commit message. The temporary ref was removed. No histories were merged.

| Component | Current execution evidence |
| --- | --- |
| Demo and Makefile | Isolated synthetic pipeline and configured suite passed |
| Interval store | SQLite transaction failure, recovery, revision and stale-replay contract passed |
| Forecast status | Missing output and DST target contract passed |
| Event validation | Equal-budget and catalog-boundary tests passed. Metrics recomputed on release hourly data |
| Interval DAG | Local Airflow import and task dependency edge passed. Both DAGs discovered |
| Compose | Configuration inspected. Docker unavailable, so service startup unverified |
| CI | Workflow adapted to current dependencies and PDF build. Hosted result unverified |
| Publication | Metric-driven report, README, vector figures and employer PDF built locally |

Network PostgreSQL, live API operation, hosted CI and unattended uptime remain unverified. The historical full-snapshot verification is an opt-in check outside the configured fixture suite and was not rerun here. Raw source files remain ignored. The two protected untracked folders were not modified.

## Literature and bibliography

The literature review is now available in `docs/literature_review.md`. The release report condenses it to one PDF page and ends with four gaps and this project's responses. The README links to the shared [APA reference list](references.md); the web report and PDF read the same 24 entries. Each has a completed [verification record](reference_verification.csv), with authoritative source URLs, retrieval digests where available, and notes about dates or metadata differences. The expanded review's unidentified repository and preprint claims remain unverified search leads; they are not release findings.

## Publication validation

The current publication pass supersedes the old font and pagination evidence above. XCharter body fonts and TeX Gyre Heros heading/figure fonts are vendored with licenses and SHA-256 digests under `reports/fonts/`. The PDF uses file-based fontspec loading. Every table is boxed to stay on one page. Figure captions are explicitly left aligned. Verification is a second-level subsection, numbered 10.1 in the PDF.

The targeted stale-number scan is restricted to README.md, docs/, reports/ and notebooks/release_results.ipynb. It checks superseded README model, spatial and test-count claims and the old verification number. See [recorded result](../verification/stale_number_check.json) for the exact patterns and scanned files. Historical snapshot counts and explicitly historical roadmap figures are retained. This does not assert that every numeric claim in the expanded literature review has been independently validated.

## Remaining limits

The original Prophet scoring runtime remains unavailable and strict replay still differs only in its Prophet metrics. CISO storage correction remains unsupported by the observed dedicated battery field. Seasonal OASIS checks diagnose alignment and demand definitions; they do not establish model superiority. The expanded review contains unverified search leads beyond the release bibliography. No merge is authorized or performed.
