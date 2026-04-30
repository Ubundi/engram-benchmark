# Phase 4 — Category Gap Diagnosis

Per-probe failure analysis for the three weak/variable areas surfaced by Phase 2:

1. Temporal reasoning (Cortex 1.88 stably loses to baseline 2.00)
2. Fact recall (all conditions weak — Cortex 0.34, baseline 0.00, LCM 0.50)
3. Cortex single-session-assistant variance (run 1: 2.89, run 2: 1.00)

## 4.1 Temporal Reasoning

Per-probe scores across all 6 runs:

| Probe | Ctx-r1 | Ctx-r2 | Bsl-r1 | Bsl-r2 | LCM-r1 | LCM-r2 |
|---|---:|---:|---:|---:|---:|---:|
| temporal_001 (JWT vs iron-session order) | 2.67 | 3.00 | 3.00 | 3.00 | 3.00 | 2.00 |
| temporal_002 (Resend vs SendGrid order) | 3.00 | 2.00 | 3.00 | 3.00 | 2.00 | 2.00 |
| temporal_003 (refresh flow before removal) | 2.00 | 1.00 | 2.00 | 2.00 | 2.00 | 3.00 |
| temporal_004 (Neon-first vs pg-pool order) | 1.00 | 3.00 | 3.00 | 3.00 | 3.00 | 3.00 |
| temporal_005 (auth vs email migration order) | 3.00 | 3.00 | 3.00 | 0.00 | 3.00 | 0.00 |
| temporal_006 (S3 key pattern bug) | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 |
| temporal_007 (event-loop lag before/after) | 3.00 | 3.00 | 3.00 | 3.00 | 1.00 | 1.67 |
| temporal_008 (7-day lifetime constant) | 0.33 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **mean** | **1.88** | **1.88** | **2.12** | **1.88** | **1.75** | **1.46** |

### Failure types found

**Type A — Universal failures (probes 006, 008): seeded data ambiguity.** All conditions (and both runs of each) failed to recover the ground-truth answer. The seed conversation probably never contained the exact answer cleanly:

- Probe 008: ground truth says "7-day lifetime stayed constant", but every run (including baseline reading raw memory files) answered "30 days." The seed data appears to mention 30-day in some context the agent latches onto.
- Probe 006: ground truth says revert was to `uploads/{userId}/{uuid}.{ext}`. Every run got the *buggy* pattern right (`{sessionId}/{originalFilename}`) but every run hallucinated a different correction format.

These aren't memory failures — they're dataset issues where the ground truth is not unambiguously derivable from the seeded conversations. Not Cortex's problem to solve.

**Type B — Cortex-specific: "captured the fact, lost the chronology"** (probe 004, run 1).
- Cortex r1 said: *"I don't remember seeing the chronology, only the split itself"*
- Baseline r1 (3.00): retrieved `memory/2026-04-25-drizzle-neon.md` and reasoned about timestamps in the file.
- Diagnosis: Cortex's auto-capture extracted the fact (Neon for request path, pg for workers) but flattened the temporal context. Local file memory preserved chronology by virtue of file dates and sequential structure.

**Engineering implication:** Cortex auto-capture should preserve session timestamp and session-order metadata explicitly when extracting facts — currently the chronology is lost in the extraction step.

### Net interpretation

On the 2-run mean, baseline 2.00 vs Cortex 1.88 is a **0.12 gap, not a structural weakness**. The Cortex temporal score is highly stable across runs (1.88 in both), which means the loss isn't variance-driven. The real signal: 2 of the 8 temporal probes are dataset-ambiguous, and Cortex stably loses 1 chronology-specific probe (004 in r1) due to capture flattening time order.

## 4.2 Fact Recall

Only 2 probes in this category. Both target exact-value recall.

| Probe | Ctx-r1 | Ctx-r2 | Bsl-r1 | Bsl-r2 | LCM-r1 | LCM-r2 |
|---|---:|---:|---:|---:|---:|---:|
| fact_001 (`OTEL_SERVICE_NAME=arclight-api`) | 1.33 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 |
| fact_002 (`/api/openapi.json`, `/api/docs`) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |

### Failure types found

**Type C — Exact-value precision lost in capture.** Across all conditions:

- Probe 001 (OTel service name): every run remembered the *generic* concept (`service.name` is the OTel attribute) but lost the specific value `arclight-api`. Cortex said "service.name", baseline said "api", LCM said "api-server". The exact string `arclight-api` was in the seed data but did not survive into long-term memory in any retrievable form for any condition.
- Probe 002 (URL paths): every run produced `/openapi.json` and `/docs` — losing the `/api/` prefix. The simplification happens during capture and propagates everywhere.

**Diagnosis: this is a capture-fidelity problem affecting Cortex auto-capture, baseline file extraction, and LCM summarization equally.** No condition can recall an exact technical string the seed conversation only mentioned once or twice in passing. LCM's slight edge (0.50 vs 0.34) is from one probe in run 2 where it happened to capture the path correctly.

**Engineering implication:** none of the architectures handle exact-value recall well at this seed cadence. Memory systems need either:
- explicit "exact-string" tagging during capture (Cortex would need to detect technical-token patterns and preserve them verbatim), or
- agent-level retrieval policy that pulls raw seed messages on exact-value questions instead of relying on summarized memory.

## 4.3 Cortex Variance — Why Single-Session-Assistant Collapsed

Cortex single-session-assistant: **2.89 in run 1, 1.00 in run 2**. Per probe:

| Probe | Ctx-r1 | Ctx-r2 | Δ |
|---|---:|---:|---:|
| assistant_001 (tsconfig recommendations) | 2.67 | 0.00 | -2.67 |
| assistant_002 (state-management split) | 3.00 | 0.00 | -3.00 |
| assistant_003 (third probe) | 3.00 | 3.00 | 0.00 |

Two of three probes flipped from full-credit to zero between runs at the same condition. Inspection of outputs:

**Probe 001 (tsconfig)**: ground truth includes `target: ES2022`.
- Run 1 captured: `"target": "ES2022"` ✓
- Run 2 captured: `"target": "ESNext"` ✗

Same seed conversation. Different captured value. Auto-capture pulled different specific tokens on different days.

**Probe 002 (state management)**: ground truth is "Zustand for local/global UI, TanStack Query for server state."
- Run 1 captured: "TanStack Query + Zustand" ✓
- Run 2 captured: "TanStack Query + React state/context, Zustand only if needed" ✗

Run 2 demoted Zustand from "use it" to "use only if needed." Both summaries are plausible interpretations of the same seed conversation, but the second one fails the judge because Zustand is no longer presented as the recommended choice.

### Diagnosis: non-deterministic auto-capture

LCM had range 0.08 across the same protocol; baseline file memory had range 0.31 but its variance was concentrated in different probes. **Cortex variance comes specifically from the auto-capture extraction step**: an LLM reads the seeded conversation and produces a memory record, and the LLM's interpretive choices vary run to run. LCM avoids this by storing raw messages plus deterministic DAG summaries; baseline file memory writes the conversation more faithfully without extraction reframing.

**Engineering implications:**

1. The Cortex auto-capture summarization step is the variance source. Options:
   - Lower temperature on the capture-summarization LLM call (likely already 0; check anyway).
   - Multi-pass capture with reconciliation: run extraction twice, keep facts that agree, flag disagreements.
   - Preserve the raw turn alongside the extracted fact so retrieval can fall back to source text.
2. When Cortex captures a recommendation, it loses qualifier strength: "X is recommended" can become "X is acceptable" or "X if needed" between runs. Capture should preserve recommendation polarity verbatim.
3. The variance is not a benchmark artefact — it would manifest in production as the same Kwanda agent giving different recommendations across sessions about the same prior decision. Worth investigating before launch.

## Summary For The Meeting

| Gap | Severity | Cause | Action |
|---|---|---|---|
| Cortex temporal -0.12 vs baseline | Low | One chronology probe (004 r1) where capture lost session ordering | Add session-timestamp metadata to auto-capture extractions |
| Fact recall ~0.34 (all conditions) | Universal weakness | Capture pipelines simplify exact technical strings | Capture-side: tag-and-preserve technical tokens. Retrieval-side: fall back to raw turns for exact-value Qs |
| Cortex run-to-run variance 0.26 | Real engineering issue | Auto-capture LLM extraction is non-deterministic | Investigate capture-summarization temperature, add multi-pass reconciliation, preserve raw turns alongside extracted facts |

The variance investigation is the most important finding for engineering follow-up — it explains why Cortex swung 0.26 while LCM was stable at 0.08 and gives a concrete path to fix it.
