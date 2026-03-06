# Evaluation Protocol

## Scope

This document defines scoring behavior and reporting expectations for Engram benchmark runs.

## Scoring rubric

Each probe response is judged against ground truth:

- `3`: grounded correct
- `2`: generic correct
- `1`: abstained/non-answer
- `0`: hallucinated/incorrect specific claim

Judging is multi-pass (`--judge-passes`) and aggregated by mean score per prompt.

## Judge model interface

Judge endpoint must be OpenAI-compatible:
- URL: `<base_url>/chat/completions`
- Auth: bearer API key
- Inputs: system rubric + question + ground truth + agent response
- Output: JSON containing `score` and `rationale`

## Metrics

Metrics produced in `metrics.json`:
- `mean_score`
- `prompt_count`
- `judged_count`
- `error_count`
- score distribution counts (`score_0`..`score_3`)
- per-question-type aggregates (`category.<type>.mean_score`, `.count`)

## Error handling

- Probe/runtime failures are captured in probe artifacts and counted in `error_count`.
- Judge failures keep prompt-level records with `score: null` and explicit error message.
- Runs still produce artifacts for audit and postmortem.

## Reporting requirements

A benchmark run is considered auditable only if the output directory contains:
- `run_metadata.json`
- `metrics.json`
- `predictions.jsonl`
- phase artifacts: `seed_turns.jsonl`, `probes.jsonl`, `judgments.jsonl`

Official reports must also disclose the evaluated `answer_model`. Direct benchmark deltas should keep that model fixed; if it changes, treat the result as a separate system track rather than a controlled within-system comparison.
