# Leaderboard Policy

## Current status

A public automated leaderboard is not yet active. This policy defines submission and review expectations for future activation and for private internal leaderboards.

The current frozen public benchmark setting is [Engram v3.0](benchmark_release_v3.md).

## Eligibility

A submission is eligible only if it includes:

- Benchmark release: `engram-v3.0`
- Protocol version: `engram-runtime-v1`
- Full run artifacts (`predictions.jsonl`, `metrics.json`, `run_metadata.json`, phase artifacts)
- Agent version and configuration
- Reproducible command sequence
- Dataset version: Engram v3
- Official scoring settings as defined in [benchmark_release_v3.md](benchmark_release_v3.md)

## Primary metric

`mean_score` — the mean judge score (0–3 scale) across all probed tasks.

## Secondary metrics (tie-break and diagnosis)

- Per-category mean scores (`category.<type>.mean_score`)
- Grounded correct rate (fraction of responses scoring 3)
- Hallucination rate (fraction of responses scoring 0)
- Abstention rate (fraction of responses scoring 1)
- Error count

## Governance

- Submissions without complete artifacts are ineligible.
- Submissions missing the official release metadata are ineligible.
- Submissions that change the frozen judge settings must be labeled exploratory rather than official.
- Maintainers may request reruns with pinned settings for verification.
- Any corrected or superseded result must preserve historical traceability.
- Submissions must disclose settle seconds, judge model, and number of judge passes used.
