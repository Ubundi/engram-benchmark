# Benchmark Specification

## Objective

Measure memory-aware agent behavior in repeatable runtime conditions.

Primary focus:
- Can the agent recall grounded project details from prior sessions?
- Can the agent answer rationale and cross-session questions with reduced abstention?
- What quality profile is observed under baseline vs memory-augmented conditions?

## Benchmark protocols

### Standard protocol (`--protocol standard`)

A lightweight scaffold protocol for task loading, adapter prediction, and placeholder
evaluation.

- Input: canonical task objects (`id`, `input`, `reference_answer`).
- Adapters: `local_stub` (deterministic), `codex` (stub), `openai` (stub).
- Output: predictions and placeholder metrics.

### V2 protocol (`--protocol v2`)

Runtime-oriented protocol for OpenClaw memory evaluation.

- Conditions: `baseline` and `cortex`.
- Input: legacy V2 question dataset (`openclaw-memory-benchmark-v2.json`).
- Phases: seed -> settle -> probe -> judge -> report.
- Output: phase-level artifacts plus summary metrics.

## Canonical task model

Canonical internal fields:
- `id` (string)
- `input` (string)
- `reference_answer` (string)
- `metadata` (object, optional)

Legacy V2 records are normalized into this model while preserving source metadata.

## V2 runtime lifecycle

1. **Load**: parse legacy V2 records and extract seed sessions from haystack context.
2. **Seed**: replay user turns into the target agent runtime.
3. **Settle**: wait for memory indexing/processing window.
4. **Probe**: ask evaluation prompts in a fresh probe session.
5. **Judge**: score responses using a 0-3 rubric via OpenAI-compatible API.
6. **Report**: write JSONL/JSON artifacts under `outputs/<run_id>/`.

## Condition definitions

- **baseline**: reference condition without Cortex plugin behavior.
- **cortex**: memory-augmented condition. Preflight checks for
  `cortex_search_memory` and `cortex_save_memory` availability.

## Non-goals (current release)

- Public leaderboard automation.
- Built-in baseline vs cortex comparison report generation.
- Full production adapter implementations for `codex` and `openai` in standard mode.
