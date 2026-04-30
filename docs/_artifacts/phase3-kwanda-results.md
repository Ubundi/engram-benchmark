# Phase 3 — Kwanda-Specific Benchmark Results (2026-04-29)

## What this measures

A 10-task benchmark slice authored to match Kwanda's actual ops categories, not the existing Engram-v3 "Arclight" technical-project tasks. Each task is a multi-turn conversation embedding a Kwanda-flavored decision, recurring routine, customer-context note, or operational fact, then probed in a fresh session.

Dataset: `data/raw/kwanda-test.json`. Tasks span:

- Recurring ops routines (Monday investor update with a tweak)
- Pricing and product decisions (R2000 agency tier; Cortex managed-only v1)
- Customer-context (Tyrelife: Anna for finance, Georg for product, async-written preferred)
- User style preferences (5-bullet summary format; security-first review order)
- Cross-system synthesis (Cortex-API regression: GitHub commit + Plane ticket + Slack incident)
- Recurring policy (3-month-revenue hiring rule, applied across two specific role discussions)
- Multi-session project handoff (landing-page redesign across three sessions)
- Exact-value config (API rate limit 60/min per tenant, burst 100, `/v1/*` except `/v1/health`)

All conditions ran on the same gpt-5.4 answer model, same gpt-4.1-mini judge with 3 passes, same protocol as the Engram runs. n=2 per condition.

## Headline

| Condition | Run 1 | Run 2 | Mean | Range |
|---|---:|---:|---:|---:|
| Cortex | 2.90 | 2.90 | **2.90** | **0.00** |
| Lossless-Claw | 2.70 | 2.60 | 2.65 | 0.10 |
| Baseline | 2.20 | 2.40 | 2.30 | 0.20 |

**Mean-on-mean gaps:**

- Cortex vs Baseline: **+0.60** (vs +0.37 on the Arclight test split — Kwanda probes amplify the Cortex advantage)
- Cortex vs LCM: **+0.25**
- LCM vs Baseline: **+0.35**

**Cortex was perfectly stable across the two Kwanda runs (range 0.00).** This is a striking contrast to its 0.26 range on Arclight. The implication is that Cortex variance on Arclight came from interpretive decisions during auto-capture (e.g. was "Zustand if needed" the same as "Zustand recommended"?), and Kwanda's more declarative content ("we decided to lead with R2000 agency tier", "the rate limit is 60/min") leaves less room for that drift.

## Score-band distribution

| Band | Cortex r1 | Cortex r2 | LCM r1 | LCM r2 | Baseline r1 | Baseline r2 |
|---|---:|---:|---:|---:|---:|---:|
| Grounded (3) | 9 | 9 | 7 | 7 | 5 | 6 |
| Generic (2) | 1 | 1 | 3 | 2 | 3 | 2 |
| Abstained (1) | 0 | 0 | 0 | 1 | 1 | 1 |
| Hallucinated (0) | 0 | 0 | 0 | 0 | 1 | 1 |

Cortex hallucination rate: 0% across both runs. LCM: 0%. Baseline: 10% in each run.

## Category mean scores (2-run means)

| Category | Cortex | LCM | Baseline | Winner |
|---|---:|---:|---:|---|
| single-session-user (Tyrelife customer context) | **3.00** | 3.00 | 3.00 | three-way tie at ceiling |
| single-session-assistant (pricing decision; Slack capture) | **3.00** | 3.00 | 3.00 | three-way tie |
| recurring-pattern (Monday update routine; user preferences) | **2.83** | 3.00 | 2.33 | LCM (very close) |
| multi-hop-reasoning (Cortex-API incident) | **3.00** | 2.00 | 1.50 | Cortex |
| knowledge-update (hiring policy applied across cases) | **3.00** | 2.00 | 2.00 | Cortex |
| multi-session (landing-page redesign across 3 sessions) | **2.50** | 1.50 | 0.50 | Cortex |
| fact-recall (API rate limit specifics) | **3.00** | 3.00 | 3.00 | three-way tie |

Notes:

- **Cortex stable wins, wide margin:** multi-hop reasoning (Cortex-API incident across GitHub/Plane/Slack), knowledge-update (hiring policy), multi-session (landing-page handoff). These are categories that depend on linking facts across sessions — Cortex's managed memory is materially better at this than baseline file memory or LCM's DAG.
- **Three-way tie on single-session probes:** when the answer is in one session and explicitly stated, all three architectures get full credit. The differentiation is in cross-session and synthesis.
- **Fact-recall surprise:** all three got 3.00 on the rate-limit probe. The seed conversation stated the values clearly twice, which was enough for every architecture to capture them — different from Arclight's `OTEL_SERVICE_NAME=arclight-api` probe where the value was mentioned once in passing.
- **LCM ties Cortex on recurring-pattern.** LCM's DAG navigation is a good fit for repeated-conversation patterns. Cortex's recurring-pattern came in slightly under because run 1 dropped a 2.67 on the Monday-update tweak probe.

## Comparison to Arclight test split

| Condition | Arclight 2-run mean | Kwanda 2-run mean | Δ Kwanda − Arclight |
|---|---:|---:|---:|
| Cortex | 2.05 | **2.90** | +0.85 |
| LCM | 1.85 | 2.65 | +0.80 |
| Baseline | 1.685 | 2.30 | +0.61 |

All three conditions score higher on Kwanda than on Arclight, but **Cortex's lift is the largest** (+0.85). The Cortex–Baseline gap widens from +0.37 (Arclight) to +0.60 (Kwanda).

Why the Kwanda probes are easier overall:
- Smaller search space (10 tasks, fewer cross-task interference)
- Higher answer redundancy (most key facts are stated twice in the seed)
- More declarative ground truths ("we decided X", "the rule is Y") vs Arclight's interpretive ones ("the recommended tsconfig settings include...")

Why Cortex's lift is biggest:
- Multi-hop and multi-session probes (Cortex's strongest categories) are over-represented in the Kwanda slice relative to Arclight.
- Cortex variance on Arclight was largely concentrated in single-session-assistant probes that asked about interpretive recommendations. Kwanda probes ask about explicit decisions, removing that variance source.

## What this strengthens

The "Cortex helps Kwanda" claim is now backed by direct evidence on Kwanda-shaped tasks:

- Cortex 2.90 vs Baseline 2.30 = **+0.60 lead** (vs +0.37 on Arclight)
- Cortex's wins are concentrated in cross-session synthesis and decision tracking (multi-hop, multi-session, knowledge-update) — the categories Kwanda agents need most.
- Cortex's stability problem (0.26 variance on Arclight) does not appear on Kwanda's declarative content (0.00 variance). Kwanda's actual production content is closer in shape to the Kwanda test slice than to Arclight, so production variance may be lower than Arclight suggested.

## What this does not change

- The Arclight evidence still matters for general "long-term agent memory" claims.
- Cortex auto-capture non-determinism is still a real engineering follow-up — Kwanda probes don't trigger it because the content is declarative, but agents will encounter ambiguous content in production.
- Exact-value capture is still a known weakness; the rate-limit probe happened to have redundant statements that compensated.
- LCM still has stable strengths on cross-agent memory and fact-recall in the broader Arclight context.

## Run artifacts

- Cortex r1: `outputs/exploratory/kwanda/cortex/2026-04-29-cortex-codex-gpt54-1/`
- Cortex r2: `outputs/exploratory/kwanda/cortex/2026-04-29-cortex-codex-gpt54-2/`
- LCM r1: `outputs/exploratory/kwanda/lossless-claw/2026-04-29-lossless-claw-codex-gpt54-1/`
- LCM r2: `outputs/exploratory/kwanda/lossless-claw/2026-04-29-lossless-claw-codex-gpt54-2/`
- Baseline r1: `outputs/exploratory/kwanda/baseline/2026-04-29-baseline-codex-gpt54-1/`
- Baseline r2: `outputs/exploratory/kwanda/baseline/2026-04-29-baseline-codex-gpt54-2/`
- Dataset: `data/raw/kwanda-test.json`
- Generation script: `scripts/build_kwanda_dataset.py`
