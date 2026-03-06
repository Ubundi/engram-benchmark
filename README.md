<p align="center">
  <img src="docs/assets/Engram Banner.png" alt="Engram — Measuring what AI agents remember" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="https://github.com/Ubundi/engram-benchmark/actions/workflows/ci.yml"><img src="https://github.com/Ubundi/engram-benchmark/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://huggingface.co/datasets/matthewschramm/engram-v3"><img src="https://img.shields.io/badge/%F0%9F%A4%97-Dataset-yellow.svg" alt="Dataset on HF"></a>
</p>

> **Finding:** Without memory augmentation, agents abstain on 64% of long-term recall probes and answer correctly on only 4%. With memory augmentation, correct recall reaches 48% and abstention drops to 12%.

[Dataset](https://huggingface.co/datasets/matthewschramm/engram-v3) &nbsp;·&nbsp; [Results](docs/FINDINGS.md) &nbsp;·&nbsp; [Benchmark Spec](docs/benchmark_spec.md) &nbsp;·&nbsp; [Evaluation Protocol](docs/evaluation_protocol.md) &nbsp;·&nbsp; [Integration Guide](docs/integration_guide.md)

---

**Engram** is a runtime-first benchmark for evaluating long-term memory recall in AI agents. It tests whether agents can retrieve grounded, specific knowledge from prior sessions — not just recent in-context messages.

Unlike static QA benchmarks, Engram operates inside the agent runtime: it seeds real multi-turn conversation histories into the agent, waits for memory processing to settle, then probes recall in a fresh session with no in-context history. Whatever memory architecture the agent has is what gets measured.

---

## Task Categories

<p align="center">
  <img src="docs/assets/task-categories.png" alt="Engram task category examples" width="100%">
</p>

Engram v3 contains **498 tasks** spanning 9 question types, targeting the specific failure modes where compaction-based memory systems break down:

| Category | Count | What it tests |
|----------|------:|---------------|
| `multi-session` | 79 | Facts requiring information from multiple separate conversations |
| `temporal-reasoning` | 78 | Ordering and recency — distinguishing current from historical facts |
| `cross-agent-memory` | 71 | Knowledge shared or referenced across different agent instances |
| `multi-hop-reasoning` | 68 | Connecting facts via intermediate entities across the session corpus |
| `recurring-pattern` | 54 | Conventions and patterns established repeatedly across sessions |
| `knowledge-update` | 53 | Tracking how facts evolved — decisions reversed or revised over time |
| `single-session-user` | 45 | Direct recall of specifics stated by the user in a single session |
| `single-session-assistant` | 32 | Recall of specifics stated by the assistant in a single session |
| `fact-recall` | 18 | Direct retrieval of a single grounded specific fact |

---

## Dataset

The Engram v3 dataset is hosted on HuggingFace and fetched automatically on first run.

```python
from benchmark.tasks.hf import fetch_engram_dataset
path = fetch_engram_dataset()  # downloads and caches locally
```

| Property | Value |
|----------|-------|
| Tasks | 498 |
| Avg haystack sessions per task | 3.0 |
| Avg haystack turns per task | 30.1 |
| Question types | 9 |
| Format | JSON |
| HuggingFace | [matthewschramm/engram-v3](https://huggingface.co/datasets/matthewschramm/engram-v3) |

The dataset is public — no authentication required.

---

## Quickstart

### 1. Install

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv if not already installed
source $HOME/.local/bin/env                        # add uv to PATH
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Dry run (local stub, no agent required)

```bash
python3 -m benchmark.run --agent local_stub
```

### 3. Run against a live agent

Start your agent server, then point the benchmark at it:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run --agent http://localhost:8080
```

Engram seeds memory sessions into the agent, waits for memory processing to settle, probes recall in a fresh session, and judges responses with an LLM.

See [docs/integration_guide.md](docs/integration_guide.md) for the HTTP server contract, the OpenClaw CLI adapter, and a custom Python adapter option.

### 4. Run on EC2 with OpenClaw

Clone the repo on an EC2 instance where OpenClaw is already installed:

```bash
git clone https://github.com/Ubundi/engram-benchmark.git && cd engram-benchmark
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

Dry-run first to confirm the setup:

```bash
python3 -m benchmark.run --agent local_stub --dry-run --max-tasks 3
```

Live run against the local OpenClaw agent:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <your-agent-id> \
  --condition baseline \
  --output-dir outputs/baseline
```

To compare conditions, run again with a different `--condition` and `--output-dir`:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <your-agent-id> \
  --condition cortex \
  --output-dir outputs/cortex
```

After both runs, compare results offline:

```bash
python3 -m benchmark.run \
  --agent local_stub \
  --compare outputs/baseline/<run-id> outputs/cortex/<run-id>
```

Use `tmux` for long-running sessions — see [docs/integration_guide.md](docs/integration_guide.md) for details.

**Useful flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--condition NAME` | — | Condition (baseline/cortex/clawvault). Sets settle defaults and enables cortex features |
| `--agent-id ID` | — | OpenClaw agent ID (passed to `openclaw agent --agent`) |
| `--settle-seconds N` | auto | Wait between seed and probe (cortex=180s, baseline/clawvault=10s, other=120s) |
| `--judge-passes N` | 3 | LLM judge passes per response (scores averaged) |
| `--judge-concurrency N` | 4 | Parallel judge workers |
| `--flush-sessions` | — | Send `/new` after each seed session to trigger memory hooks |
| `--skip-seed` | — | Skip seeding; probe a pre-seeded agent only |
| `--max-tasks N` | — | Run a subset of N tasks |
| `--judge-model` | `gpt-4.1-mini` | Judge model name |
| `--openclaw-timeout N` | 120 | Timeout in seconds for `openclaw agent` CLI calls |
| `--compare DIR_A DIR_B` | — | Compare two run directories offline (no agent needed) |

---

## Evaluation Protocol

Engram uses a four-phase pipeline:

```
Seed  →  Settle  →  Probe  →  Judge
```

1. **Seed** — Replay haystack sessions into the agent turn-by-turn via the agent runtime
2. **Settle** — Wait for memory indexing and async processing to complete (cortex: 180s, baseline: 10s)
3. **Probe** — Ask evaluation questions in a fresh session with no haystack in context
4. **Judge** — Score responses 0–3 against ground truth using a multi-pass LLM judge

**Scoring rubric:**

| Score | Label | Description |
|------:|-------|-------------|
| 3 | Grounded correct | Cites the specific detail from the haystack |
| 2 | Generic correct | Right direction, missing the specific |
| 1 | Abstained | Honest "I don't have that context" |
| 0 | Hallucinated | Wrong specific stated with confidence |

See [docs/evaluation_protocol.md](docs/evaluation_protocol.md) for full protocol specification.

---

## Results

Reference run results on a live OpenClaw agent (Mar 4, 2026). Scores are on a 0–3 scale.

| Condition | Overall | Rationale | Synthesis | Evolution | Temporal | Grounded | Abstained |
|-----------|--------:|----------:|----------:|----------:|---------:|---------:|----------:|
| Baseline (native memory only) | 1.10 | 1.93 | 0.54 | 1.07 | 0.62 | 4% | 64% |
| Memory-augmented | **1.95** | **3.00** | **2.00** | **2.10** | 0.67 | **48%** | **12%** |
| Δ | **+0.85** | **+1.07** | **+1.46** | **+1.03** | +0.05 | +44pp | −52pp |

Key findings:

- **Rationale recall reaches 3.00** — the reasoning behind decisions is fully preserved with memory augmentation
- **Synthesis** (facts spanning multiple sessions) improves from near-impossible (0.54) to reliable (2.00)
- **Temporal reasoning** (+0.05) is the hardest category — semantic retrieval surfaces historical and current facts without reliable recency ranking
- Memory value **compounds across runs**: a second seeding pass raised overall score from 1.81 to 1.95

Full analysis and per-category breakdowns: [docs/FINDINGS.md](docs/FINDINGS.md)

---

## Outputs

Each run produces `outputs/<run_id>/` containing:

| File | Contents |
|------|----------|
| `predictions.jsonl` | Per-task agent responses |
| `metrics.json` | Aggregate and per-category scores |
| `run_metadata.json` | Full run configuration, git commit, provenance |
| `seed_turns.jsonl` | Seeded conversation turns with latency |
| `probes.jsonl` | Probe session transcripts with latency |
| `judgments.jsonl` | Per-response judge scores, rationale, and pass scores |
| `report.md` | Human-readable Markdown report with full per-probe detail |

---

## Repository Structure

```
engram/
├── benchmark/           CLI, adapters, task loader, evaluators, writers
│   ├── tasks/           Task loading, HuggingFace fetch, schema validation
│   ├── adapters/        Agent adapters: local_stub, http, openclaw, openai, codex
│   ├── evaluators/      QA, retrieval, and abstention evaluators
│   └── judge.py         Multi-pass LLM judge (0–3 scoring)
├── data/
│   └── splits/          CI sample splits (*.sample.jsonl)
├── docs/                Benchmark spec, evaluation protocol, findings, integration guide
├── leaderboard/         Submission format and leaderboard policy
├── outputs/             Run artifacts (gitignored)
├── scripts/             Dataset generation pipeline
└── tests/               Import, CLI, and schema tests
```

---

## Citation

```bibtex
@software{engram2026,
  title   = {Engram: A Runtime Benchmark for Agent Long-Term Memory Recall},
  author  = {Ubundi},
  year    = {2026},
  url     = {https://github.com/Ubundi/engram-benchmark},
}
```

---

## License

MIT

---

## Built by Ubundi

<a href="https://ubundi.com">
  <img src="docs/assets/ubundi_logo.jpeg" alt="Ubundi" height="36">
</a>

Engram is an open-source project by [Ubundi](https://ubundi.com) — a South African venture studio shaping human-centred AI. Based in Cape Town, Ubundi builds at the intersection of AI capability and African context.

Engram grew out of a need to rigorously measure what memory systems actually retain. Existing benchmarks test in-context recall; Engram tests what survives after the context window is gone. The result: a reproducible, runtime-first evaluation that exposes the gap between "the agent saw it" and "the agent remembers it."

> [ubundi.com](https://ubundi.com)
