# Reproducibility

## Environment baseline

Recommended:
- Python 3.10+
- Stable OpenClaw CLI version for V2 live runs
- Fixed judge model and endpoint settings

Install:

```bash
python3 -m pip install -e ".[dev]"
```

## Determinism controls

- Use fixed `--max-tasks` and fixed dataset path for comparisons.
- Keep `--judge-model`, `--judge-passes`, and `--judge-temperature` unchanged across
  baseline and cortex runs.
- Keep `--settle-seconds` and `--openclaw-timeout` consistent across conditions.
- Use separate agent IDs for baseline and cortex.

## Reproducible V2 run procedure

1. Run baseline:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --protocol v2 \
  --condition baseline \
  --agent <baseline-agent-id> \
  --data-path openclaw-memory-benchmark-v2.json
```

2. Run cortex with the same non-condition settings:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --protocol v2 \
  --condition cortex \
  --agent <cortex-agent-id> \
  --data-path openclaw-memory-benchmark-v2.json
```

3. Archive both output directories unchanged.

## Verification checklist

- `run_metadata.json` exists and includes protocol, condition, and config.
- `metrics.json` exists and includes V2 score fields.
- `seed_turns.jsonl`, `probes.jsonl`, and `judgments.jsonl` exist for each run.
- No probe or judge errors beyond tolerated thresholds for your org.

## Reporting checklist

When sharing results, include:
- run IDs
- commit SHA
- protocol and condition
- model/judge settings
- dataset path
- mean and per-category metrics
- known errors/failures observed in run artifacts
