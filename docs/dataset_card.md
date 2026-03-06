# Dataset Card — Engram v3

## Dataset summary

**Engram v3** (`data/splits/v3.jsonl`) is a 498-task benchmark dataset for evaluating long-term memory in AI agents. It covers 9 question types: temporal reasoning, multi-session recall, knowledge updates, cross-agent memory, multi-hop reasoning, recurring patterns, single-session recall, and fact recall.

Source JSON: `data/raw/engram-v3.json`. A 50-task test subset is available at `data/raw/engram-v3-test.json`.

## Provenance

- Generated from synthetic multi-turn conversation histories designed to stress-test long-term memory systems under a controlled runtime benchmark.
- Canonical JSONL produced by `make ingest-v3` via `benchmark.tasks.openclaw`.
- Sample JSONL files (`*.sample.jsonl`) are minimal CI-safe fixtures, not leaderboard-grade data.

## Intended use

- Public and internal benchmarking of long-term agent memory behavior.
- Comparative evaluation across agents, memory systems, or retrieval strategies under a common protocol.
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
- Runtime outputs include per-prompt evidence for audit and leaderboard verification.

## Known limitations

- Dataset is synthetic; real agent sessions have more noise and topic-hopping.
- Coverage may not represent all memory failure modes in production deployments.
- Temporal reasoning tasks remain the hardest category for semantic retrieval systems.

## Positioning note

Engram v3 is intended as a benchmark dataset, not a product-specific demo corpus. Systems should be evaluated using the same protocol, metrics, and artifact requirements regardless of vendor or memory architecture.
