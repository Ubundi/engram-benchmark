# Benchmark Roadmap

**Date**: 26 March 2026
**Updated**: 30 March 2026
**Status**: Living document — updated as work progresses

---

## Where we are

Phase 1 variance baselines and Phase 2 diagnosis are complete. Phase 3 experimental fixes have identified the key problem and a working mitigation.

**Key discovery**: The "baseline" condition was never truly memoryless — the OpenClaw agent's built-in file memory (`memory/YYYY-MM-DD.md`) persists across session flushes and provides recall during probes. All conditions share this mechanism.

**Key fix**: Disabling Cortex auto-recall (the `<cortex_memories>` injection before each turn) while keeping Cortex tools available raised scores from 1.53 to 1.71 — within 0.07 of the file-memory baseline (1.78). Auto-recall was actively degrading performance by competing with the agent's own file notes.

## What we're optimising for

**Cost-aware rigour.** The full 498-task dataset is too expensive and time-consuming to run routinely. Each 50-task run already involves 88 seed sessions (268 turns), 180s settle, 50 probes, and triple-pass judging. A full run would be ~10x that. Instead, we get more value from repeated runs on the 50-task split and targeted expansions where the data is thin.

---

## Phase 1: Establish variance baselines — COMPLETE (27 March 2026)

**Goal**: Answer "how much do results move between identical runs?" before making any more changes.

**Runs completed**: 6 total (Cortex x3, LCM x2, Baseline x1)

### Results

| Condition | Runs | Mean Score | StdDev | Hit Rate | Abstain Rate |
|-----------|------|-----------|--------|----------|-------------|
| **Baseline** (no memory) | 1 | **1.78** | — | 0.52 | 0.42 |
| **Cortex** v2.12 | 3 | 1.53 | 0.187 | 0.44 | 0.43 |
| **Lossless-Claw** v0.4 | 2 | 1.37 | 0.014 | 0.26 | 0.64 |

Individual Cortex runs: 1.35, 1.73, 1.52. Individual LCM runs: 1.38, 1.36.

**Category breakdown (means):**

| Category | Cortex | LCM | Baseline |
|----------|--------|-----|----------|
| cross-agent-memory | 1.62 | 2.00 | 1.86 |
| fact-recall | 1.00 | 2.00 | 0.50 |
| knowledge-update | 1.73 | 1.10 | 2.20 |
| multi-hop-reasoning | 1.76 | 1.45 | 1.43 |
| multi-session | 1.00 | 1.10 | 1.88 |
| recurring-pattern | 1.80 | 1.30 | 2.00 |
| single-session-assistant | 1.11 | 1.00 | 2.33 |
| single-session-user | 1.78 | 1.30 | 1.80 |
| temporal-reasoning | 1.64 | 1.25 | 1.62 |

### Key findings

1. **Baseline outperforms both memory systems.** The no-memory agent scored 1.78 vs Cortex 1.53 and LCM 1.37. This is the opposite of the original single-run results.

2. **Cortex has high run-to-run variance** (stddev 0.19 on a 0-3 scale). The spread from 1.35 to 1.73 means a single run is unreliable for comparisons.

3. **LCM is consistent but low.** Very tight variance (0.01) but 64% abstain rate — the agent frequently refuses to answer rather than attempting recall.

4. **All scores dropped from original runs.** The March 20-22 single runs (Cortex 1.95-1.99, LCM 1.93, Baseline 1.62) are not reproducible at these levels. Possible causes: model provider-side changes, API instability during runs, or the original results were high-variance outliers.

5. **Memory systems may be hurting recall behaviour.** The high abstain rates for Cortex (43%) and especially LCM (64%) suggest that when the agent has memory tools, it over-relies on them and refuses to answer when retrieval returns nothing — whereas the baseline agent attempts answers from parametric knowledge or in-context patterns.

### Run artifacts

- `outputs/exploratory/test/cortex/2026-03-26-cortex-v2.12-codex-variance-{1,2,3}/`
- `outputs/exploratory/test/lossless-claw/2026-03-27-lossless-claw-codex-variance-{1,2}/`
- `outputs/exploratory/test/baseline/2026-03-27-baseline-codex-variance-1/`

**Versions**: Cortex runs used cortex `bc4b777`, openclaw-cortex `879df11` (v2.12.0). All runs used `openai-codex/gpt-5.3-codex` as the answer model and `gpt-4.1-mini` as the judge (3 passes).

## Phase 2: Diagnose the baseline-beats-memory problem — IN PROGRESS (28 March 2026)

**Goal**: Understand *why* the baseline outperforms memory systems before investing in further runs.

### Root cause: FOUND

**The baseline is not memoryless.** The OpenClaw agent has built-in file-based memory independent of any plugin:

1. `AGENTS.md` instructs the agent to "Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context" at the start of every session
2. During seeding, the agent writes facts to `workspace/memory/2026-03-27.md` and `workspace/MEMORY.md` as part of its normal behaviour
3. The `/new` session flush clears conversation history but **not** workspace files
4. At probe time, the agent reads these files and has access to all seeded facts

This means **all three conditions** (Cortex, LCM, baseline) share the same file-based recall mechanism. The "baseline" was never truly memoryless — it had the agent's built-in file memory all along.

### Why memory plugins scored LOWER than file-only baseline

Analysis of 12 tasks where baseline scored 3 and Cortex scored 0-1 reveals a consistent pattern:

1. **Recall channel conflict**: The Cortex agent searches both "file memory" and "Cortex memory". When Cortex returns nothing or partial results, the agent reports "I checked both file memory and Cortex memory, and there were no matching records" — even when the file memory likely had the answer. The plugin's presence causes the agent to distrust its own file-based notes.

2. **Infrastructure failures**: Cortex had 502/503 errors during probes. The agent responds: "Cortex recall is currently unavailable (503), so I don't want to guess." The baseline agent has no such failure mode.

3. **Over-cautious abstain behaviour**: Memory-equipped agents (especially LCM with 64% abstain rate) are trained/prompted to say "I don't have that in memory" rather than attempting an answer. The baseline agent just answers from its notes without second-guessing.

4. **The cortex-memory skill** may be instructing the agent to prioritize Cortex search results over local file reads, effectively suppressing the agent's own note-reading behaviour.

### Implications

- **All prior benchmark comparisons are invalid for measuring memory plugin value.** The baseline was never memoryless — it had the exact same file-based notes as every other condition.
- **The benchmark is actually measuring**: does adding a memory plugin *on top of* the agent's built-in file memory help or hurt?
- **Current answer**: it hurts, because of recall channel conflict, infrastructure reliability, and over-cautious abstain behaviour.

## Phase 3: Fix and re-run — COMPLETE (30 March 2026)

**Goal**: Implement fixes based on Phase 2 diagnosis and validate with benchmark runs.

### Step 1: True memoryless baseline — DONE

Added `baseline-clean` condition to the benchmark adapter. After seeding, workspace memory files are wiped before probes begin. This establishes the genuine floor.

**Result**: baseline-clean scored **1.60** — confirming file memory adds +0.18 over nothing (file-mem baseline = 1.78).

### Step 2: Skill fix — DONE (not effective)

Updated `SKILL.md` to reorder recall priority (daily notes first, Cortex supplementary), removed "SEARCH BEFORE HEDGING" gate, added graceful degradation on Cortex errors.

**Result**: Scored **1.31** — worse than Phase 1 Cortex (1.53). The skill changes alone don't fix the problem; the auto-recall injection overrides skill instructions.

### Step 3: Disable auto-recall — DONE (effective)

Set `autoRecall: false` in Cortex plugin config. Kept auto-capture on, Cortex tools available, updated SKILL.md active.

**Result**: Scored **1.71** — best Cortex result yet.

### Full comparison

| Condition | Mean Score | Hit Rate | Abstain | vs Clean |
|-----------|-----------|----------|---------|---------|
| **Cortex no-auto-recall** | **1.71** | **0.52** | **0.38** | **+0.11** |
| File-mem baseline | 1.78 | 0.52 | 0.42 | +0.18 |
| Clean baseline | 1.60 | 0.44 | 0.44 | — |
| Phase 1 Cortex (mean) | 1.53 | 0.44 | 0.43 | -0.07 |
| Cortex skill-fix | 1.31 | 0.32 | 0.46 | -0.29 |

### Category highlights (no-auto-recall vs file-mem baseline)

| Category | No-AR | File-Mem | Delta |
|----------|-------|---------|-------|
| temporal-reasoning | **2.17** | 1.62 | **+0.55** |
| recurring-pattern | **2.33** | 2.00 | **+0.33** |
| fact-recall | **1.50** | 0.50 | **+1.00** |
| knowledge-update | **2.27** | 2.20 | +0.07 |
| single-session-user | **2.00** | 1.80 | +0.20 |
| multi-session | 0.83 | **1.88** | -1.05 |
| single-session-assistant | 1.33 | **2.33** | -1.00 |
| cross-agent-memory | 1.43 | **1.86** | -0.43 |

Cortex tools add significant value in temporal, recurring-pattern, and fact-recall categories. The agent loses ground in multi-session and single-session-assistant — likely because the Cortex skill's instructions cause the agent to over-think in these categories instead of just reading its notes.

### Key finding

**Auto-recall injection is the primary problem.** The `<cortex_memories>` block injected as `prependContext` before each turn:
1. Anchors the agent's reasoning on partial/noisy recalled memories
2. Competes with the agent's natural file-reading behaviour
3. Introduces 502/503 failure modes that force abstention

When auto-recall is disabled, the agent reads its daily notes naturally and uses `cortex_search_memory` on-demand — getting the best of both worlds.

### Run artifacts

- `outputs/exploratory/test/baseline-clean/2026-03-28-baseline-clean-codex-1/`
- `outputs/exploratory/test/cortex/2026-03-29-cortex-v2.12-codex-skill-fix-1/`
- `outputs/exploratory/test/cortex/2026-03-30-cortex-v2.12-codex-no-autorecall-1/`

### Next steps for Cortex product

The auto-recall feature needs to be rethought:
1. **Short term**: Ship with `autoRecall: false` as default for benchmark-sensitive deployments
2. **Medium term**: Redesign auto-recall to inject memories as supplementary context *after* the agent reads its files, not before — or make it additive rather than anchoring
3. **Long term**: Investigate why multi-session and single-session-assistant categories regress even without auto-recall — the Cortex skill instructions may still be interfering

## Phase 4: Model sensitivity testing

**Goal**: Understand how much of the variance is model-driven vs memory-system-driven.

Phase 1 showed all scores dropped from original runs. If the model changed (provider-side), that could explain the across-the-board decline. Testing a second model also answers: does Cortex's *relative* advantage over baseline hold across models?

| Run | What | Why |
|-----|------|-----|
| Cortex + Model B x1 | Same Cortex config, different answer model | Isolates memory layer contribution from model capability |
| Baseline + Model B x1 | No memory, same alternate model | Control for the model swap |

**Cost**: 2 runs. Pick a model that's meaningfully different (e.g., Anthropic Claude instead of OpenAI Codex).

## Phase 5: Expanded task coverage (targeted, not full)

**Goal**: Strengthen the evidence in categories where 50 tasks gives us thin data.

Instead of the full 498-task run, pull targeted subsets from the full dataset:

| Subset | Why |
|--------|-----|
| +20 multi-hop reasoning tasks | Cortex trails Lossless-Claw here (2.14 vs 2.57) — need to know if that's real or noise from 7 tasks |
| +20 knowledge update tasks | Only 5 tasks in current split — too few to draw conclusions |
| +20 recurring pattern tasks | Cortex's weakest category (1.53) — is this a real gap or small-sample variance? |

**How**: Use `--max-tasks` with filtered task IDs from the full dataset. Seed only the sessions relevant to the selected probes.

**Cost**: ~3 partial runs (20-30 tasks each), much cheaper than a full 498. Gives us category-level confidence where it matters most.

## Phase 6: Competitive refresh

**Goal**: Updated head-to-head comparison once Cortex improvements have landed.

Only run this after Phases 1-3 are done and Cortex hallucination rate is measurably improved. Re-run all five conditions (or the top 3: Cortex, Lossless-Claw, Baseline) with 2 runs each on the 50-task split.

**This is the run that produces publishable numbers.** Everything before it is internal iteration.

---

## What we're deliberately not doing

- **Full 498-task runs.** Cost and time don't justify it when repeated 50-task runs give us variance data and targeted expansions fill category gaps. The 50-task split was designed to be representative — running it multiple times is more informative than running the full set once.
- **Settle-time sensitivity analysis.** Valid methodological question, but low priority. The 180s/10s split reflects real operational differences (server-side vs local). We could test 60s/120s/300s for Cortex, but the expected insight is small relative to the cost.
- **New competitor additions.** Not until our existing baselines have variance data. Adding a 6th system to single-run comparisons doesn't make the evidence stronger.
- **Confidence interval calculations on current data.** Single runs can't produce meaningful CIs. Phase 1 fixes this — once we have 3 runs per condition, we can compute them properly.

---

## Run budget estimate

| Phase | Runs | Tasks/run | Total task-evaluations |
|-------|------|-----------|----------------------|
| 1. Variance baselines | 6 | 50 | 300 |
| 2. Post-improvement | 2 | 50 | 100 |
| 3. Hallucination fixes | 2-4 | 50 | 100-200 |
| 4. Model sensitivity | 2 | 50 | 100 |
| 5. Targeted expansion | 3 | 20-30 | 60-90 |
| 6. Competitive refresh | 6 | 50 | 300 |
| **Total** | **21-23** | | **~960-1090** |

For comparison, a single full-dataset run would be 498 task-evaluations. This roadmap gets ~2x the total evaluations spread across focused, answerable questions rather than one broad pass.

---

## Success criteria

When this roadmap is done, we should be able to say:

1. Cortex consistently outperforms the no-memory baseline (not within run-to-run variance)
2. The abstain and hallucination rates are competitive with the best alternative
3. The advantage holds across at least two answer models
4. Category-level claims are backed by enough data points to be credible
5. We understand and can explain *why* memory helps (or when it doesn't)
6. We have a repeatable process for re-benchmarking as Cortex evolves

Phase 1 showed us that criterion #1 is not yet met. The immediate priority is understanding why, then fixing it.
