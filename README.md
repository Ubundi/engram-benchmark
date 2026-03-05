# Engram

Runtime-first benchmark for evaluating agent memory behavior.

This project is designed to run directly inside an agent runtime workspace. It is not
library-first. You clone or copy the repo, run benchmark commands, and collect artifacts
from `outputs/`.

## Dataset

504-task [Engram v3](https://huggingface.co/datasets/matthewschramm/engram-v3) dataset. Tests agent memory across 8 question types: temporal reasoning, multi-session, knowledge updates, cross-agent memory, multi-hop reasoning, recurring patterns, and single-session recall.

The dataset is fetched automatically from HuggingFace on first run and cached locally. Authentication is required:

```bash
hf auth login   # or set HF_TOKEN env var
```

## Quickstart

### 1) Install

```bash
python3 -m pip install -e ".[dev]"
```

### 2) Run against the v3 dataset

```bash
python3 -m benchmark.run --agent local_stub
```

### 3) Run on a live agent

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run --agent <openclaw-agent-id>
```

The benchmark seeds memory sessions into the agent, waits for settle, probes recall, then judges answers with an LLM. Whatever memory setup the agent has is what gets measured.

Notes:
- Use `--skip-seed` to skip seeding and only probe + judge a pre-seeded agent.
- Use `--settle-seconds` to control the wait between seed and probe phases.
- Use `--max-tasks N` to run a subset.

## Outputs

Each run creates `outputs/<run_id>/` containing:
- `predictions.jsonl`
- `metrics.json`
- `run_metadata.json`

## Repository map

- `benchmark/`: CLI, adapters, task loader, evaluators, report writers.
- `data/`: v3 dataset (`splits/v3.jsonl`), schemas, and raw source JSON.
- `docs/`: benchmark specification and evaluation protocol.
- `leaderboard/`: submission format and leaderboard policy.
- `outputs/`: run artifacts.
- `tests/`: import, CLI, and schema tests.

## Versioning policy

Semantic versioning applies once protocol and schema behavior stabilizes:
- MAJOR: breaking protocol/schema changes.
- MINOR: backward-compatible benchmark features.
- PATCH: bug fixes and documentation updates.
