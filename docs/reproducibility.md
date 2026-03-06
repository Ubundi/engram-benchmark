# Reproducibility

## Environment

- Python 3.10+
- Stable OpenClaw CLI version for live agent runs
- Fixed judge model and endpoint settings across compared conditions
- Official public release: `engram-v3.0`
- Official protocol version: `engram-runtime-v1`

```bash
pip install -e ".[dev]"
```

## Determinism controls

- Use the frozen official split (`v3`) for benchmark-comparable runs.
- Keep `--judge-model`, `--judge-passes`, and `--judge-temperature` unchanged across conditions.
- Keep `--settle-seconds` and `--openclaw-timeout` consistent across conditions.
- Use separate agent IDs for each condition.

## Official benchmark-comparable setting

Runs reported as official Engram v3.0 results should use:

- `--split v3`
- `--judge-model gpt-4.1-mini`
- `--judge-passes 3`
- effective judge temperature `0.3`
- normal seed and judge flow; do not use `--skip-seed` or `--dry-run`

For the full frozen release policy, see [benchmark_release_v3.md](benchmark_release_v3.md).

## Reproducible run procedure

### Baseline condition

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <baseline-agent-id> \
  --condition baseline \
  --split v3
```

### Memory-augmented condition

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <augmented-agent-id> \
  --condition cortex \
  --split v3
```

These commands use the official condition-aware settle defaults. Archive both output directories unchanged before comparison.

## Verification checklist

- `run_metadata.json` exists and includes agent ID and full config.
- `run_metadata.json` includes `benchmark_release`, `protocol_version`, and `official_setting`.
- `metrics.json` exists and includes `mean_score` and per-category fields.
- `seed_turns.jsonl`, `probes.jsonl`, and `judgments.jsonl` exist for each run.
- No probe or judge errors beyond tolerated thresholds for your org.

## Reporting checklist

When sharing results, include:

- Run IDs and commit SHA
- Benchmark release and protocol version
- Agent version and configuration
- Judge model and number of passes
- Dataset version (Engram v3)
- Settle seconds used
- Mean score and per-category scores
- Error count and any known failures observed in run artifacts
