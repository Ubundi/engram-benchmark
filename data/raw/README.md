---
license: mit
task_categories:
  - question-answering
language:
  - en
tags:
  - agent-memory
  - memory-benchmark
  - long-term-memory
  - multi-session
  - temporal-reasoning
  - benchmark
size_categories:
  - n<1K
---

# Engram v3 — Agent Long-Term Memory Benchmark

**Engram** is a benchmark dataset for evaluating long-term memory recall in AI agents. It tests whether agents can retrieve grounded, specific knowledge from prior sessions — not just recent in-context messages.

Unlike static QA benchmarks, Engram operates inside the agent runtime: it seeds real multi-turn conversation histories into the agent, waits for memory processing to settle, then probes recall in a fresh session with no in-context history. Whatever memory architecture the agent has is what gets measured.

> **Key finding:** Without memory augmentation, agents abstain on 64% of recall probes and answer correctly on only 4%. With memory augmentation, correct recall reaches 48% and abstention drops to 12%.

## Dataset Summary

| Property | Value |
|----------|-------|
| Tasks | 504 |
| Avg haystack sessions per task | 3.0 |
| Avg haystack turns per task | 30.1 |
| Question types | 9 |
| Language | English |
| Format | JSON |
| License | MIT |

## Task Categories

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

## Schema

Each record contains:

```json
{
  "question_id": "oc_temporal_001",
  "question_type": "temporal-reasoning",
  "question": "...",
  "answer": "...",
  "question_date": "2026/03/19 (Thu) 15:00",
  "haystack_dates": ["2026-02-19", "..."],
  "haystack_session_ids": ["s001", "..."],
  "haystack_sessions": [
    [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  ],
  "answer_session_ids": ["s042"],
  "metadata": { "difficulty": "medium", "memory_type": "temporal_ordering" }
}
```

## Evaluation Protocol

Engram uses a four-phase pipeline:

```
Seed  →  Settle  →  Probe  →  Judge
```

1. **Seed** — Replay `haystack_sessions` into the agent turn-by-turn
2. **Settle** — Wait for memory indexing to complete (default: 120s)
3. **Probe** — Ask `question` in a fresh session with no haystack in context
4. **Judge** — Score the response 0–3 against `answer` using an LLM judge

**Scoring rubric:**

| Score | Label | Description |
|------:|-------|-------------|
| 3 | Grounded correct | Cites the specific detail from the haystack |
| 2 | Generic correct | Right direction, missing the specific |
| 1 | Abstained | "I don't have that context" |
| 0 | Hallucinated | Wrong specific stated with confidence |

## Dataset Files

| File | Split | Tasks | Purpose |
|------|-------|------:|---------|
| `engram-v3.json` | `v3` (default) | 504 | Full benchmark — use for final evaluation |
| `engram-v3-test.json` | `test` | 50 | Lightweight test split — use for development and quick runs |

Both files are hosted on HuggingFace at [matthewschramm/engram-v3](https://huggingface.co/datasets/matthewschramm/engram-v3) and fetched automatically at runtime. They are not committed to the repository.

## Fetching the Dataset

Requires HF authentication — either run `huggingface-cli login` or set the `HF_TOKEN` environment variable.

**Via Makefile:**
```bash
make fetch        # full dataset (engram-v3.json)
make fetch-test   # test split  (engram-v3-test.json)
```

**Via Python:**
```python
from benchmark.tasks.hf import fetch_engram_dataset, fetch_engram_test_dataset

path = fetch_engram_dataset()       # → ~/.cache/huggingface/...
path = fetch_engram_test_dataset()  # → ~/.cache/huggingface/...
```

**Via benchmark runner:**
```bash
# Full dataset (default)
python3 -m benchmark.run --agent <id>

# Test split
python3 -m benchmark.run --agent <id> --split test
```

## Benchmark Harness

The full evaluation harness — including HuggingFace fetching, OpenClaw adapter, LLM judge, and artifact writers — is available at [Ubundi/cortex-benchmark](https://github.com/Ubundi/cortex-benchmark).

```bash
pip install -e ".[dev]"
JUDGE_API_KEY="<key>" python3 -m benchmark.run --agent <openclaw-agent-id>
```

## Citation

```bibtex
@software{engram2026,
  title   = {Engram: A Runtime Benchmark for Agent Long-Term Memory Recall},
  author  = {Ubundi},
  year    = {2026},
  url     = {https://github.com/Ubundi/cortex-benchmark},
}
```

## License

MIT
