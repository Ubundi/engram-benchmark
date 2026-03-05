# V2 Run Guide

## Purpose

Run the V2 memory benchmark against a real agent runtime with auditable outputs.

## Prerequisites

- Python 3.10+
- OpenClaw CLI available on PATH for live runs
- Judge API key (`JUDGE_API_KEY`) for non-dry-run runs
- V2 dataset file present: `openclaw-memory-benchmark-v2.json`

## Recommended run order

1. Dry-run smoke test
2. Live baseline run
3. Live cortex run
4. Manual comparison of run artifacts

## 1) Dry-run smoke test

```bash
python3 -m benchmark.run \
  --protocol v2 \
  --condition baseline \
  --agent bench-baseline \
  --data-path openclaw-memory-benchmark-v2.json \
  --max-tasks 5 \
  --dry-run
```

## 2) Live baseline run

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --protocol v2 \
  --condition baseline \
  --agent <baseline-agent-id> \
  --data-path openclaw-memory-benchmark-v2.json
```

## 3) Live cortex run

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --protocol v2 \
  --condition cortex \
  --agent <cortex-agent-id> \
  --data-path openclaw-memory-benchmark-v2.json
```

## Key flags

- `--skip-seed`: skip replaying seed turns
- `--max-tasks N`: limit probe count
- `--settle-seconds N`: wait window between seed and probe
- `--openclaw-timeout N`: timeout for each OpenClaw CLI call
- `--judge-model`: judge model name
- `--judge-base-url`: OpenAI-compatible endpoint
- `--judge-passes`: judge passes per prompt
- `--judge-temperature`: judge sampling temperature

## Artifacts produced

Each run writes:
- `predictions.jsonl`
- `metrics.json`
- `run_metadata.json`
- `seed_turns.jsonl`
- `probes.jsonl`
- `judgments.jsonl`
- `v2_report.json`

## Operational notes

- Cortex condition validates tool availability before execution.
- Use clean agent state for each condition to avoid cross-condition contamination.
- Keep run settings identical between baseline and cortex for fair comparison.
