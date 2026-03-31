# Cortex Recall Channel Conflict — Diagnosis and Fixes

**Date**: 28 March 2026
**Context**: Phase 1 variance baselines revealed that adding Cortex (or LCM) to the OpenClaw agent reduces benchmark scores vs the file-memory-only baseline (1.78). Root cause analysis identified three specific failure modes.

---

## Problem Summary

When the Cortex plugin is active, the agent has **two parallel recall channels**:

1. **File-based memory** — the agent's built-in `AGENTS.md` instructs it to read `memory/YYYY-MM-DD.md` at session start. These daily notes contain raw, detailed facts from seeded conversations.

2. **Cortex auto-recall** — the plugin's `before_agent_start` hook injects a `<cortex_memories>` block containing semantically retrieved memories from the Cortex API.

The two channels conflict. When Cortex auto-recall returns partial or no results (due to API errors, retrieval gaps, or cold-start), the agent distrusts its own file notes and abstains — even when those notes contain the exact answer.

## Failure Modes (from Phase 1 data)

### 1. Cortex API Errors (502/503) During Probes

**Evidence**: 11 of 50 Cortex probe responses mention errors:
- "Cortex recall is currently unavailable (503), so I don't want to guess"
- "cortex lookup is currently failing (502)"

**Code path**: `recall/handler.ts` has retry logic with cold-start detection (`COLD_START_WINDOW = 3`), but the tool-level `cortex_search_memory` in `tools.ts` only retries once on 502/503 (`attempt < 1`). During sustained API instability, the agent gets `"Memory search failed: ..."` responses and abstains.

**Impact**: Direct score-0 or score-1 on any task where the agent encounters an API error during probe.

### 2. Skill Instructs Agent to Distrust File Notes

**Evidence**: Cortex agent responses repeatedly say "I checked both file memory and Cortex memory, and there were no matching records" — then abstain.

**Source**: The cortex-memory `SKILL.md` contains:
- "SEARCH BEFORE HEDGING. Before saying 'I don't have that information', search with `cortex_search_memory` using at least 2 different queries."
- "TOOL PRIORITY. `cortex_search_memory` for detailed fact retrieval. If the `memory_search` tool is available (memory-core plugin), also use it for file-based session logs."

This instructs the agent to search Cortex first, file memory second. When both return nothing (Cortex API issue + memory-core index incomplete), the agent abstains — even though the raw daily notes file likely has the answer sitting in the workspace.

**The baseline agent** has no such instructions. It simply reads its daily notes file and answers from them.

### 3. Agent-Instructions.ts Creates Confusing Dual Guidance

**Evidence**: `src/internal/agent-instructions.ts` injects this into `AGENTS.md`:
```
### Cortex vs File Memory
Use `cortex_save_memory` for cross-session persistence. Use `memory/YYYY-MM-DD.md` for session-local scratch notes.
```

This frames file memory as "scratch notes" — subordinate to Cortex. But in the benchmark, the daily notes often contain more detailed and accurate information than what Cortex auto-recall returns, because auto-capture summarises topics rather than preserving exact values.

---

## Proposed Fixes

### Fix 1: Improve Cortex API Reliability (Infrastructure)

**What**: Reduce 502/503 errors during probe phase.

**Where**: Server-side Cortex API infrastructure (not plugin code).

**Specifics**:
- The recall handler (`handler.ts`) already has retry logic with mode downgrade (`full` → `fast`). The tool search (`tools.ts`) has a single retry. Both are reasonable.
- The real fix is server-side: ensure the Cortex API doesn't return 502/503 during sustained load. The benchmark runs 50 probes sequentially, each hitting the recall endpoint — this is a realistic production workload.

**Priority**: High. This is the only fix that requires no plugin code changes.

### Fix 2: Adjust Skill to Not Override File-Based Recall

**What**: Change the cortex-memory `SKILL.md` so the agent treats file notes as a primary source, not a fallback.

**Where**: `~/skills/cortex-memory/SKILL.md` on the benchmark server (and upstream in the skill distribution).

**Current problematic instructions**:
```
TOOL PRIORITY. `cortex_search_memory` for detailed fact retrieval.
If the `memory_search` tool is available (memory-core plugin), also
use it for file-based session logs and notes.
```

**Proposed change**:
```
RECALL PRIORITY:
1. Check `<cortex_memories>` auto-recall context first
2. Read your daily notes (memory/YYYY-MM-DD.md) for detailed facts
3. Use `cortex_search_memory` for cross-session or older memories
4. If none of the above contain the answer, say what you know and
   flag what's missing — don't abstain if you have partial context
```

**Additional skill changes**:
- Remove "SEARCH BEFORE HEDGING" rule or soften it to "search Cortex if daily notes don't cover the topic"
- Add: "Your daily notes are often more detailed than Cortex auto-recall summaries. Trust them for exact values (port numbers, paths, config values)."
- Change "PRECISION OVER CONFIDENCE" to explicitly say: "If your daily notes contain a specific value, you can cite it — don't require Cortex confirmation."

**Priority**: High. This is the highest-impact fix — it directly addresses the recall channel conflict that causes most abstentions.

### Fix 3: Fix Agent Instructions Framing

**What**: Change the injected `AGENTS.md` section so file memory isn't dismissed as "scratch notes".

**Where**: `src/internal/agent-instructions.ts` in openclaw-cortex repo.

**Current**:
```
### Cortex vs File Memory
Use `cortex_save_memory` for cross-session persistence.
Use `memory/YYYY-MM-DD.md` for session-local scratch notes.
```

**Proposed**:
```
### Cortex vs File Memory
Your daily notes (`memory/YYYY-MM-DD.md`) contain detailed facts from
recent conversations — read them for exact values and specifics.
Cortex auto-recall provides broader cross-session context.
Use `cortex_save_memory` for important facts that should persist
beyond daily notes (decisions, architecture choices, key metrics).
```

**Priority**: Medium. Supports Fix 2 by aligning the injected instructions with the skill guidance.

### Fix 4: Graceful Degradation on Cortex Errors

**What**: When Cortex tools fail, the agent should fall back to file notes instead of abstaining.

**Where**: `SKILL.md` — the "Connection Check" section.

**Current**:
```
If it didn't [get auto-recall] and you need memory, try one
cortex_search_memory call — if it errors, Cortex is unreachable.
Do not retry in a loop. Fall back to file-based memory
(memory_search if available) and tell the user Cortex is
temporarily unavailable.
```

**Proposed**:
```
If Cortex is unreachable or returns errors, rely on your daily
notes (memory/YYYY-MM-DD.md) and MEMORY.md for recall.
These files contain detailed facts from recent conversations
and are always available. Do not abstain just because Cortex
is unavailable — answer from your notes.
```

**Priority**: Medium. Prevents the 502/503 → abstain cascade.

---

## Experimental Results (28-30 March 2026)

### Experiment 1: Skill fix only (Fix 2 + Fix 4)

Updated SKILL.md with recall priority reordering and graceful degradation. Auto-recall still enabled.

**Result: 1.31** — worse than Phase 1 Cortex (1.53). The skill changes are overridden by auto-recall's `prependContext` injection, which anchors agent reasoning before the skill instructions take effect.

### Experiment 2: Disable auto-recall (Fix 5)

Set `autoRecall: false` in plugin config. Kept auto-capture on, Cortex tools available, updated SKILL.md active.

**Result: 1.71 and 1.69 (mean 1.70 +/- 0.014)** — validated across 2 runs. +0.17 over Phase 1 Cortex, within 0.08 of file-memory baseline.

| Condition | Runs | Mean | Hit Rate | Abstain |
|-----------|------|------|----------|---------|
| **No-auto-recall** | **2** | **1.70** | **0.52** | **0.37** |
| File-mem baseline | 1 | 1.78 | 0.52 | 0.42 |
| Phase 1 Cortex | 3 | 1.53 | 0.44 | 0.43 |
| Skill-fix only | 1 | 1.31 | 0.32 | 0.46 |

### Conclusion

**Auto-recall injection is the primary problem, not the skill instructions.** The `<cortex_memories>` block injected as `prependContext` before each turn:
1. Anchors the agent on partial/noisy recalled memories before it reads its own files
2. Competes with file-based recall instead of supplementing it
3. Introduces 502/503 failure modes that force abstention

With auto-recall off, the agent reads daily notes naturally and uses `cortex_search_memory` on-demand. This result is highly reproducible (stddev 0.014 vs 0.187 for auto-recall-on Cortex). Cortex tools add genuine value in temporal reasoning (+0.53), multi-hop reasoning (+0.38), and fact recall (+0.50) vs the file-memory-only baseline.

---

## Revised Fix Priority

1. **Fix 5 (NEW, highest priority)**: Disable or redesign auto-recall. Short-term: ship with `autoRecall: false` as default. Medium-term: redesign to inject memories *after* file reads, not before — or make injection additive/optional rather than anchoring.

2. **Fix 1 (infrastructure)**: Fix Cortex API 502/503 errors under sustained load. Still relevant — even with auto-recall off, the agent's `cortex_search_memory` calls hit these errors.

3. **Fix 3 (agent-instructions.ts)**: Change "scratch notes" framing. Lower priority now that auto-recall is the proven culprit, but still worth doing for correctness.

4. **Fix 2 (skill)**: Already implemented and deployed. Helpful when auto-recall is off, but not the primary lever.

5. **Fix 4 (graceful degradation)**: Already implemented in the updated skill. Active in current config.
