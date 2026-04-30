# AGENTS.md

## Project

Engram Benchmark — a runtime benchmark for evaluating long-term memory in AI agents. It seeds multi-turn conversations into an agent runtime, waits for memory processing, then probes recall in a fresh session with no prior context.

## Tech Stack

- Python 3.10+, managed with uv
- Dataset hosted on HuggingFace (public, no auth required)
- Judge model: OpenAI API (gpt-4.1-mini)
- Target agent runtime: OpenClaw CLI adapter
- CI: GitHub Actions (lint + test + dataset validation)

## Project Structure

```
benchmark/           # Core benchmark code
  adapters/          # Agent adapters (OpenClaw CLI, HTTP, local stub)
  config.py          # RunConfig, official release constants
  judge.py           # LLM judge scoring (0-3 rubric)
  run.py             # Main benchmark runner
  reports/           # Markdown report generation
  tasks/             # Dataset loading, HF fetcher, normalization
data/                # Schemas, splits, raw datasets (gitignored)
docs/                # Benchmark spec, evaluation protocol, release policy
scripts/             # Validation, dataset tools
tests/               # Pytest test suite
outputs/             # Benchmark run artifacts (gitignored)
```

## Build & Test

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

Lint and test (mirrors CI):
```bash
ruff check benchmark tests
ruff format --check benchmark tests
pytest
```

Dry run (no agent or API key needed):
```bash
python3 -m benchmark.run --agent local_stub --dry-run --max-tasks 3
```

## Commit Convention

This is a public open source repo. Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.) via `/oss-commit`. No AI co-author tags.

## OpenClaw Cortex Plugin Reference

The benchmark targets **`@ubundi/openclaw-cortex`** (v2.5.0) — the OpenClaw plugin that provides long-term memory via Cortex. When you need implementation details, config options, or recent changes, **use the GitHub MCP plugin** to read from `ubundi/openclaw-cortex` rather than guessing.

### How the plugin works

- **Auto-Recall** (`before_agent_start` hook) — queries `/v1/recall` and prepends `<cortex_memories>` block before each agent turn
- **Auto-Capture** (`agent_end` hook) — flattens new user+assistant messages and submits to `/v1/jobs/ingest` (async). Watermark tracks ingested messages to avoid duplicates.
- **Recovery Detection** — detects unclean prior sessions and prepends `<cortex_recovery>` block on next start

### Agent tools (LLM-invocable)

- `cortex_search_memory` — natural language search of long-term memory
- `cortex_save_memory` — explicitly save a fact/preference to memory
- `cortex_forget` — remove a memory

### In-chat commands (auto-reply, no LLM invocation)

- `/checkpoint [summary]` — save session context to Cortex (auto-summarizes if no summary given)
- `/sleep` — mark session as cleanly ended (clears recovery state)
- `/audit [on|off]` — toggle local audit logging to `.cortex/audit/`

### CLI commands (`openclaw cortex ...`)

- `status` — API health, latency, memory counts
- `memories` — memory count, session count, maturity, top entities
- `search [query...]` — search memories from terminal (`--mode decisions|...`)
- `config` — show current plugin configuration
- `pair` — generate a TooToo pairing code
- `reset [--yes]` — permanently delete all memories

### Gateway RPC

- `cortex.status` — programmatic health/metrics (version, knowledgeState, recallMetrics, retryQueuePending)

### Key config options (in `openclaw.json` → plugins.entries.@ubundi/openclaw-cortex.config)

| Option | Default | Notes |
|--------|---------|-------|
| `autoRecall` | `true` | Inject memories before turns |
| `autoCapture` | `true` | Extract facts after turns |
| `recallTopK` | `10` | Max memories after scoring |
| `recallProfile` | `"auto"` | auto/default/factual/planning/incident/handoff |
| `recallReferenceDate` | _now_ | Fixed ISO date for benchmarks (temporal anchor) |
| `namespace` | `"openclaw"` | Auto-derived from workspace dir |
| `dedupeWindowMinutes` | `30` | Client-side dedupe window |
| `noveltyThreshold` | `0.85` | Similarity above this = duplicate |

### Accessing plugin source

Use the GitHub MCP plugin to read files from `ubundi/openclaw-cortex`:
```
owner: ubundi, repo: openclaw-cortex, path: src/plugin/index.ts  # main plugin wiring
owner: ubundi, repo: openclaw-cortex, path: src/plugin/tools.ts  # tool registration
owner: ubundi, repo: openclaw-cortex, path: src/plugin/cli.ts    # CLI commands
owner: ubundi, repo: openclaw-cortex, path: src/plugin/commands.ts # in-chat commands
owner: ubundi, repo: openclaw-cortex, path: src/features/recall/  # recall logic
owner: ubundi, repo: openclaw-cortex, path: src/features/capture/ # capture logic
owner: ubundi, repo: openclaw-cortex, path: src/cortex/client.ts  # HTTP client
owner: ubundi, repo: openclaw-cortex, path: CHANGELOG.md          # recent changes
```

## Operational Learnings

When interacting with an OpenClaw instance (installing plugins, configuring conditions, debugging agent behavior), update `agent_docs/ec2_benchmark_server.md` with any new learnings — gotchas, config quirks, plugin setup steps, or behavioral observations. This file is the single source of truth for server operations and must stay current as new memory conditions are added.

## Task-Specific Guides

Read the relevant file before starting task-specific work:

- `agent_docs/ec2_benchmark_server.md` — SSH access, agent memory reset, running benchmarks on the EC2 instance, plugin setup per condition
