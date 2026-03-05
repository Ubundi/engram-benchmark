# Cortex Benchmark

Runtime-first benchmark repository for evaluating agent memory behavior.

This project is designed to run directly inside an agent runtime workspace. It is not
library-first. You clone or copy the repo, run benchmark commands, and collect artifacts
from `outputs/`.

## What this repository supports today

- `standard` protocol: generic benchmark scaffold with local/offline stub adapter support.
- `v2` protocol: legacy OpenClaw V2 benchmark execution pipeline with explicit
  `baseline` and `cortex` conditions.
- Legacy V2 source dataset: `openclaw-memory-benchmark-v2.json`.

## Quickstart

### 1) Install

```bash
python3 -m pip install -e ".[dev]"
```

### 2) Inspect CLI

```bash
python3 -m benchmark.run --help
```

### 3) Standard scaffold smoke test

```bash
python3 -m benchmark.run --agent local_stub --split dev
```

### 4) V2 protocol dry-run smoke test

```bash
python3 -m benchmark.run \
  --protocol v2 \
  --condition baseline \
  --agent bench-baseline \
  --data-path openclaw-memory-benchmark-v2.json \
  --max-tasks 5 \
  --dry-run
```

## Run the V2 benchmark on live agents

The V2 protocol is a real runtime flow: seed conversations, settle, probe recall,
then judge answers.

### Baseline condition

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --protocol v2 \
  --condition baseline \
  --agent <openclaw-agent-id> \
  --data-path openclaw-memory-benchmark-v2.json
```

### Cortex condition

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --protocol v2 \
  --condition cortex \
  --agent <openclaw-agent-id> \
  --data-path openclaw-memory-benchmark-v2.json
```

Notes:
- `cortex` mode runs a `/memories` preflight and requires cortex tools to be present.
- Use separate agent IDs for clean baseline vs cortex comparisons.
- Use `--skip-seed` if you only want probe + judge on a pre-seeded agent.

## Outputs

Each run creates `outputs/<run_id>/`.

Core artifacts:
- `predictions.jsonl`
- `metrics.json`
- `run_metadata.json`

Additional V2 artifacts:
- `seed_turns.jsonl`
- `probes.jsonl`
- `judgments.jsonl`
- `v2_report.json`

## Repository map

- `benchmark/`: CLI, protocols, adapters, task loaders, evaluators, report writers.
- `data/`: schemas, sample splits, and raw staging notes.
- `docs/`: benchmark specification, evaluation protocol, reproducibility, and V2 run docs.
- `leaderboard/`: submission format and leaderboard policy docs.
- `outputs/`: run artifacts.
- `tests/`: import, CLI, schema, and V2 protocol dry-run tests.

## Current scope and limitations

- V2 runtime flow and judge scoring are implemented.
- Baseline/cortex comparison report generation is still manual.
- `codex` and `openai` adapters remain stubs in standard mode.
- Final production dataset package is not yet integrated.

## Versioning policy

Semantic versioning applies once protocol and schema behavior stabilizes:
- MAJOR: breaking protocol/schema changes.
- MINOR: backward-compatible benchmark features.
- PATCH: bug fixes and documentation updates.
