# Data Directory

This directory holds benchmark datasets, schemas, and staging notes.

## Layout

- `splits/`: canonical JSONL task splits used by the standard protocol.
  - `v3.jsonl` — 518-task OpenClaw Memory Benchmark v3 (canonical, generated from `raw/v3/`)
  - `*.sample.jsonl` — small CI-safe sample splits
- `schemas/`: JSON schemas for tasks and predictions.
- `raw/v2/`: staging guidance for the V2 dataset refresh.
- `raw/v3/`: source JSON for the v3 dataset (`openclaw-memory-benchmark-v3.json`).
  Regenerate the canonical split with `make ingest-v3`.

## Canonical task fields

Required fields per task record:
- `id` (string)
- `input` (string)
- `reference_answer` (string)

Optional:
- `metadata` (object)

## Safety and governance

- Keep sample files small and CI-safe.
- Do not commit private, sensitive, or proprietary data.
- Validate schema compatibility before adding new splits.
