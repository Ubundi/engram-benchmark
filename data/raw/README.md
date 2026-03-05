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
size_categories:
  - n<1K
---

# Engram v3

**Engram** is a benchmark dataset for evaluating long-term memory recall in AI agents. It tests whether an agent can retrieve grounded, specific knowledge from prior sessions — not just recent in-context messages.

## Dataset summary

- **504 tasks** across 9 question types
- Multi-turn conversation haystack (synthetic project history spanning weeks)
- Designed to stress-test compaction-based memory systems
- Each task includes the full haystack sessions needed to seed an agent before probing

## Question types

| Type | Count | What it tests |
|------|-------|---------------|
| `temporal-reasoning` | 78 | Ordering and recency of decisions |
| `multi-session` | 80 | Facts that span multiple conversations |
| `knowledge-update` | 53 | Tracking how facts changed over time |
| `cross-agent-memory` | 72 | Knowledge shared across different agents |
| `multi-hop-reasoning` | 69 | Connecting facts across entities |
| `recurring-pattern` | 54 | Patterns that appear repeatedly |
| `single-session-user` | 45 | Facts from a single user turn |
| `single-session-assistant` | 35 | Facts from a single assistant turn |
| `fact-recall` | 18 | Direct specific fact retrieval |

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
  "haystack_sessions": [ ... ],
  "answer_session_ids": ["s042"],
  "metadata": { ... }
}
```

## Evaluation protocol

The benchmark uses a seed → settle → probe → judge pipeline:

1. **Seed** — replay haystack sessions into the agent
2. **Settle** — wait for memory indexing
3. **Probe** — ask questions in a fresh session (no haystack in context)
4. **Judge** — score responses 0–3 against ground truth using an LLM judge

Scoring rubric:
- `3` — grounded correct (cites the specific detail)
- `2` — generic correct (right direction, missing specifics)
- `1` — abstained ("I don't have that context")
- `0` — hallucinated (wrong specific claim stated confidently)

## Benchmark harness

The full evaluation harness is available at [Ubundi/cortex-benchmark](https://github.com/Ubundi/cortex-benchmark).

## License

MIT
