# Release preparation status

## Access and preservation

Step 0 switched successfully to `release/v1` at `bf7169c`. Status showed only the two protected untracked folders. The freeze tag was absent and was then created as an annotated local tag at `53d75a23d37021f25f0a62449420fbc5621c2084`. Its annotation explicitly records that it was added after scoring.

The original replay commits remain in history. Frozen source files and the published forecast JSON are unchanged. See [freeze scope](freeze_scope.md).

## Operator-data gate

All seasonal OASIS reports validated. The April files were preserved. Remaining files were acquired sequentially under the prescribed pacing and attempt policy. Exact URLs, targets, attempt times, hashes and report coverage are in the [request manifest](../verification/oasis_download_requests.json). Findings and supported sensitivities are in [operator definitions](operator_definitions.md).

## Validation

Final fresh-clone validation is pending. Earlier local fixture and contract tests passed.

## Local commits

```text
5cdab2a Add isolated freeze-reference replay with strict byte comparison
c14e7c8 Record freeze verification and blocked operator-data handoff
f4aee61 Inventory individual ports from afa56acaef5e42093c9ad57c4b057586f91906c5
b4d6614 Quantify Prophet replay differences and repeat-fit stability
1011cae Port isolated demo from afa56acaef5e42093c9ad57c4b057586f91906c5
c2a15cc Port interval contracts from afa56acaef5e42093c9ad57c4b057586f91906c5
094922a Port forecast status from afa56acaef5e42093c9ad57c4b057586f91906c5
d626e1a Port and rescore events from afa56acaef5e42093c9ad57c4b057586f91906c5
cb70f3c Port interval DAGs from afa56acaef5e42093c9ad57c4b057586f91906c5
86ba1e7 Port Compose configuration from afa56acaef5e42093c9ad57c4b057586f91906c5
95817fb Port release CI from afa56acaef5e42093c9ad57c4b057586f91906c5
c370196 Validate seasonal OASIS reports and quantify post-freeze sensitivities
e2e6e41 Adapt publication from afa56acaef5e42093c9ad57c4b057586f91906c5 with audited figures and PDF
4b49f83 Add clean-clone result notebook and isolated pipeline test fixtures
87c5ee7 Remove private links and machine paths and add release hygiene check
```

This list records the implementation source history before the final status-record commit. The final local Git log supplies the complete commit list.

## Outstanding inputs and unverified environments

The literature source remains missing. Its original wording and full reference list cannot be processed. The strict replay failure remains unresolved. Docker, network PostgreSQL, hosted CI and GitHub rendering require their own verification. No publication action was taken.
