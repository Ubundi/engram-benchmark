# Exploratory Repeated Runs: `split=test`

This document tracks exploratory benchmark runs on the `test` split.

These runs are for pilot benchmarking, debugging, and early stability checks. They are not official Engram v3.0 paper-grade results and should not be mixed with the final `v3` campaign.

## Current exploratory protocol

Use this block only for runs that match all of the following:

- split: `test`
- condition-specific benchmark run
- no `--dry-run`
- same judge settings within a repeated-run block
- same `skip_seed` choice within a repeated-run block
- same `flush_sessions` choice within a repeated-run block

## Baseline exploratory block

This is the current comparable baseline block:

- condition: `baseline`
- split: `test`
- `skip_seed=false`
- `flush_sessions=true`
- agent ID: `main`
- judge model: `gpt-4.1-mini`
- judge passes: `3`

| Run | Run directory | Agent ID | Split | Skip seed | Flush sessions | Judge model | Judge passes | Task count | Seed count | Mean score | Abstain rate | Retrieval hit rate | Error count | Notes |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `outputs/exploratory/test/baseline/2026-03-06-1646-baseline` | `main` | `test` | `false` | `true` | `gpt-4.1-mini` | 3 | 50 | 50 | 2.20 | 0.26 | 0.72 | 0 | `run_metadata.json` recorded `output_dir=outputs/baseline`, but the stored artifact path is correct |
| 2 | `outputs/exploratory/test/baseline/2026-03-06-2124-baseline` | `main` | `test` | `false` | `true` | `gpt-4.1-mini` | 3 | 50 | 50 | 2.13 | 0.18 | 0.70 | 0 | Comparable with run 1 |
| 3 | `outputs/exploratory/test/baseline/2026-03-07-1022-baseline` | `main` | `test` | `false` | `true` | `gpt-4.1-mini` | 3 | 50 | 50 | 1.78 | 0.38 | 0.58 | 0 | Comparable with runs 1-2 |

## Baseline exploratory summary

| Condition | N runs | Mean mean_score | Mean abstain rate | Mean retrieval hit rate | Included in exploratory comparison |
|---|---:|---:|---:|---:|---|
| `baseline` | 3 | 2.04 | 0.27 | 0.67 | Yes |

## Excluded runs

Do not mix these into the comparable baseline block above.

| Run directory | Why excluded |
|---|---|
| `outputs/exploratory/test/baseline/2026-03-06-1451-baseline` | Used `skip_seed=true`, so it belongs to a different exploratory configuration block |
| `outputs/exploratory/test/baseline/2026-03-06-1423-no-memory` | Earlier exploratory run outside the current standardized baseline block |

## Next blocks

- `cortex`: pending 3 comparable exploratory runs
- `clawvault`: pending 3 comparable exploratory runs if the condition is available

## Notes

- Use this file for exploratory `test`-split campaigns only.
- Keep final paper-grade repeated runs in [docs/repeated_runs.md](/Users/matthew-schramm-ubundi/Desktop/Ubundi.nosync/cortex-benchmark/docs/repeated_runs.md).
