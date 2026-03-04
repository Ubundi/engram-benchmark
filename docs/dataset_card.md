# Dataset Card

## Dataset summary

Current benchmark source datasets in this repository:
- `openclaw-memory-benchmark-v2.json` (legacy V2 task set)
- sample scaffold splits under `data/splits/*.sample.jsonl`

The V2 dataset is used to evaluate runtime memory recall behavior under baseline and
memory-augmented conditions.

## Provenance

- V2 source: imported from historical plugin-repo benchmark assets.
- Canonical conversion: performed at load time by `benchmark.tasks.legacy_v2`.
- Included sample JSONL files are minimal CI-safe fixtures, not leaderboard-grade data.

## Intended use

- Runtime benchmarking of agent memory behavior.
- Regression checks when changing retrieval, memory, or prompting systems.
- CI smoke tests for benchmark pipeline integrity.

## Out-of-scope use

- General model capability benchmarking outside memory-focused scenarios.
- Safety certification or legal/compliance attestation.

## Licensing

- Repository code and docs are MIT-licensed.
- Dataset redistribution rights for imported legacy assets should be confirmed before
  external republishing.

## PII policy

- Do not add real personal data, private keys, or secrets to datasets.
- Keep benchmark conversations synthetic or fully anonymized.
- Remove sensitive content immediately if detected.

## Data quality controls

- Required canonical task fields: `id`, `input`, `reference_answer`.
- Schema checks enforced by tests for sample splits.
- Runtime outputs include per-prompt evidence for audit.

## Known limitations

- Current dataset package is legacy and pre-curated.
- Coverage may not represent all memory failure modes in production agents.
- Category balance and temporal complexity should be re-validated when the new dataset
  package lands.
