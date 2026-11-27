# Freeze scope

The published manifest in `config/frozen_benchmark.json` at `53d75a2` ties the following files to the freeze. Every observed digest matches the published digest. The full verification is saved in [the hash check](../verification/freeze_hash_check.json).

| File | Published SHA-256 |
| --- | --- |
| `config/holdout.json` | `0c450f8baa93772300e4cea6fc3fa81c20543f6b6760276a95bdb3d4fc906732` |
| `src/benchmark.py` | `5ac6d050d7fddda5cb5b7974b5036883e17804e226e02ffeb8047918b2d201bd` |
| `src/quality_audit.py` | `792451467efbdcce08b5e17ccb68f205ed64219f51cea44732e2b95a547d7e35` |
| `data/manifest/benchmark_sources.json` | `9da4e94bf3c3127c6a54679e0a81ff7ad616cf2e2aeed7e0356f070e26399ea5` |
| `.artifacts/benchmark/hourly.parquet` | `c93d542f88f71b8ee8d2301e5a2d7788ada9962795db3a63457b927716dfa138` |

The frozen specification and these tracked files are unchanged on the release line. `src/acquire_history.py` first appears in scoring commit `bf7169c`. Its acquisition logic is outside the published code-hash scope.

The hourly parquet was extracted from the archived release ZIP and hashed directly. Its bytes match the frozen digest. Saved predictions were also recovered from that archive, but predictions are outside the published freeze hash list.

The annotated `spec-frozen-v1` tag now resolves to `53d75a2`. It was added after scoring and does not establish when scoring occurred.

## Replay

Run `python -m src.replay_benchmark --freeze-ref 53d75a2` after installing `requirements-replay.txt` and restoring the archived hourly parquet to `.artifacts/benchmark/hourly.parquet`. The reference defaults to `spec-frozen-v1`. The command creates a fresh local clone at the selected freeze reference, copies the verified local input, runs the immutable scorer, and compares the entire output file with the published metrics. It changes the historical tag binding only in the disposable clone. No frozen source code is patched.

Replay verification is recorded separately in the release preparation status. A byte comparison failure must remain a failure even when rounded headline values agree.

The fresh-clone replay completed but failed the byte comparison. Differences were confined to Prophet authority metrics. The headline and all other JSON fields matched. See [the result](../verification/replay_result.json) and [the exact differences](../verification/replay_difference.patch). `requirements-replay.txt` records the tested environment, not a verified original scoring environment. Prophet fitting in the immutable scorer has no explicit seed. Whether optimizer randomness or the original runtime explains these differences remains unresolved.

## Quantified replay audit

Both fresh local clone runs were compared with the published JSON at `bf7169c`. The strict byte comparison outcome remains FAIL. Every field outside Prophet authority metrics matched exactly in both runs, including LightGBM, authority, previous-week, moving-average, and all headline fields.

The first run has the following maxima across authorities. Relative differences divide by the absolute published value. A zero published value gives an undefined relative difference.

| Prophet metric | Units | Largest absolute difference | Authority | Largest relative difference | Authority |
| --- | --- | ---: | --- | ---: | --- |
| daily_mae_mw | MW | 109.129167297 | CISO | 4.090304438% | CISO |
| mae_mw | MW | 109.103165155 | CISO | 4.088931027% | CISO |
| bias_mw | MW | 92.2305543551 | CISO | 5.231999866% | CISO |
| rmse_mw | MW | 97.0877367077 | CISO | 2.952971385% | CISO |
| peak_mae_mw | MW | 244.857561378 | CISO | 4.012920587% | CISO |

Platform: macOS-26.7.3-x86_64-i386-64bit. Machine: x86_64. Python: 3.11.5. Packages: prophet 1.5.0, cmdstanpy 1.3.2, lightgbm 4.7.0, pandas 3.0.3, numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1.

The immutable Prophet constructor and fit call set neither a seed nor a thread count. LightGBM explicitly sets random_state and n_jobs as recorded in the audit JSON. Thread environment values are recorded there. No frozen source was changed.

The repeated same-environment run was byte identical to the first run. The original scoring runtime is unavailable. The cause of the published-versus-replay difference remains unresolved. Detailed row differences, undefined relative values, package versions, and repeat comparisons are in [the audit metrics](../outputs/metrics/replay_audit.json).
