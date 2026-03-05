# Benchmark Specification

## Objective

Measure memory-aware agent behavior in repeatable runtime conditions.

Primary focus:
- Can the agent recall grounded project details from prior sessions?
- Can the agent answer rationale and cross-session questions with reduced abstention?
- What quality profile is observed under baseline vs memory-augmented conditions?

## Benchmark protocol

Engram uses a single runtime-oriented protocol for evaluating agent memory:

- Input: canonical task objects (`id`, `input`, `reference_answer`) from the Engram v3 dataset.
- Phases: seed -> settle -> probe -> judge -> report.
- Output: phase-level artifacts plus summary metrics.

## Canonical task model

Canonical internal fields:
- `id` (string)
- `input` (string)
- `reference_answer` (string)
- `metadata` (object, optional)

## Runtime lifecycle

1. **Load**: parse Engram v3 records and extract seed sessions from haystack context.
2. **Seed**: replay user turns into the target agent runtime.
3. **Settle**: wait for memory indexing/processing window.
4. **Probe**: ask evaluation prompts in a fresh probe session.
5. **Judge**: score responses using a 0-3 rubric via OpenAI-compatible API.
6. **Report**: write JSONL/JSON artifacts under `outputs/<run_id>/`.

## Non-goals (current release)

- Public leaderboard automation.
- Built-in comparison report generation across conditions.
- Full production adapter implementations for `codex` and `openai`.
