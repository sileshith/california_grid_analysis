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
