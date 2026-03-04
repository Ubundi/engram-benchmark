# Legacy V2 Data Staging

This directory documents how legacy V2 benchmark assets map into the runtime-first scaffold.

## Current state

- Legacy benchmark tasks currently live at repository root:
  - `openclaw-memory-benchmark-v2.json`
- Canonical scaffold sample split derived from legacy V2:
  - `data/splits/v2.sample.jsonl`

## Planned dataset drop

When the new dataset arrives, place files here and convert to canonical JSONL task format:

- Required canonical fields: `id`, `input`, `reference_answer`
- Optional fields: `metadata` (object)

## Loader behavior

`benchmark.tasks.loader.load_tasks` supports:
- Canonical `.jsonl` task files
- Legacy V2 `.json` list files (auto-normalized)
