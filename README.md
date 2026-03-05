# Engram — Agent Long-Term Memory Benchmark

> **Finding:** Without memory augmentation, agents abstain on 64% of long-term recall probes and answer correctly on only 4%. With memory augmentation, correct recall reaches 48% and abstention drops to 12%.

🤗 [Dataset](https://huggingface.co/datasets/matthewschramm/engram-v3) &nbsp;·&nbsp; 📊 [Results](docs/FINDINGS.md) &nbsp;·&nbsp; 📋 [Benchmark Spec](docs/benchmark_spec.md) &nbsp;·&nbsp; 📄 [Evaluation Protocol](docs/evaluation_protocol.md) &nbsp;·&nbsp; 🔌 [Integration Guide](docs/integration_guide.md)

---

**Engram** is a runtime-first benchmark for evaluating long-term memory recall in AI agents. It tests whether agents can retrieve grounded, specific knowledge from prior sessions — not just recent in-context messages.

Unlike static QA benchmarks, Engram operates inside the agent runtime: it seeds real multi-turn conversation histories into the agent, waits for memory processing to settle, then probes recall in a fresh session with no in-context history. Whatever memory architecture the agent has is what gets measured.

---

## Task Categories

<p align="center">
  <img src="docs/assets/task-categories.png" alt="Engram task category examples" width="100%">
</p>

Engram v3 contains **504 tasks** spanning 9 question types, targeting the specific failure modes where compaction-based memory systems break down:

| Category | Count | What it tests |
|----------|------:|---------------|
| `multi-session` | 80 | Facts requiring information from multiple separate conversations |
| `temporal-reasoning` | 78 | Ordering and recency — distinguishing current from historical facts |
| `cross-agent-memory` | 72 | Knowledge shared or referenced across different agent instances |
| `multi-hop-reasoning` | 69 | Connecting facts via intermediate entities across the session corpus |
| `recurring-pattern` | 54 | Conventions and patterns established repeatedly across sessions |
| `knowledge-update` | 53 | Tracking how facts evolved — decisions reversed or revised over time |
| `single-session-user` | 45 | Direct recall of specifics stated by the user in a single session |
| `single-session-assistant` | 35 | Recall of specifics stated by the assistant in a single session |
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
| Tasks | 504 |
| Avg haystack sessions per task | 3.0 |
| Avg haystack turns per task | 30.1 |
| Question types | 9 |
| Format | JSON |
| HuggingFace | [matthewschramm/engram-v3](https://huggingface.co/datasets/matthewschramm/engram-v3) |

Authentication required: run `hf auth login` or set `HF_TOKEN`.

---

## Quickstart

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Authenticate

```bash
hf auth login        # or: export HF_TOKEN=<your-token>
```

### 3. Dry run (local stub, no agent required)

```bash
python3 -m benchmark.run --agent local_stub
```

### 4. Run against a live agent

Start your agent server, then point the benchmark at it:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run --agent http://localhost:8080
```

Engram seeds memory sessions into the agent, waits for memory processing to settle, probes recall in a fresh session, and judges responses with an LLM.

See [docs/integration_guide.md](docs/integration_guide.md) for the HTTP server contract, a minimal Python example, and a custom Python adapter option.

**Useful flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--settle-seconds N` | 120 | Wait between seed and probe phases |
| `--judge-passes N` | 3 | LLM judge passes per response (scores averaged) |
| `--skip-seed` | — | Skip seeding; probe a pre-seeded agent only |
| `--max-tasks N` | — | Run a subset of N tasks |
| `--judge-model` | `gpt-4.1-mini` | Judge model name |

---

## Evaluation Protocol

Engram uses a four-phase pipeline:

```
Seed  →  Settle  →  Probe  →  Judge
```

1. **Seed** — Replay haystack sessions into the agent turn-by-turn via the agent runtime
2. **Settle** — Wait for memory indexing and async processing to complete (default: 120s)
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
| `run_metadata.json` | Full run configuration and provenance |
| `seed_turns.jsonl` | Seeded conversation turns |
| `probes.jsonl` | Probe session transcripts |
| `judgments.jsonl` | Per-response judge scores and rationale |

---

## Repository Structure

```
engram/
├── benchmark/           CLI, adapters, task loader, evaluators, writers
│   ├── tasks/           Task loading, HuggingFace fetch, schema validation
│   ├── adapters/        Agent adapters: local_stub, http, openai, codex
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
  url     = {https://github.com/Ubundi/cortex-benchmark},
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

Engram is an open-source project by [Ubundi](https://ubundi.com) — a South African venture studio shaping human-centred AI. Based in Cape Town, Ubundi builds at the intersection of AI capability and African context, developing tools that ensure the benefits of AI reach their continent first.

Engram was built as part of the infrastructure behind [TooToo](https://ubundi.com), Ubundi's personal identity layer for language models — where robust long-term memory recall is foundational to delivering contextually relevant, grounded responses.

→ [ubundi.com](https://ubundi.com)
