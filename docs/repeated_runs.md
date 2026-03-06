# Repeated-Run Reporting Template

This document is a fill-in template for reporting repeated benchmark runs and run-to-run variability once results exist.

## Goal

Report each main condition with multiple benchmark runs, then summarize stability using mean and spread rather than a single point estimate.

## Recommended Minimum

Use at least three full runs per main condition. Five is preferred if runtime budget allows.

| Condition | Minimum runs | Preferred runs | Status |
|---|---:|---:|---|
| `baseline` | 3 | 5 | Pending |
| `clawvault` | 3 | 5 | Pending |
| `cortex` | 3 | 5 | Pending |

If a condition is dropped from the main table, remove it here rather than leaving an incomplete row in the final paper.

## Control Rules

Keep these fixed across repeated runs for a condition:

- benchmark release: `engram-v3.0`
- protocol version: `engram-runtime-v1`
- split: `v3`
- judge model
- judge passes
- judge temperature
- settle seconds for the named condition
- agent version or image
- benchmark commit SHA

Only rerun with the same configuration. If a meaningful setting changes, start a new block and do not pool the runs.

## Run Directory Convention

Use a stable naming pattern so repeated runs are easy to collect later.

```text
outputs/
  baseline/
    run-01/
    run-02/
    run-03/
  clawvault/
    run-01/
    run-02/
    run-03/
  cortex/
    run-01/
    run-02/
    run-03/
```

## Per-Run Log Template

Fill one row per completed run.

### `baseline`

| Run | Run directory | Agent ID | Agent version | Commit SHA | Task count | Judge model | Judge passes | Settle seconds | Mean score | Grounded rate | Hallucination rate | Abstention rate | Error count | Notes |
|---|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| 2 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| 3 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

### `clawvault`

| Run | Run directory | Agent ID | Agent version | Commit SHA | Task count | Judge model | Judge passes | Settle seconds | Mean score | Grounded rate | Hallucination rate | Abstention rate | Error count | Notes |
|---|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| 2 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| 3 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

### `cortex`

| Run | Run directory | Agent ID | Agent version | Commit SHA | Task count | Judge model | Judge passes | Settle seconds | Mean score | Grounded rate | Hallucination rate | Abstention rate | Error count | Notes |
|---|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| 2 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| 3 | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

## Aggregate Summary Template

Fill this only after the per-run tables are complete.

| Condition | N runs | Mean mean_score | SD | 95% CI | Mean grounded rate | Mean hallucination rate | Mean abstention rate | Mean error count | Included in paper |
|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| `baseline` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `clawvault` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `cortex` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

## Per-Category Variance Template

Use this for the hardest or most paper-salient categories first.

| Condition | Category | N runs | Mean | SD | 95% CI | Notes |
|---|---|---:|---:|---:|---|---|
| `baseline` | `temporal-reasoning` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `baseline` | `multi-session` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `cortex` | `temporal-reasoning` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `cortex` | `multi-session` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

## Paper Table Template

Use this as the paper-facing compact version once the aggregate summary is complete.

| System or condition | Runtime family | N | Mean score | 95% CI | Grounded rate | Hallucination rate | Abstention rate |
|---|---|---:|---:|---|---:|---:|---:|
| `baseline` | OpenClaw | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `clawvault` | OpenClaw | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| `cortex` | OpenClaw | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |

## Methods Text Template

Use this paragraph in the paper after filling the placeholders:

> We ran each main Engram condition `TBD` times under the frozen `engram-v3.0` release using identical judge settings, dataset split, and condition-specific settle times. We report the mean across runs together with `TBD` as the spread estimate. Repeated runs used separate agent instances or clean resets between runs, and each reported row is backed by complete benchmark artifacts.

## Caveats Template

Fill this section with anything that would affect variance interpretation.

- `TBD`: Were any runs rerun because of infrastructure failure?
- `TBD`: Did any condition require a disclosed override to settle seconds?
- `TBD`: Were any runs excluded from the aggregate summary? If yes, why?
- `TBD`: Did any agent version change during the repeated-run campaign?

## Completion Checklist

- [ ] At least three runs completed for every included main-table condition.
- [ ] Every included run has full artifacts.
- [ ] The configuration is identical within each repeated-run block.
- [ ] Baseline was rerun alongside augmented conditions.
- [ ] Aggregate mean and spread are filled in for every included condition.
- [ ] The paper table template has been replaced with actual numbers.
