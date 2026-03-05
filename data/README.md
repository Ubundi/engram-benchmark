# Data Directory

This directory holds benchmark datasets, schemas, and staging notes.

## Layout

- `splits/`: canonical JSONL task splits used by the standard protocol.
- `schemas/`: JSON schemas for tasks and predictions.
- `raw/v2/`: staging guidance for the V2 dataset refresh.

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
