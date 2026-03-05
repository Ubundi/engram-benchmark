# Dataset Card — Engram v3

## Dataset summary

**Engram v3** (`data/splits/v3.jsonl`) is a 504-task benchmark dataset for evaluating agent memory recall behavior. It covers 8 question types: temporal reasoning, multi-session recall, knowledge updates, cross-agent memory, multi-hop reasoning, recurring patterns, and single-session recall.

Source JSON: `data/raw/v3/engram-v3.json`.

## Provenance

- Generated from synthetic multi-turn conversation histories designed to stress-test compaction-based memory systems.
- Canonical JSONL produced by `make ingest-v3` via `benchmark.tasks.openclaw`.
- Sample JSONL files (`*.sample.jsonl`) are minimal CI-safe fixtures, not leaderboard-grade data.

## Intended use

- Runtime benchmarking of agent memory behavior.
- Regression checks when changing retrieval, memory, or prompting systems.
- CI smoke tests for benchmark pipeline integrity.

## Out-of-scope use

- General model capability benchmarking outside memory-focused scenarios.
- Safety certification or legal/compliance attestation.

## Licensing

- Repository code and docs are MIT-licensed.
- Dataset redistribution rights for imported assets should be confirmed before external republishing.

## PII policy

- Do not add real personal data, private keys, or secrets to datasets.
- Keep benchmark conversations synthetic or fully anonymized.
- Remove sensitive content immediately if detected.

## Data quality controls

- Required canonical task fields: `id`, `input`, `reference_answer`.
- Schema checks enforced by tests for sample splits and the full v3 dataset.
- Runtime outputs include per-prompt evidence for audit.

## Known limitations

- Dataset is synthetic; real agent sessions have more noise and topic-hopping.
- Coverage may not represent all memory failure modes in production deployments.
- Temporal reasoning tasks remain the hardest category for semantic retrieval systems.
