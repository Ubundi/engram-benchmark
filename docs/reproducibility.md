# Reproducibility

## Environment

- Python 3.10+
- Stable OpenClaw CLI version for live agent runs
- Fixed judge model and endpoint settings across compared conditions

```bash
pip install -e ".[dev]"
```

## Determinism controls

- Use a fixed `--max-tasks` cap and the same dataset version for all compared runs.
- Keep `--judge-model`, `--judge-passes`, and `--judge-temperature` unchanged across conditions.
- Keep `--settle-seconds` and `--openclaw-timeout` consistent across conditions.
- Use separate agent IDs for each condition.

## Reproducible run procedure

### Baseline condition

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <baseline-agent-id> \
  --settle-seconds 120
```

### Memory-augmented condition

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <augmented-agent-id> \
  --settle-seconds 120
```

Archive both output directories unchanged before comparison.

## Verification checklist

- `run_metadata.json` exists and includes agent ID and full config.
- `metrics.json` exists and includes `mean_score` and per-category fields.
- `seed_turns.jsonl`, `probes.jsonl`, and `judgments.jsonl` exist for each run.
- No probe or judge errors beyond tolerated thresholds for your org.

## Reporting checklist

When sharing results, include:

- Run IDs and commit SHA
- Agent version and configuration
- Judge model and number of passes
- Dataset version (Engram v3)
- Settle seconds used
- Mean score and per-category scores
- Error count and any known failures observed in run artifacts
