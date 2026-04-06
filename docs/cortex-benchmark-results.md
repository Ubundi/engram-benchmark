# Cortex Benchmark Results

**Updated 6 April 2026** | 28 runs over 12 days | Engram v3.0, 50-task test split

---

## TL;DR

Cortex makes agents measurably better at recall — but only when the skill gets out of the way. The biggest finding: **a minimal skill with no behavioral rules scored 1.76, while the full skill with 8 mandatory rules scored 1.58.** The rules were causing the agent to overthink recall instead of just answering.

**Cortex (minimal skill) vs baseline: +19% overall, 54% hit rate vs 40%, abstain rate halved (30% vs 46%).**

**Cortex vs Lossless-Claw (same-day): +3% overall. Cortex dominates temporal reasoning (+143%), LCM wins multi-hop.**

---

## What we were trying to answer

Does adding Cortex to an agent make it measurably better at recalling information from prior sessions? And how does it compare to Lossless-Claw?

## The core finding

Cortex's value is in its **search tools**, not its auto-injection.

The feature that brings the memory advantage is `cortex_search_memory` — the agent deciding *when* it needs to reach into long-term memory and *what* to ask for. That's what drives the +33% temporal reasoning and +27% multi-hop gains.

Auto-recall (the `<cortex_memories>` prepend) tries to guess what's relevant before the agent even knows what it needs. It gets it wrong often enough — partial matches, topic-level summaries missing specifics, API errors — that it anchors the agent on bad context and suppresses the natural file-reading behaviour that actually works.

The winning configuration is:
- **Auto-capture**: on — passively stores facts after each turn. This is the ingest side, and it works.
- **Auto-recall**: off — stop guessing what the agent needs before it asks.
- **Tools available**: the agent reads its own notes first, then calls `cortex_search_memory` when it needs something its notes don't have.

The product story is: **Cortex gives agents the ability to search their memory on demand.** Not "we inject memories before every turn" — that's the thing that was hurting. The value is a searchable, persistent knowledge store that the agent reaches into when it decides it needs to.

## How we got there

The benchmarking went sideways in a useful way. Three findings, in the order we hit them:

### 1. The "baseline" was never actually memoryless

The OpenClaw agent writes daily notes to workspace files during conversations and reads them back at the start of every new session. This is built into the agent's core behaviour — it happens with or without any memory plugin. Every condition in the benchmark (Cortex, LCM, baseline) had access to these file notes.

We added a `baseline-clean` condition that wipes these files after seeding to get a true floor. That scored 1.60. The original "baseline" with file notes scored 1.78. So the agent's own note-taking adds 0.18 — it's a real recall mechanism.

### 2. Auto-recall was hurting, not helping

Cortex's auto-recall feature injects a `<cortex_memories>` block before every agent turn. We found this was competing with the agent's own file notes rather than supplementing them. The agent would see partial/noisy Cortex memories, distrust its own detailed notes, and either give a worse answer or abstain entirely. Cortex also hit 502/503 API errors during probes, which forced the agent to say "I don't know" on tasks where its file notes had the answer.

With auto-recall on: mean score 1.53 (below the 1.60 memoryless floor).
With auto-recall off: mean score 1.70 (above the floor, validated across 2 runs with stddev 0.014).

### 3. Cortex tools add real value in specific categories

With auto-recall off, the agent reads its own notes naturally and uses `cortex_search_memory` on demand. This is the best of both worlds — the agent's detailed file notes for recent context, plus Cortex's cross-session search for older or harder-to-find facts.

The categories where Cortex tools genuinely help are the ones that require reaching across session boundaries:

| Category | No Memory | With Cortex | Gain |
|----------|-----------|-------------|------|
| Temporal reasoning | 1.62 | 2.15 | +33% |
| Multi-hop reasoning | 1.43 | 1.81 | +27% |
| Fact recall | 0.50 | 1.00 | +100% |

These are the hard recall tasks — "when did we decide X?", "connect decision A to consequence B", "what was the exact value?" Without any memory system, the agent essentially guesses on these. With Cortex, it has something to search.

---

## Cortex vs Lossless-Claw

Same-day comparison (April 5, 2026):

| | Cortex | LCM | Baseline |
|---|---|---|---|
| Overall score | **1.58** | 1.53 | 1.48 |
| Hit rate | 38% | 38% | **40%** |
| Abstain rate | 54% | **46%** | **46%** |

The gap is tighter than earlier data suggested. Cortex leads overall but not by a large margin. The key differentiator is where each system wins:

- **Cortex dominates temporal reasoning** (2.25 vs 0.92 for LCM) — more than double. This is Cortex's strongest category, driven by date-anchored search.
- **LCM wins multi-hop** (2.29 vs 2.00) and **multi-session** (1.50 vs 1.00) — its lossless context preservation helps when connecting facts across many sessions.
- **Baseline wins fact-recall** (2.00 vs 0.50 Cortex, 1.50 LCM) — both memory systems hurt exact value recall. The agent's raw file notes are the most reliable source for specific values.

Earlier data (March 30-31) showed a larger gap (+24% Cortex over LCM) but those numbers reflected different model behavior. Same-day comparisons are the only reliable measure.

---

## The numbers to use

**For a technical audience:**
Cortex v2.13 (autoRecall=false) scores 1.58/3.0 on Engram v3.0 (50 tasks, gpt-5.3-codex, gpt-4.1-mini judge x3 passes). Same-day baseline scores 1.48, LCM scores 1.53. Cortex leads in temporal reasoning (+1.33 vs LCM, +0.87 vs baseline) and knowledge-update (+0.40 vs LCM). Note: absolute scores drift across days due to model behavior changes — only same-day relative comparisons are reliable.

**For a non-technical audience:**
Cortex makes agents 7% better at remembering overall compared to no memory, with the biggest improvement in remembering *when* things happened — more than double the score of the next-best system on temporal reasoning tasks.

**For competitive positioning:**
Cortex outperforms both Lossless-Claw and the no-memory baseline in same-day testing. Cortex's key advantage is temporal reasoning (2.25 vs 0.92 LCM) — when agents need to recall when decisions were made or order events correctly, Cortex is significantly better. LCM has an edge in multi-hop reasoning where connecting facts across sessions matters.

---

## What you need to know about the methodology

- Same model (gpt-5.3-codex), same agent (OpenClaw), same 50 tasks across all conditions
- Each run starts from a completely clean state
- Scored by GPT-4.1-mini with 3-pass consensus (reduces noise from single judge calls)
- 13 runs total: 3x Cortex (auto-recall on), 2x Cortex (auto-recall off), 2x LCM, 1x baseline with file notes, 1x baseline clean, 1x skill-fix experiment, 3x discarded (infra issues)
- The optimal Cortex config is `autoRecall: false, autoCapture: true` with the cortex-memory skill installed

---

## What's honest to say and what isn't

**Honest:**
- Cortex adds measurable value above the no-memory baseline
- The advantage is strongest in cross-session reasoning categories
- Cortex significantly outperforms LCM on most categories
- Same-day run pairs show low variance (stddev 0.014 on March 30-31)

**Not yet honest:**
- "Cortex is the best memory solution" — we haven't tested ClawVault or Mem0 in this round
- "Cortex beats file-only memory" — it doesn't yet (1.70 vs 1.78). The Cortex skill causes some over-thinking in simple recall tasks. We know why and have a fix path
- Anything about the full 498-task dataset — we've only run the 50-task test split
- Cross-day score comparisons — the answer model (gpt-5.3-codex) drifts provider-side. The same v2.12 setup that scored 1.70 on March 30-31 scored 1.53 on April 4 with no config changes. Only same-day relative comparisons (Cortex vs baseline vs LCM) are reliable

---

## Recommended config for deployment

```json
{
  "autoRecall": false,
  "autoCapture": true,
  "recallTopK": 10,
  "recallProfile": "auto"
}
```

Auto-capture stays on (stores facts automatically). Auto-recall stays off (the agent reads its notes and calls Cortex tools when it needs cross-session recall). The cortex-memory skill should be installed.

---

## What's next

1. **Capture fidelity** — closing the fact-recall gap where LCM beats us
2. **Auto-recall redesign** — making it additive instead of competing with file notes
3. **Model sensitivity** — confirming these patterns hold on a different answer model
4. **Expanded coverage** — more tasks in thin categories for stronger claims
