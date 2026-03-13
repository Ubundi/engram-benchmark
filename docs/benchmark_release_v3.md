# Official Benchmark Release: Engram v3.0

This document defines the frozen public benchmark setting for Engram v3.0.

Use this release when reporting official benchmark results, submitting to a leaderboard, or citing Engram in external comparisons.

## Release identity

- Benchmark release: `engram-v3.0`
- Protocol version: `engram-runtime-v1`
- Canonical dataset split: `v3`

## Official scoring configuration

- Judge model: `gpt-4.1-mini`
- Judge passes: `3`
- Judge temperature: `0.3`

These values are part of the official setting. If you change them, the run may still be useful for research, but it should be treated as exploratory rather than leaderboard-comparable.

## Runtime protocol

Official runs follow the Engram runtime protocol:

1. Seed
2. Settle
3. Probe
4. Judge
5. Report

The protocol version for this release is `engram-runtime-v1`.

## Condition-specific settle defaults

The official release keeps the benchmark's condition-aware settle defaults:

| Condition | Official settle seconds |
|---|---:|
| `baseline` | 10 |
| `mem0` | 60 |
| `clawvault` | 10 |
| `cortex` | 180 |
| other / unspecified | 120 |

If you override settle seconds, disclose it clearly and do not present the run as directly leaderboard-comparable to the frozen official setting.

## Required artifacts

Official submissions must include:

- `metrics.json`
- `run_metadata.json`
- `predictions.jsonl`
- `seed_turns.jsonl`
- `probes.jsonl`
- `judgments.jsonl`

## Required run metadata

Official runs must record the following in `run_metadata.json`:

- `benchmark_release`
- `protocol_version`
- `answer_model`
- `official_setting`
- `run_id`
- `timestamp_utc`
- `condition`
- `git_commit`
- `config`
- `task_count`
- `prediction_count`
- `seed_count`
- `judgment_count`

## Canonical reporting fields

When publishing results for Engram v3.0, include:

- benchmark release
- protocol version
- dataset split
- condition
- answer model
- judge model
- judge passes
- judge temperature
- settle seconds
- primary metric: mean score
- secondary metrics: grounded rate, hallucination rate, abstention rate, per-category scores
- run ID and git commit

For the OpenClaw CLI reference track in this repo, the supported condition labels are:

- `baseline`
- `mem0`
- `clawvault`
- `cortex`

## Canonical command shape

Baseline example:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <agent> \
  --condition baseline \
  --split v3
```

Memory-augmented example:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <agent> \
  --condition cortex \
  --split v3
```

Alternative memory-system examples:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <agent> \
  --condition mem0 \
  --split v3
```

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent <agent> \
  --condition clawvault \
  --split v3
```

## Exploratory runs

The following are allowed for internal research, but should not be presented as official Engram v3.0 submissions without explicit disclosure:

- alternate answer models under the same row label
- alternate judge models
- alternate judge pass counts
- alternate temperatures
- custom subsets
- `--skip-seed`
- `--dry-run`
- custom settle timing

## Versioning policy

Engram v3.0 is frozen for comparison purposes. Any future benchmark changes that affect task content, protocol semantics, or official scoring settings should be released under a new benchmark release identifier rather than silently changing this one.
