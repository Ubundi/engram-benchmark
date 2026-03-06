# Candidate System Matrix

This document defines a practical evaluation lineup for Engram's main results table.

## Goal

Show that Engram compares memory behavior across multiple systems or conditions, not only `baseline` versus `cortex`.

## Minimum Publishable Matrix

The smallest paper-credible matrix is five evaluated rows:

| Row | Runtime family | System or condition | Memory configuration | Adapter path | Why it belongs in the main table | Status target |
|---|---|---|---|---|---|---|
| A | OpenClaw CLI | `baseline` | Native agent behavior with no benchmark-specific memory augmentation | `--agent openclaw --condition baseline` | Reference point for all OpenClaw-based comparisons | Must run |
| B | OpenClaw CLI | `clawvault` | OpenClaw with its alternate memory condition | `--agent openclaw --condition clawvault` | Adds a second memory condition in the same runtime family | Must run if the condition is available in the target environment |
| C | OpenClaw CLI | `cortex` | OpenClaw with Cortex memory enabled | `--agent openclaw --condition cortex` | Current headline augmented condition; needed for continuity with prior results | Must run |
| D | HTTP adapter | External agent, memory off or minimal memory | `--agent http://...` | Proves the benchmark can evaluate a non-OpenClaw runtime and provides a cross-runtime low-memory point | Must run |
| E | HTTP adapter | External agent, memory on | `--agent http://...` | Adds a second non-OpenClaw row showing that Engram measures memory-system differences outside the OpenClaw family | Must run |

If five rows are not feasible, four is the minimum fallback:

- `baseline`
- `cortex`
- one external HTTP runtime without memory augmentation
- one external HTTP runtime with memory augmentation

That fallback is weaker than the five-row matrix because it drops the third OpenClaw condition and leaves less within-family contrast.

## Preferred Expansion

If engineering bandwidth allows, expand from five rows to six or seven:

| Priority | Add-on row | Why it helps |
|---|---|---|
| High | Second external runtime family | Reduces the risk that Engram looks tied to one agent stack plus one guest implementation |
| High | Same external runtime with a different retrieval strategy | Separates "better agent" from "better memory architecture" |
| Medium | Strong long-context but weak memory baseline | Shows the difference between long-context handling and post-context-window memory |
| Medium | Smaller or cheaper memory-enabled system | Helps show whether gains depend on model scale or on memory design |

## Concrete Row Definitions

Use these definitions when assembling the main results table.

### Row A: OpenClaw baseline

- Use the frozen official setting.
- Separate agent identity from every other condition.
- Treat this as the canonical no-augmentation reference row.

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <baseline-agent-id> \
  --condition baseline \
  --split v3 \
  --output-dir outputs/baseline
```

### Row B: OpenClaw clawvault

- Use only if the target environment actually exposes the `clawvault` condition.
- Keep all benchmark settings identical to Row A except for agent identity and condition.
- If `clawvault` is unavailable or unstable, drop it and replace it with a second external runtime row.

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <clawvault-agent-id> \
  --condition clawvault \
  --split v3 \
  --output-dir outputs/clawvault
```

### Row C: OpenClaw cortex

- Use the same OpenClaw versioning discipline as Rows A and B.
- Keep the official `cortex` settle default unless there is a disclosed reason to override it.
- This row is useful only if Cortex is healthy and preflight passes.

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <cortex-agent-id> \
  --condition cortex \
  --split v3 \
  --output-dir outputs/cortex
```

### Row D: External runtime without memory augmentation

- Run through the HTTP adapter or a custom in-process adapter.
- Disable retrieval, episodic memory, vector memory, or memory plugins as cleanly as the target runtime allows.
- This row should answer the question: what happens when the non-OpenClaw agent mostly relies on immediate model behavior rather than persistent memory?

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent http://localhost:8080 \
  --split v3 \
  --output-dir outputs/http-no-memory
```

### Row E: External runtime with memory augmentation

- Use the same runtime family as Row D whenever possible.
- Change only the memory system or retrieval layer, not the entire application stack.
- This row is where Engram becomes visibly system-neutral: the benchmark can compare memory deltas in another runtime family, not just OpenClaw.

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent http://localhost:8080 \
  --split v3 \
  --output-dir outputs/http-memory
```

## Recommended Pairing Strategy

When possible, choose systems that let the paper isolate both of these effects:

- within-family memory effect:
  `baseline` vs `clawvault` vs `cortex`
- cross-family benchmark portability:
  external runtime without memory vs the same external runtime with memory

That pairing is stronger than comparing five unrelated systems because it lets the paper say both:

- Engram detects meaningful memory differences inside one runtime family.
- Engram also transfers to other runtime families.

## What Counts As A Distinct Row

Count a row as distinct only if at least one of these changes:

- runtime family
- memory architecture
- retrieval strategy
- condition label with meaningful runtime behavior differences

Do not count rows as distinct if they differ only by:

- output directory name
- agent nickname without architectural changes
- different judge settings
- different settle seconds without a principled reason

## What Does Not Count

Do not use these as paper rows:

- `local_stub`
- `codex`
- `openai`

`local_stub` is a deterministic test adapter, not a real evaluated system. `codex` and `openai` are scaffold stubs in the current repo and should not appear in benchmark results until they are fully wired and validated.

## Artifact Requirements Per Row

Each main-table row should have:

- `run_metadata.json`
- `metrics.json`
- `predictions.jsonl`
- `seed_turns.jsonl`
- `probes.jsonl`
- `judgments.jsonl`
- exact command used
- agent version or image reference
- benchmark commit SHA

If any row is missing these artifacts, exclude it from the main paper table.

## Minimal Result Table Shape

The main paper table should include at least:

- system or condition name
- runtime family
- memory mode
- `mean_score`
- grounded rate
- hallucination rate
- abstention rate
- per-category highlights for the hardest categories

After repeated runs are available, add variance to every headline metric.

## Decision Rules

- Prefer five clean rows over seven messy rows.
- Prefer two runtime families over one runtime family with many cosmetic variants.
- Prefer paired memory-on versus memory-off comparisons over a grab bag of unrelated systems.
- If `clawvault` is not operational, replace it with another external row rather than waiting on a blocked integration.
- If an external runtime cannot cleanly disable memory, document that limitation and compare against its strongest available "minimal memory" configuration.
