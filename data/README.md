# Data Directory

This directory holds benchmark datasets, schemas, and staging notes.

## Layout

- `splits/`: canonical JSONL task splits.
  - `v3.jsonl` — 498-task Engram v3 dataset (generated from `raw/engram-v3.json`)
  - `*.sample.jsonl` — small CI-safe sample splits
- `schemas/`: JSON schemas for tasks and predictions.
- `raw/`: source JSON (`engram-v3.json`, `engram-v3-test.json`).

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
