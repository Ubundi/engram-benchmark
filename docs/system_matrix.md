# Candidate System Matrix

This document defines a practical evaluation lineup for Engram's main results table.

## Goal

Show that Engram compares memory behavior across multiple systems or conditions, not only `baseline` versus one augmented memory plugin.

## Recommended Publishable Matrix

The current recommended OpenClaw matrix is four evaluated rows:

| Row | Runtime family | System or condition | Memory configuration | Adapter path | Why it belongs in the main table | Status target |
|---|---|---|---|---|---|---|
| A | OpenClaw CLI | `baseline` | Native agent behavior with no benchmark-specific memory augmentation | `--agent openclaw --condition baseline` | Reference point for all OpenClaw-based comparisons | Must run |
| B | OpenClaw CLI | `mem0` | OpenClaw with the Mem0-backed memory plugin enabled | `--agent openclaw --condition mem0` | Adds an external semantic memory backend under the same runtime family | Must run if the condition is available in the target environment |
| C | OpenClaw CLI | `clawvault` | OpenClaw with ClawVault integrated | `--agent openclaw --condition clawvault` | Adds a structured, local-first memory condition in the same runtime family | Must run if the condition is available in the target environment |
| D | OpenClaw CLI | `cortex` | OpenClaw with Cortex memory enabled | `--agent openclaw --condition cortex` | Current headline augmented condition; needed for continuity with prior results | Must run |
| E | OpenClaw CLI | `lossless-claw` | OpenClaw with Lossless-Claw context engine | `--agent openclaw --condition lossless-claw` | DAG-based lossless context (fundamentally different from semantic extraction) | Must run if the condition is available in the target environment |

If all five rows are not feasible, the minimum fallback is two rows:

- `baseline`
- `cortex`

That fallback is weaker than the full matrix because it drops the extra within-family contrast provided by Mem0, ClawVault, and Lossless-Claw.

## Preferred Expansion

If engineering bandwidth allows, expand beyond the four core OpenClaw rows:

| Priority | Add-on row | Why it helps |
|---|---|---|
| High | Additional OpenClaw memory condition | Increases within-family contrast if another stable condition exists later |
| Medium | Additional benchmark release or corpus | Tests whether findings persist across benchmark variations |
| Medium | Repeated-run depth beyond 3 | Strengthens stability claims even without adding more systems |

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

### Row B: OpenClaw mem0

- Use only if the target environment actually exposes the `mem0` condition.
- Keep all benchmark settings identical to Row A except for agent identity and condition.
- If `mem0` is unavailable or unstable, drop it and document the reduced matrix explicitly.

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <mem0-agent-id> \
  --condition mem0 \
  --split v3 \
  --output-dir outputs/mem0
```

### Row C: OpenClaw clawvault

- Use only if the target environment actually exposes the `clawvault` condition.
- Keep all benchmark settings identical to Row A except for agent identity and condition.
- If `clawvault` is unavailable or unstable, drop it and document the reduced matrix explicitly.

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <clawvault-agent-id> \
  --condition clawvault \
  --split v3 \
  --output-dir outputs/clawvault
```

### Row D: OpenClaw cortex

- Use the same OpenClaw versioning discipline as Rows A-C.
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

### Row E: OpenClaw lossless-claw

- Use only if the target environment has `@martian-engineering/lossless-claw` installed.
- Lossless-Claw replaces the default context engine with a DAG-based summarization tree. It stores all messages in SQLite and builds hierarchical summaries, allowing the agent to expand condensed context on demand.
- Unlike Cortex/Mem0, this is primarily an in-session context management system rather than a cross-session semantic memory. The benchmark tests whether lossless context preservation improves recall compared to no augmentation.
- Keep all benchmark settings identical to Row A except for agent identity and condition.
- Settle time is 30s (compaction runs synchronously after each turn, but a short buffer ensures the final compaction pass completes).

Command template:

```bash
JUDGE_API_KEY="<key>" python3 -m benchmark.run \
  --agent openclaw \
  --agent-id <lossless-claw-agent-id> \
  --condition lossless-claw \
  --split v3 \
  --flush-sessions \
  --output-dir outputs/lossless-claw
```

## Recommended Pairing Strategy

Choose conditions that let the paper isolate this effect:

- within-family memory effect:
  `baseline` vs `mem0` vs `clawvault` vs `lossless-claw` vs `cortex`

That lineup is stronger than comparing only `baseline` vs `cortex` because it lets the paper say:

- Engram detects meaningful memory differences inside one runtime family across multiple memory architectures.
- The matrix covers both semantic extraction (Cortex, Mem0), structured vaults (ClawVault), and lossless DAG context (Lossless-Claw).

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

- Prefer four clean rows when available, but do not force inclusion of unstable plugin conditions.
- Prefer stable OpenClaw conditions over speculative external rows that are not part of the current paper plan.
- If `mem0` or `clawvault` is not operational, drop the missing row, keep the matrix honest, and disclose that limitation clearly.
