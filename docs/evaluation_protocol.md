# Evaluation Protocol

## Scope

This document defines scoring behavior and reporting expectations for Engram benchmark runs.

## Scoring intent

Engram evaluates memory behavior after the original context window is gone. The scoring rubric is designed to separate four materially different outcomes:

- grounded recall of the required project detail
- generic but underspecified recall
- safe abstention
- hallucinated specificity

The rubric should be interpreted as a memory-quality scale, not as a binary QA accuracy label.

## Scoring rubric

Each probe response is judged against ground truth:

- `3`: grounded correct. The response contains the required specific detail from the ground truth. Paraphrase is fine, but the decisive fact must be present. Extra context is acceptable only if it does not introduce a wrong specific claim.
- `2`: generic correct. The response is directionally right or identifies the right object, topic, or conclusion, but it misses the required specific detail. A `2` is partial recall, not full success.
- `1`: abstained/non-answer. The response says it lacks the memory or context, refuses to answer, or otherwise avoids a concrete answer without introducing a wrong specific claim.
- `0`: hallucinated/incorrect specific claim. The response supplies a wrong or fabricated specific fact about the target. If it mixes relevant context with an incorrect specific answer, score it `0`.

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
