# Architecture

This document explains how Engram is designed, why it works the way it does, and how to extend it.

---

## System Overview

```
                    ┌──────────────────────────────────────────────┐
                    │              CLI / RunConfig                  │
                    └──────────────────┬───────────────────────────┘
                                       │
                    ┌──────────────────▼───────────────────────────┐
                    │              Task Loader                      │
                    │   local JSONL  ←→  HuggingFace fetch         │
                    └──────────────────┬───────────────────────────┘
                                       │
          ┌────────────────────────────▼────────────────────────────┐
          │                    run_benchmark()                       │
          │                                                         │
          │  Phase 1: SEED ──── adapter.seed(task) ──→ seed_turns   │
          │                                                         │
          │  Phase 2: SETTLE ── time.sleep(N) ──────→ (wait)        │
          │                                                         │
          │  Phase 3: PROBE ─── adapter.predict(task) → predictions │
          │                                                         │
          │  Phase 4: JUDGE ─── judge_all() ────────→ judgments      │
          │                                                         │
          │  Phase 5: EVALUATE ─ qa + retrieval + abstain → metrics │
          └────────────────────────────┬────────────────────────────┘
                                       │
                    ┌──────────────────▼───────────────────────────┐
                    │            Output Writer                      │
                    │  metrics.json  predictions.jsonl  judgments…  │
                    └──────────────────────────────────────────────┘
```

---

## Why Four Phases?

Most benchmarks treat assessment as a single pass: give the model a prompt, check the answer. Memory benchmarks can't do that. The agent needs time to process seeded context — compaction, indexing, embedding — before being probed. Engram's four phases exist because each maps to a distinct real-world constraint:

| Phase | What happens | Why it's separate |
|-------|-------------|-------------------|
| **Seed** | Replay haystack sessions into the agent turn-by-turn | The agent must receive context through its normal interface, not injected into a prompt |
| **Settle** | Wait for memory processing (default: 120s) | Compaction, re-ranking, and embedding pipelines are async — probing immediately would measure latency, not recall |
| **Probe** | Ask questions in a fresh session with no haystack in context | Isolates long-term memory from in-context recall — the whole point of the benchmark |
| **Judge** | Score responses 0–3 using an LLM judge | Memory recall is nuanced — binary pass/fail misses the difference between "right but vague" and "right with the specific detail" |

Skipping any phase changes what you're measuring. `--skip-seed` probes an already-seeded agent. `--dry-run` skips the judge entirely (useful for adapter testing). `--settle-seconds 0` tests immediate recall.

---

## Why 0–3 Scoring?

Binary scoring (correct/incorrect) doesn't capture the failure modes that matter for memory systems. An agent that says "I think there was a meeting about that" vs. one that says "The March 4th standup decided to switch from Redis to PostgreSQL for the cache layer" are both partially correct, but the second is operationally useful.

| Score | Label | What it means | Why it matters |
|------:|-------|---------------|----------------|
| 3 | Grounded correct | Cites the specific detail from the haystack | The agent's memory is working — it retrieved and grounded its answer |
| 2 | Generic correct | Right direction, missing the specific | Retrieval found relevant context but compaction lost the detail |
| 1 | Abstained | "I don't have that context" | Honest uncertainty — better than hallucination, signals retrieval miss |
| 0 | Hallucinated | Wrong specific stated with confidence | The worst outcome — the agent fabricated a plausible but false detail |

This scale makes the metrics actionable:
- **Mean score** tracks overall quality
- **Hit rate** (score >= 2) measures retrieval effectiveness
- **Abstention rate** (score == 1) measures calibration
- Score 0 vs. 1 separates dangerous failures from safe ones

---

## Why Multi-Pass Judging?

LLM judges are noisy. A single judge call can return 2 or 3 for the same response depending on sampling. Multi-pass judging (default: 3 passes) averages across calls to reduce variance.

The temperature is auto-selected:
- **Single pass** (`--judge-passes 1`): temperature 0.0 (deterministic, no variance to average)
- **Multi-pass** (default 3): temperature 0.3 (mild variation, enables consensus)

This is configurable via `--judge-temperature` for experiments where you want to measure judge consistency itself.

Judge calls run concurrently (`--judge-concurrency 4` by default) via thread pool. Individual pass failures are tolerated — if 2 of 3 passes succeed, the score is the average of those 2.

---

## Component Map

### Task Loader (`benchmark/tasks/`)

```
loader.py
  load_tasks(split, data_path, max_tasks)
    ├── canonicalize split aliases (v3 = engram-v3 = engram-v3.json)
    ├── resolve source: local JSONL → HuggingFace fallback
    ├── parse: .jsonl (direct) or .json (OpenClaw normalization)
    ├── validate: required fields (id, input, reference_answer)
    └── return validated task list

openclaw.py
  normalize_openclaw_task(raw_record)
    ├── map: question_id → id, question → input, answer → reference_answer
    ├── preserve: haystack_sessions, dates, session_ids in metadata
    ├── generate: context_snippets (first 2 turns from first 3 sessions)
    └── return canonical task dict

hf.py
  fetch_engram_dataset() / fetch_engram_test_dataset()
    └── huggingface_hub.hf_hub_download() → cached local path
```

The loader checks for local files first (`data/splits/v3.jsonl`) before hitting HuggingFace. This lets CI run without network access using checked-in sample splits.

### Adapter Layer (`benchmark/adapters/`)

All adapters implement `BaseAdapter` with two methods:

```python
class BaseAdapter(ABC):
    @property
    def name(self) -> str: ...       # stable identifier for logs/reports

    def seed(self, task) -> dict: ... # Phase 1: load context (optional, default no-op)
    def predict(self, task) -> dict:  # Phase 3: query agent (required)
```

| Adapter | `name` | Seed behavior | Predict behavior |
|---------|--------|---------------|------------------|
| `LocalStubAdapter` | `local_stub` | Reports session count | Returns reference answer or deterministic hash |
| `HttpAdapter` | `http:{url}` | POSTs sessions to `/seed` | POSTs question to `/probe` |
| `OpenClawCLIAdapter` | `openclaw:{id}` | Replays turns via `openclaw agent` CLI | Single-turn probe in fresh session |
| `CodexAdapter` | `codex` | Not implemented | Not implemented |
| `OpenAIAdapter` | `openai` | Not implemented | Not implemented |

The adapter registry (`get_adapter()`) routes by name: URLs starting with `http://` or `https://` automatically use `HttpAdapter`. Everything else is looked up by string.

**Extension point:** Add a new adapter by subclassing `BaseAdapter` and registering it in `__init__.py`.

### Judge (`benchmark/judge.py`)

```
judge_all(tasks, predictions, config)
  ├── skip if dry_run (generates random scores for testing)
  ├── for each task+prediction pair:
  │     judge_response(question, reference, response, config)
  │       ├── call _call_judge() N times (judge_passes)
  │       ├── each call: POST to OpenAI-compatible /chat/completions
  │       ├── parse JSON response: {"score": int, "rationale": str}
  │       ├── tolerate individual pass failures
  │       └── return averaged score + first rationale
  └── return judgment list (score, scores[], rationale, pass_count)
```

The judge uses any OpenAI-compatible API (`--judge-base-url`). Default model is `gpt-4.1-mini` — fast and cheap for scoring. Switch to `gpt-4.1` or `o3-mini` for higher-stakes runs.

### Evaluators (`benchmark/evaluators/`)

Three independent evaluators, each producing a metric namespace:

| Evaluator | Metrics | Logic |
|-----------|---------|-------|
| `evaluate_qa()` | `qa.mean_score`, `qa.exact_match`, `qa.judged_count`, `qa.error_count`, `qa.category.{type}.mean_score` | Exact string match + judge score averaging, per-category breakdown by `question_type` |
| `evaluate_retrieval()` | `retrieval.hit_rate`, `retrieval.judged_count` | Score >= 2.0 counts as a hit (agent found relevant context) |
| `evaluate_abstain()` | `abstain.rate` | Keyword detection (26 phrases like "don't have", "no information") OR judge score rounds to 1 |

Evaluators are stateless functions. They take tasks, predictions, and judgments as input and return a flat metrics dict. Add new evaluators by writing a function and calling it in `run_benchmark()`.

### Output Writer (`benchmark/reports/writer.py`)

Writes all artifacts to `{output_dir}/{run_id}/`:

| File | When written | Content |
|------|-------------|---------|
| `predictions.jsonl` | Always | Agent responses with task_id linkage |
| `metrics.json` | Always | Aggregate scores |
| `run_metadata.json` | Always | Full config, answer model, counts, timestamp |
| `seed_turns.jsonl` | If seeding ran | Per-task seed results |
| `probes.jsonl` | If probing ran | Question-answer pairs |
| `judgments.jsonl` | If judging ran | Per-task scores with rationale |

All JSON is written with sorted keys for deterministic diffs.

---

## Error Handling Philosophy

Engram favors **graceful degradation** over hard failure:

- **Adapter errors during seed:** Logged, task still probed (seed result records the failure)
- **Judge pass failures:** If 2 of 3 passes succeed, the score is the average of those 2
- **All judge passes fail:** Score is `null` with error message — counted in `qa.error_count`
- **Missing predictions:** Judge skips the task, records `"error": "no prediction"`
- **No judge API key:** Phase 4 is skipped entirely — you get predictions but no scores

This means a benchmark run always produces *something*, even if parts fail. The `run_metadata.json` counts tell you exactly how complete the run was.

---

## Configuration Precedence

Settings are merged in this order (last wins):

1. `RunConfig` defaults (code)
2. JSON config file (`--config path.json`)
3. CLI arguments

This allows sharing a base config across team members while overriding specific flags per run.

---

## Adding a New Adapter

```python
# benchmark/adapters/my_agent.py
from benchmark.adapters.base import BaseAdapter

class MyAgentAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "my_agent"

    def seed(self, task):
        sessions = task.get("metadata", {}).get("haystack_sessions", [])
        # ... send sessions to your agent ...
        return {"seeded": True, "session_count": len(sessions)}

    def predict(self, task):
        question = task["input"]
        # ... query your agent ...
        return {"output": response_text, "metadata": {"latency_ms": 42}}
```

Register in `benchmark/adapters/__init__.py`:
```python
if normalized == "my_agent":
    return MyAgentAdapter()
```

Run: `python -m benchmark.run --agent my_agent`

---

## Adding a New Evaluator

```python
# benchmark/evaluators/my_metric.py
def evaluate_my_metric(tasks, predictions, judgments=None):
    # ... compute your metric ...
    return {"my_metric.score": value, "my_metric.count": n}
```

Add to `benchmark/run.py` in `run_benchmark()`:
```python
from benchmark.evaluators.my_metric import evaluate_my_metric
metrics.update(evaluate_my_metric(tasks, predictions, judgments))
```

The metric keys will appear in `metrics.json` automatically.
