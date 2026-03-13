# Engram Benchmark Integration Guide

This guide explains how to run the Engram benchmark against your own AI agent.

## Overview

The benchmark executes a four-phase pipeline:

1. **Seed** — replay haystack conversation sessions into your agent's memory
2. **Settle** — wait for your agent to consolidate memories (default: 120 seconds)
3. **Probe** — ask recall questions in fresh sessions
4. **Judge** — score each response 0–3 using an LLM judge

---

## Prerequisites

```bash
pip install engram-benchmark
```

Set environment variables:

```bash
export JUDGE_API_KEY="sk-..."        # OpenAI-compatible key for scoring
```

The public Engram dataset can be fetched anonymously. `huggingface-cli login` or `HF_TOKEN` is optional if you want authenticated HuggingFace access for your environment.

---

## Option A: HTTP Server (recommended)

Expose two endpoints on your agent server. The benchmark POSTs JSON and expects JSON back.

### POST /seed

Receives conversation history to store in memory.

**Request:**
```json
{
  "task_id": "abc123",
  "sessions": [
    [
      {"role": "user", "content": "My dog's name is Biscuit."},
      {"role": "assistant", "content": "Got it, I'll remember that."}
    ]
  ]
}
```

**Response:**
```json
{"seeded": true, "session_count": 1}
```

### POST /probe

Receives a recall question. Return your agent's response.

**Request:**
```json
{
  "task_id": "abc123",
  "question": "What is my dog's name?"
}
```

**Response:**
```json
{"output": "Your dog's name is Biscuit."}
```

### Minimal Python server example

```python
#!/usr/bin/env python3
"""Minimal example agent server for Engram benchmark integration."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

memory: dict[str, list] = {}   # task_id -> list of sessions


class AgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(length))

        if self.path == "/seed":
            task_id = body["task_id"]
            sessions = body.get("sessions", [])
            memory[task_id] = sessions
            response = {"seeded": True, "session_count": len(sessions)}

        elif self.path == "/probe":
            task_id = body["task_id"]
            question = body["question"]
            # Replace this with your real agent call:
            response = {"output": f"[stub] I don't recall anything about: {question}"}

        else:
            self.send_response(404)
            self.end_headers()
            return

        data = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass  # suppress request logs


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8080), AgentHandler)
    print("Agent server listening on http://localhost:8080")
    server.serve_forever()
```

### Run the benchmark

```bash
# Start your agent server in one terminal
python my_agent_server.py

# Run the benchmark in another terminal
python -m benchmark.run \
  --agent http://localhost:8080 \
  --split test \
  --dry-run \
  --max-tasks 5
```

Remove `--dry-run` for a live scored run. The `--agent` flag accepts any `http://` or `https://` URL.

---

## Option B: Custom Python Adapter

Subclass `BaseAdapter` for tighter integration (e.g., in-process agents).

```python
from benchmark.adapters.base import BaseAdapter

class MyAgentAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "my_agent"

    def seed(self, task: dict) -> dict:
        sessions = task.get("metadata", {}).get("haystack_sessions", [])
        for session in sessions:
            for turn in session:
                self.agent.ingest(turn["role"], turn["content"])
        return {"seeded": True, "session_count": len(sessions)}

    def predict(self, task: dict) -> dict:
        answer = self.agent.ask(task["input"])
        return {"output": answer}
```

Then pass your adapter directly to `run_benchmark()`:

```python
from benchmark.run import run_benchmark
from benchmark.config import RunConfig

config = RunConfig(agent="my_agent", split="test", dry_run=True)
# Monkey-patch get_adapter for your adapter, or call run_benchmark internals directly.
```

---

## Option C: OpenClaw CLI Agent

Use this when running on an EC2 instance (or any server) with the OpenClaw CLI installed. This is the canonical setup for producing reference results.

### Prerequisites

- `openclaw` executable on `PATH` — verify with `openclaw --version`
- An OpenClaw agent ID (optional if you have a default agent)
- A separate OpenClaw agent or clean reset path for each benchmark condition you want to compare

### Reference condition lineup

For the OpenClaw reference track used in this repo, the main benchmark lineup is:

| Condition | Runtime setup | Upstream project | Benchmark-specific behavior |
|------|------|------|------|
| `baseline` | OpenClaw reference runtime with no additional benchmark-specific memory augmentation | [OpenClaw](https://github.com/openclaw/openclaw) | 10s default settle |
| `mem0` | OpenClaw with the Mem0-backed memory plugin enabled | [serenichron/openclaw-memory-mem0](https://github.com/serenichron/openclaw-memory-mem0) | 60s default settle |
| `clawvault` | OpenClaw with ClawVault installed and integrated | [Versatly/clawvault](https://github.com/Versatly/clawvault) | 10s default settle |
| `cortex` | OpenClaw with Cortex enabled | [Ubundi/openclaw-cortex](https://github.com/Ubundi/openclaw-cortex) | Preflight, seed-date injection, probe-date annotation, 180s default settle |

Engram does not install or switch these memory systems for you. The benchmark measures the runtime configuration that is already active in the target OpenClaw agent.

### Run command

```bash
JUDGE_API_KEY="sk-..." python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <your-agent-id> \
  --condition baseline \
  --output-dir outputs/baseline
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--agent-id ID` | _(none)_ | OpenClaw agent ID passed to `openclaw agent --agent` |
| `--openclaw-timeout N` | `120` | Timeout in seconds per `openclaw agent` call |
| `--condition NAME` | _(none)_ | Condition label (baseline/mem0/clawvault/cortex). Records the evaluated memory configuration and enables condition-specific benchmark behavior where implemented |
| `--flush-sessions` | off | Send `/new` after each seed session to trigger session-close memory hooks |
| `--judge-concurrency N` | `4` | Parallel judge workers |
| `--compare DIR_A DIR_B` | — | Compare two run directories offline (no agent needed) |

### What the adapter does

**Seed phase:** For each haystack session, the adapter sends every user turn to the OpenClaw agent via `openclaw agent --message <msg> --json --session-id <unique-id>`. Assistant turns are skipped — the agent generates its own responses. Each session gets a unique session ID so memory boundaries are preserved. With `--flush-sessions`, a `/new` command is sent after each session to trigger session-close memory hooks.

**Cortex condition:** When `--condition cortex` is set:
- **Preflight check** — runs `openclaw cortex status` and validates the reported health checks before the benchmark starts. Aborts with a clear error if Cortex is missing or unhealthy.
- **Seed date injection** — injects a narrative date context prefix into the first turn of each session, so temporal enrichment anchors `occurred_at` values correctly.
- **Probe date annotation** — prepends a `[cortex-date: YYYY-MM-DD]` marker to every probe, so the recall handler passes the correct `reference_date` for temporal ordering.
- **Settle default** — 180s instead of the usual 10s, to allow async Cortex ingest jobs (LLM extraction + embedding + graph build) to drain.

**Mem0 and ClawVault conditions:** When `--condition mem0` or `--condition clawvault` is set, the benchmark currently changes labeling and default settle timing only. Install and verify those memory systems in OpenClaw before running the benchmark.

**Probe phase:** The probe question is sent in a fresh session (new session ID) with no prior context. The adapter parses the JSON response using the same fallback chain as the V2 TypeScript runner: `result.payloads[].text` → `parsed.text` → `parsed.message` → `parsed.response` → raw stdout. Per-probe latency (in ms) is recorded in the output.

### EC2 setup walkthrough

```bash
# 1. Clone and install
git clone https://github.com/Ubundi/engram-benchmark.git
cd engram-benchmark
pip install -e ".[dev]"

# 2. Optional: authenticate with HuggingFace for your environment
# hf auth login

# 3. Smoke test (no OpenClaw needed)
python3 -m benchmark.run --agent local_stub --dry-run --max-tasks 3

# 4. Verify OpenClaw is available
openclaw --version

# 5. Live baseline run (inside tmux)
tmux new -s bench
JUDGE_API_KEY="sk-..." python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <baseline-id> \
  --condition baseline \
  --output-dir outputs/baseline

# 6. Reset agent memory between conditions
#    Or use separate OpenClaw agents/workspaces per condition

# 7. Memory-augmented run (cortex auto-settles for 180s)
JUDGE_API_KEY="sk-..." python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <cortex-id> \
  --condition cortex \
  --output-dir outputs/cortex

# 8. Optional: Mem0-backed run
JUDGE_API_KEY="sk-..." python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <mem0-id> \
  --condition mem0 \
  --output-dir outputs/mem0

# 9. Optional: ClawVault-backed run
JUDGE_API_KEY="sk-..." python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <clawvault-id> \
  --condition clawvault \
  --output-dir outputs/clawvault

# 10. Compare results offline
python3 -m benchmark.run \
  --agent local_stub \
  --compare outputs/baseline/<run-id> outputs/cortex/<run-id>
```

---

## Running Long Benchmarks with tmux

The full v3 split takes approximately 30 minutes (498 tasks, settle time depends on condition). Use tmux to keep the run alive across disconnections:

```bash
# Create a new session
tmux new -s benchmark

# Inside tmux: run the full benchmark
python -m benchmark.run \
  --agent http://localhost:8080 \
  --split v3 \
  --settle-seconds 120

# Detach with Ctrl-B D, reattach later with:
tmux attach -t benchmark
```

---

## Workflow: Dry Run First

Always verify your setup with a dry run before the full benchmark:

```bash
# Step 1: dry run against test split (2 tasks, no settle, no judge)
python -m benchmark.run --agent http://localhost:8080 --split test --dry-run

# Step 2: dry run with a small sample and judge enabled
JUDGE_API_KEY=sk-... python -m benchmark.run \
  --agent http://localhost:8080 \
  --split dev \
  --max-tasks 5 \
  --dry-run

# Step 3: full run
JUDGE_API_KEY=sk-... python -m benchmark.run \
  --agent http://localhost:8080 \
  --split v3
```

---

## Output Artifacts

Each run writes to `outputs/<run_id>/`:

| File | Contents |
|------|----------|
| `predictions.jsonl` | Raw agent outputs per task |
| `probes.jsonl` | Question + output pairs with latency |
| `seed_turns.jsonl` | Seed results per task with latency |
| `judgments.jsonl` | Per-task judge scores (0–3), pass scores, rationale |
| `metrics.json` | Aggregated metrics |
| `run_metadata.json` | Run config, answer model, git commit, and counts |
| `report.md` | Human-readable Markdown report with per-probe detail |

### Key metrics

| Metric | Description |
|--------|-------------|
| `qa.exact_match` | Fraction where output exactly matches reference answer |
| `qa.mean_score` | Mean judge score (0–3) across all judged tasks |
| `retrieval.hit_rate` | Fraction scoring ≥ 2 (grounded recall) |
| `abstain.rate` | Fraction of responses that abstained |
| `qa.category.<type>.mean_score` | Per question-type breakdown |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JUDGE_API_KEY` | _(empty)_ | API key for judge model; judging skipped if unset |
| `JUDGE_MODEL` | `gpt-4.1-mini` | Judge model name |
| `JUDGE_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL |
| `HF_TOKEN` | _(huggingface-cli)_ | HuggingFace token for dataset access |
| `OPENCLAW_TIMEOUT` | `120` | Timeout in seconds for `openclaw agent` CLI calls |

---

## Scoring Rubric

The LLM judge scores each response on a 0–3 scale:

| Score | Label | Meaning |
|-------|-------|---------|
| 3 | Grounded correct | Right answer, cites a specific detail from the haystack |
| 2 | Generic correct | Right direction, missing the specific detail |
| 1 | Abstained | Honest admission of not knowing |
| 0 | Hallucinated | Wrong specific detail stated confidently |

A score ≥ 2 counts as a retrieval hit.
