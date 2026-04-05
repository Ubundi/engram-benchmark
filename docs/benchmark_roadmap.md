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

### Step 3: Disable auto-recall — DONE (effective, validated)

Set `autoRecall: false` in Cortex plugin config. Kept auto-capture on, Cortex tools available, updated SKILL.md active.

**Result**: Two runs scored **1.71** and **1.69** (mean **1.70 +/- 0.014**) — extremely consistent and the best Cortex configuration tested.

### Full comparison

| Condition | Runs | Mean Score | Hit Rate | Abstain | vs Clean |
|-----------|------|-----------|----------|---------|---------|
| File-mem baseline | 1 | 1.78 | 0.52 | 0.42 | +0.18 |
| **Cortex no-auto-recall** | **2** | **1.70** | **0.52** | **0.37** | **+0.10** |
| Clean baseline | 1 | 1.60 | 0.44 | 0.44 | — |
| Phase 1 Cortex (auto-recall on) | 3 | 1.53 | 0.44 | 0.43 | -0.07 |
| Cortex skill-fix (auto-recall on) | 1 | 1.31 | 0.32 | 0.46 | -0.29 |

### Category highlights (no-auto-recall mean of 2 runs vs file-mem baseline)

| Category | No-AR | File-Mem | Delta |
|----------|-------|---------|-------|
| temporal-reasoning | **2.15** | 1.62 | **+0.53** |
| multi-hop-reasoning | **1.81** | 1.43 | **+0.38** |
| fact-recall | **1.00** | 0.50 | **+0.50** |
| recurring-pattern | **1.97** | 2.00 | -0.03 |
| cross-agent-memory | 1.79 | **1.86** | -0.07 |
| knowledge-update | 1.73 | **2.20** | -0.47 |
| single-session-user | 1.60 | **1.80** | -0.20 |
| multi-session | 1.23 | **1.88** | -0.65 |
| single-session-assistant | 1.50 | **2.33** | -0.83 |

Cortex tools add genuine value in temporal reasoning, multi-hop reasoning, and fact recall — categories requiring cross-session knowledge retrieval. The agent loses ground in multi-session and single-session categories where file notes alone are sufficient and Cortex tool calls add latency and over-thinking.

### Key finding

**Auto-recall injection is the primary problem.** The `<cortex_memories>` block injected as `prependContext` before each turn:
1. Anchors the agent's reasoning on partial/noisy recalled memories
2. Competes with the agent's natural file-reading behaviour
3. Introduces 502/503 failure modes that force abstention

When auto-recall is disabled, the agent reads its daily notes naturally and uses `cortex_search_memory` on-demand — getting the best of both worlds. The result is highly reproducible (stddev 0.014 across 2 runs vs 0.187 for Phase 1 Cortex with auto-recall).

### Run artifacts

- `outputs/exploratory/test/baseline-clean/2026-03-28-baseline-clean-codex-1/`
- `outputs/exploratory/test/cortex/2026-03-29-cortex-v2.12-codex-skill-fix-1/`
- `outputs/exploratory/test/cortex/2026-03-30-cortex-v2.12-codex-no-autorecall-1/`
- `outputs/exploratory/test/cortex/2026-03-31-cortex-v2.12-codex-no-autorecall-2/`

### Next steps for Cortex product

The auto-recall feature needs to be rethought:
1. **Short term**: Ship with `autoRecall: false` as default. Cortex tools + file notes is a proven, reproducible configuration.
2. **Medium term**: Redesign auto-recall to inject memories as supplementary context *after* the agent reads its files, not before — or make it additive rather than anchoring.
3. **Long term**: Investigate why multi-session and single-session-assistant categories still trail the file-mem baseline even without auto-recall — the Cortex skill instructions may still cause over-thinking in simple recall tasks.

## Phase 3b: Plugin release validation — COMPLETE (2-4 April 2026)

**Goal**: Validate that the shipped plugin (v2.13.0) with all changes baked in produces the same results as the manual v2.12.0 + config overrides.

### Step 4: v2.13.0 default config — DONE (regression detected)

Updated EC2 to openclaw-cortex v2.13.0 (autoRecall defaults to false, new SKILL.md with FILE NOTES FIRST / SEARCH CORTEX PROACTIVELY / ANSWER FROM WHAT YOU HAVE rules, handler gate for daily notes). Ran with **no manual config overrides** — pure out-of-the-box.

**Result: 1.42** — significant regression from v2.12.0 no-auto-recall (1.70). Abstain rate jumped to 48% (vs 37%). Hit rate dropped to 33% (vs 52%).

| Condition | Score | Hit Rate | Abstain |
|-----------|-------|----------|---------|
| v2.12 no-auto-recall (manual) | **1.70** | **0.52** | **0.37** |
| **v2.13.0 default** | **1.42** | **0.33** | **0.48** |

**Root cause: Skill over-caution.** The v2.13.0 SKILL.md rules created an abstention bias:
- 17/50 probes showed abstain-like language ("I checked memory and don't have that")
- 7 tasks that scored 3 in v2.12 dropped to 0-1 in v2.13 — the agent had context in file notes but abstained after Cortex search returned nothing
- Rules 2 ("SEARCH BEFORE HEDGING" → abstain gate), 5 ("PRECISION OVER CONFIDENCE" → flag gaps), and 6 ("ANSWER FROM WHAT YOU HAVE" — too weak at position 6) conflicted: the abstain/hedging rules overrode the answer-from-notes rule
- Only 9/50 probes referenced file notes — the agent wasn't reading them enough

**Category regressions vs v2.12 no-AR:**

| Category | v2.13 | v2.12 no-AR | Delta |
|----------|-------|-------------|-------|
| temporal-reasoning | 1.38 | **2.15** | -0.77 |
| single-session-assistant | 0.67 | **1.50** | -0.83 |
| recurring-pattern | 1.20 | **1.97** | -0.77 |
| knowledge-update | 1.00 | **1.73** | -0.73 |
| multi-session | 0.86 | **1.23** | -0.37 |
| cross-agent-memory | **2.33** | 1.79 | +0.54 |
| single-session-user | **2.20** | 1.60 | +0.60 |

### Step 5: Skill-fix v2 — DONE (not effective)

Targeted changes to 4 SKILL.md rules to reduce abstention bias while keeping precision for specific values:

1. **Rule 1**: "FILE NOTES FIRST" → "FILE NOTES ARE YOUR PRIMARY SOURCE"
2. **Rule 2**: "SEARCH BEFORE HEDGING" → "SEARCH CORTEX TO SUPPLEMENT" (removed abstain gate)
3. **Rule 5**: "PRECISION OVER CONFIDENCE" → "PRECISION FOR SPECIFIC VALUES"
4. **Rule 6**: "ANSWER FROM WHAT YOU HAVE" → "ALWAYS ATTEMPT AN ANSWER"

**Result: 1.43** — no improvement over v2.13 default (1.42). Abstain rate actually increased to 58%. Skill wording alone is not the cause.

### Step 6: Isolation test — v2.13 plugin + original v2.12 SKILL.md — DONE

Deployed the original v2.12.0 SKILL.md (from repo at commit 879df11) onto the server with v2.13.0 plugin code. Tests whether the v2.13 skill rewrite or the plugin code changes caused the regression.

**Result: 1.52** — better than v2.13 skill variants (~1.42) but still below 1.70. Suggested the issue was partially skill, partially plugin code.

### Step 7: v2.12.0 reproduction — DONE (critical finding)

Downgraded plugin back to v2.12.0, set autoRecall=false manually, deployed original v2.12 SKILL.md — exact same setup that scored 1.70 on March 30-31.

**Result: 1.53** — the 1.70 result is no longer reproducible.

### Key finding: external drift, not plugin regression

| Run | Date | Plugin | Skill | Score | Abstain |
|-----|------|--------|-------|-------|---------|
| v2.12 no-AR run 1 | Mar 30 | 2.12 | modified | **1.71** | 0.37 |
| v2.12 no-AR run 2 | Mar 31 | 2.12 | modified | **1.69** | 0.37 |
| v2.13 default | Apr 2 | 2.13 | v2.13 | 1.42 | 0.48 |
| v2.13 skill-fix-v2 | Apr 3 | 2.13 | fixed v2 | 1.43 | 0.58 |
| v2.13 + v2.12 skill | Apr 3 | 2.13 | v2.12 | 1.52 | 0.44 |
| **v2.12 no-AR run 3** | **Apr 4** | **2.12** | **v2.12** | **1.53** | **0.48** |
| v2.13 merged skill | Apr 4 | 2.13 | merged | 1.55 | 0.56 |

**The v2.13 plugin code is not the cause of the regression.** The identical v2.12 setup that scored 1.70 on March 30-31 now scores 1.53 on April 4 — a 0.17 drop with no changes to the plugin, skill, or benchmark code.

**Most likely cause: model behavior drift.** The answer model (gpt-5.3-codex) is served by OpenAI and may have changed provider-side between March 31 and April 2. This is the same pattern observed in Phase 1, where original single-run scores (1.95-1.99) were not reproducible at those levels in later runs. The benchmark is sensitive to model behavior changes that are outside our control.

**Implications:**
1. The v2.13 plugin changes (autoRecall default, AGENTS.md reframing, handler gate) are **not harmful** — they produce equivalent results to v2.12 when tested on the same day
2. A merged SKILL.md (v2.13 structure + v2.12's simpler tone, 6 rules instead of 8, strong anti-abstention rule at position 2) scores on par with v2.12 original skill (1.55 vs 1.53 same-day). This is the recommended skill going forward.
3. Absolute scores are unreliable for cross-day comparisons — only same-day relative comparisons are meaningful
4. Phase 4 (model sensitivity testing) is now higher priority to understand how much variance is model-driven

### Run artifacts

- `outputs/exploratory/test/cortex/2026-04-02-cortex-v2.13-codex-default-1/`
- `outputs/exploratory/test/cortex/2026-04-02-cortex-v2.13-codex-skill-fix-v2-1/`
- `outputs/exploratory/test/cortex/2026-04-03-cortex-v2.13-codex-v212skill-1/`
- `outputs/exploratory/test/cortex/2026-04-04-cortex-v2.12-codex-no-autorecall-3/`
- `outputs/exploratory/test/cortex/2026-04-04-cortex-v2.13-codex-merged-skill-1/`

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
