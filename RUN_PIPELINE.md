# Run the v3 Generation Pipeline

## Prerequisites

1. **Claude Code CLI** installed and authenticated with a Claude Max subscription:
   ```bash
   # Verify it works
   claude -p --model sonnet --no-session-persistence "Say hello"
   ```

2. **Python 3.12+** available as `python3`.

3. **Template files** in place:
   - `templates/entity_seed.json`
   - `templates/session_templates.json`
   - `openclaw-memory-benchmark-v2.json` (v2 questions to preserve — lives at repo root)

## Quick Start

Run the full pipeline end-to-end:

```bash
python3 -m scripts.generate_v3 --verbose
```

This executes 6 phases:

| Phase | What it does | ~Time |
|-------|-------------|-------|
| 1 | Load entity seed into registry | instant |
| 2 | Generate ~300 sessions via `claude -p` | ~60-90 min |
| 3 | Generate ~500 questions via `claude -p` | ~45-60 min |
| 4 | Run 10 validation checks | instant |
| 5 | Export to `data/raw/v3/openclaw-memory-benchmark-v3.json` | instant |
| 6 | Print statistics report | instant |

## Incremental / Resumable

The pipeline caches every session and question type to `cache/`. If interrupted, just re-run and it picks up where it left off:

```bash
# Resume — already-generated sessions/questions are loaded from cache
python3 -m scripts.generate_v3 --verbose
```

Skip phases explicitly:

```bash
# Skip session generation (use cached), only generate questions
python3 -m scripts.generate_v3 --skip-sessions --verbose

# Skip question generation too (use cached), just validate + export
python3 -m scripts.generate_v3 --skip-sessions --skip-questions --verbose
```

## Validate / Stats Only

```bash
# Validate an existing output file
python3 -m scripts.generate_v3 --validate-only

# Print statistics for an existing output file
python3 -m scripts.generate_v3 --stats-only
```

## Configuration

All tunable via environment variables (defaults are sensible):

| Variable | Default | Description |
|----------|---------|-------------|
| `CLI_MODEL` | `sonnet` | Model alias passed to `claude --model` |
| `CLI_TIMEOUT` | `120` | Seconds before a single CLI call times out |
| `CLI_MAX_BUDGET_PER_CALL` | `0.50` | Max USD per individual CLI call |

Example with overrides:

```bash
CLI_MODEL=opus CLI_TIMEOUT=180 python3 -m scripts.generate_v3 --verbose
```

## What the CLI Calls Look Like

Each LLM call runs:

```bash
claude -p \
  --model sonnet \
  --no-session-persistence \
  --output-format text \
  --max-budget-usd 0.50 \
  --system-prompt "..." \
  < user_prompt.txt
```

- User prompt is piped via stdin (handles long prompts)
- Rate limited to 40 requests/minute
- Retries up to 3 times on failure with exponential backoff

## Output

- **Raw benchmark JSON**: `data/raw/v3/openclaw-memory-benchmark-v3.json`
- **Canonical benchmark split**: `data/splits/v3.jsonl` — regenerate after pipeline runs with `make ingest-v3`
- **Session cache**: `cache/sessions/*.json` (one file per session)
- **Question cache**: `cache/questions/*.json` (one file per question type)

## Clearing Cache

To regenerate everything from scratch:

```bash
rm -rf cache/
python3 -m scripts.generate_v3 --verbose
```

To regenerate only questions (keep sessions):

```bash
rm -rf cache/questions/
python3 -m scripts.generate_v3 --skip-sessions --verbose
```
