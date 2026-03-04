# Evaluation Protocol

## Scope

This document defines scoring behavior and reporting expectations for benchmark runs,
with emphasis on V2 runtime evaluations.

## V2 scoring rubric

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

V2 metrics currently produced in `metrics.json`:
- `v2.mean_score`
- `v2.prompt_count`
- `v2.judged_count`
- `v2.error_count`
- score distribution counts (`v2.score_0`..`v2.score_3`)
- per-question-type aggregates (`v2.category.<type>.mean_score`, `.count`)

## Error handling

- Probe/runtime failures are captured in probe artifacts and counted in `v2.error_count`.
- Judge failures keep prompt-level records with `score: null` and explicit error message.
- Runs still produce artifacts for audit and postmortem.

## Reporting requirements

A benchmark run is considered auditable only if the output directory contains:
- `run_metadata.json`
- `metrics.json`
- `predictions.jsonl`
- protocol phase artifacts (`seed_turns.jsonl`, `probes.jsonl`, `judgments.jsonl` for V2)

## Comparison policy

Current release does not auto-generate baseline-vs-cortex comparison reports.
Operators should execute both conditions with aligned settings and compare metrics and
judgment files directly.
