# Benchmark Specification

## Objective

Measure long-term memory behavior in AI agents under repeatable runtime conditions.

Primary focus:
- Can the agent recall grounded project details from prior sessions?
- Can the agent preserve rationale, evolution, and cross-session synthesis rather than only isolated facts?
- How does a system trade off grounded recall, abstention, and hallucination under a fixed protocol?
- Can different agent architectures be compared fairly under the same runtime conditions?

## Benchmark protocol

Engram uses a single runtime-oriented protocol for evaluating agent memory:

- Input: canonical task objects (`id`, `input`, `reference_answer`) from the Engram v3 dataset.
- Phases: seed -> settle -> probe -> judge -> report.
- Output: phase-level artifacts plus summary metrics.

The benchmark is system-neutral: any agent that can be driven through a supported adapter can be evaluated under the same task and scoring procedure.

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

- Claiming to exhaustively cover every memory failure mode in deployed agents.
- Public leaderboard automation.
- Built-in comparison report generation across conditions.
- Full production adapter implementations for `codex` and `openai`.
