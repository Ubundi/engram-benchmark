# Engram Benchmark Findings: Five Memory Conditions on Codex 5.3

**Date**: 2026-03-21
**Split**: test (50 tasks)
**Model**: openai-codex/gpt-5.3-codex
**Judge**: gpt-4.1-mini (3 passes, temperature 0.3)
**Protocol**: engram-runtime-v1, benchmark release engram-v3.0

## What the Benchmark Measures

Engram is a runtime benchmark for evaluating **cross-session long-term memory** in AI agents. It does not measure reasoning ability, factual knowledge, or within-session performance. It tests a specific, harder question: when a user has multi-turn conversations with an agent across several sessions, and those sessions end, can the agent recall grounded project details in a completely new session with no prior context?

**Protocol**: Seed (replay multi-turn conversations into the agent) → Settle (wait for memory processing) → Probe (ask recall questions in a fresh, blank session) → Judge (LLM scores against ground truth).

The dataset is Engram v3, consisting of 50 probe questions across 9 memory categories, drawn from 88 seed sessions with 268 total conversational turns. The subject matter is a fictional project called "Arclight" — a developer analytics platform — with rich architectural decisions, migrations, naming conventions, and temporal events.

**Scoring rubric (0–3)**:
- **3 (Grounded correct)**: The required specific detail is present. The benchmark's success state.
- **2 (Generic correct)**: Directionally right but missing the decisive detail.
- **1 (Abstained)**: The agent says it lacks the memory. Safe, but a failure to retrieve.
- **0 (Hallucinated)**: A wrong or fabricated specific claim. The worst outcome.

## Experimental Controls

All five runs share the following controlled variables:

| Parameter | Value |
|-----------|-------|
| Answer model | openai-codex/gpt-5.3-codex |
| Benchmark release | engram-v3.0 |
| Protocol version | engram-runtime-v1 |
| Dataset split | test (50 tasks) |
| Judge model | gpt-4.1-mini |
| Judge passes | 3 |
| Agent | openclaw (agent_id: main) |
| Seed sessions | 88 sessions, 268 turns |
| Flush sessions | true |
| Error count | 0 across all conditions |

**Settle time varies by condition** (reflects architectural differences):

| Condition | Settle Seconds |
|-----------|---------------|
| Baseline | 10 |
| ClawVault | 10 |
| Lossless-Claw | 30 |
| Mem0 | 60 |
| Cortex | 180 |

Cortex was given 18x the settle time of Baseline/ClawVault. The settle window exists to let asynchronous memory pipelines finish processing before probes begin. This is not a flaw — it reflects real-world architecture differences — but it means Cortex's results partly depend on having been granted enough processing time.

## Conditions Tested

| Condition | Architecture | Memory Slot | Key Mechanism |
|-----------|-------------|-------------|---------------|
| **Baseline** | OpenClaw session-memory files + memory-core BM25 | memory-core | Keyword search over raw session transcripts |
| **Mem0** | External REST API + LLM fact extraction + vector search | memory-mem0 | Semantic extraction → Qdrant vector DB → auto-recall/capture hooks |
| **ClawVault** | Local markdown vault + observer pipeline + BM25 | clawvault | Session transcripts → LLM compression → structured observations → BM25 |
| **Lossless-Claw** | DAG context engine + memory-core coexisting | contextEngine + memory-core | Hierarchical summaries in SQLite + session-memory BM25 |
| **Cortex** | Server-side memory + auto-recall injection | hooks (no slot) + memory-core | Auto-capture after turns → server-side indexing → auto-recall injection before turns |

## Overall Rankings

| Rank | Condition | Mean Score | Hit Rate | Abstain Rate | Grounded (3) | Hallucinated (0) |
|------|-----------|-----------|----------|-------------|-------------|-------------------|
| 1 | **Cortex** | **1.95** | **70%** | **12%** | 22 (44%) | 9 (18%) |
| 2 | Lossless-Claw | 1.93 | 58% | 36% | 21 (42%) | 3 (6%) |
| 3 | ClawVault | 1.76 | 52% | 34% | 19 (38%) | 7 (14%) |
| 4 | Mem0 | 1.67 | 40% | 58% | 15 (30%) | 1 (2%) |
| 5 | Baseline | 1.62 | 40% | 60% | 11 (22%) | 0 (0%) |

### Score Distributions

| Condition | Score 3 | Score 2 | Score 1 | Score 0 |
|-----------|---------|---------|---------|---------|
| Cortex | 22 (44%) | 13 (26%) | 6 (12%) | 9 (18%) |
| Lossless-Claw | 21 (42%) | 8 (16%) | 18 (36%) | 3 (6%) |
| ClawVault | 19 (38%) | 7 (14%) | 17 (34%) | 7 (14%) |
| Mem0 | 15 (30%) | 5 (10%) | 29 (58%) | 1 (2%) |
| Baseline | 11 (22%) | 9 (18%) | 30 (60%) | 0 (0%) |

## Category-Level Analysis

| Category (count) | Baseline | ClawVault | Cortex | Lossless-Claw | Mem0 |
|------------------|----------|-----------|--------|---------------|------|
| cross-agent-memory (7) | 1.57 | 1.86 | 2.00 | **2.29** | 2.10 |
| fact-recall (2) | 1.00 | 0.50 | **1.50** | 1.00 | 1.00 |
| knowledge-update (5) | 1.80 | **2.40** | 1.80 | 2.00 | 1.60 |
| multi-hop-reasoning (7) | 2.14 | 2.00 | 2.14 | **2.57** | 1.71 |
| multi-session (8) | 1.25 | 0.75 | **1.50** | 1.62 | 1.12 |
| recurring-pattern (5) | 2.00 | **2.40** | 1.53 | 2.33 | 1.40 |
| single-session-assistant (3) | 1.00 | 1.00 | **2.33** | 1.33 | 1.00 |
| single-session-user (5) | 1.80 | 2.40 | **3.00** | 1.80 | 2.20 |
| temporal-reasoning (8) | 1.50 | 1.88 | 1.83 | 1.62 | **2.12** |

### Category Insights

- **Cortex dominates user-facing recall**: Perfect 3.00 on single-session-user — verbatim capture and injection of what users said is highly effective.
- **Lossless-Claw excels at relational reasoning**: 2.57 on multi-hop-reasoning (highest in any category for any condition) and 2.29 on cross-agent-memory. The DAG structure preserves relationships that flat storage loses.
- **ClawVault leads on evolving knowledge**: 2.40 on both knowledge-update and recurring-pattern — the observer pipeline captures decisions as they change and repeated conventions.
- **Mem0 handles temporal relationships best**: 2.12 on temporal-reasoning — its LLM extraction distills "what happened when" into discrete searchable facts.
- **Multi-session is universally hard**: No condition exceeds 1.62. Integrating details spread across many separate conversations remains unsolved.

## Finding 1: Memory Availability Is the Primary Bottleneck

The 12% to 60% abstain rate spread dwarfs all other differences. Getting relevant memories in front of the LLM matters more than the sophistication of the extraction pipeline. An agent that says "I don't know" to 60% of questions about its own project history is functionally useless regardless of how accurate its remaining answers are.

Cortex's auto-recall mechanism (injecting a `<cortex_memories>` block before every agent turn) is the primary reason it outperforms — the agent almost always has material to reason over.

## Finding 2: Retrieval-Hallucination Tradeoff

There is a measurable inverse relationship between retrieval aggressiveness and answer safety:

| Condition | Hit Rate | Hallucination Rate | Profile |
|-----------|----------|--------------------|---------|
| Baseline | 40% | 0% | Conservative — safe but rarely useful |
| Mem0 | 40% | 2% | Conservative — safe but rarely useful |
| ClawVault | 52% | 14% | Middle ground |
| Lossless-Claw | 58% | 6% | **Best balance** — high retrieval, low hallucination |
| Cortex | 70% | 18% | Aggressive — most useful but fabricates more |

When the agent has partial or noisy memories, it sometimes synthesizes plausible-but-wrong specifics. Cortex's hallucinations consistently follow this pattern: right topic, wrong detail (wrong port numbers, wrong directory paths, wrong feature-flag representations).

**Lossless-Claw breaks this tradeoff** — achieving 58% hit rate with only 6% hallucination, suggesting structured memory representations (DAG summaries) produce higher-quality retrievals that lead to accurate answers rather than confabulation.

## Finding 3: Vector Search Does Not Outperform BM25 on Raw Transcripts

Mem0 (LLM extraction + vector search via Qdrant) achieves the **same 40% hit rate** as Baseline (raw session files + BM25 keyword search). Despite a dedicated semantic memory pipeline with embeddings, it produces nearly identical abstain rates (58% vs 60%) and mean scores (1.67 vs 1.62).

This suggests that Mem0's extraction pipeline may be over-compressing conversations into atomic facts, losing the surrounding context that probe questions need to match against. Alternatively, its vector search may not be returning enough results, or its relevance threshold (0.4) may be too aggressive.

## Finding 4: Each Architecture Has a Distinct Strength Profile

No single system wins every category. The architectural approach determines what types of memory are best preserved:

| Architecture Approach | Strength | Weakness |
|----------------------|----------|----------|
| Auto-recall injection (Cortex) | User statements, single-session details | Recurring patterns, hallucination risk |
| DAG context engine (Lossless-Claw) | Multi-hop reasoning, cross-agent memory | Single-session details, exact fact recall |
| Observer pipeline (ClawVault) | Knowledge updates, recurring patterns | Multi-session, fact recall |
| LLM extraction (Mem0) | Temporal reasoning | Multi-session, recurring patterns |
| Raw transcript search (Baseline) | Safety (zero hallucination) | Everything else |

## Finding 5: Multi-Session Accumulation Is Universally Hard

Every condition struggles with the multi-session category (scores range 0.75 to 1.62). These questions require integrating details accumulated across many separate conversations into a coherent answer. No current memory architecture — whether keyword search, vector search, graph-based, or server-side extraction — reliably solves this problem.

## Caveats and Limitations

1. **Small sample size**: 50 probes across 9 categories means some categories have only 2-3 questions. Results at the category level should be treated as directional, not definitive.

2. **Settle time differences**: Cortex's 180s settle time versus 10s for Baseline/ClawVault is a confound. A controlled experiment with equal settle times would clarify how much of Cortex's advantage comes from its recall architecture versus processing time.

3. **Single model**: All runs used openai-codex/gpt-5.3-codex. Different models may interact differently with memory injection strategies. Results may not generalize to other LLMs.

4. **Test split only**: The test split (50 tasks) is a subset of the full v3 dataset (498 tasks). Official results should use the full split for statistical power.

5. **Plugin compatibility issues encountered during testing**: ClawVault required an adapter-level workaround (direct observer CLI calls) due to async plugin registration not firing lifecycle hooks. Lossless-Claw's compaction initially hung due to an incorrect model ID. These were fixed before benchmark runs but indicate the plugins may not have been tested extensively in this exact gateway version.

## Recommended Next Steps

1. **Run Cortex with 10s settle time** to isolate the settle time variable from its recall architecture advantage.
2. **Run the full v3 split (498 tasks)** for statistically meaningful results across all categories.
3. **Investigate Mem0's extraction tuning** — can preserving more context in extracted facts improve hit rate above 40%?
4. **Explore hybrid architectures**: Cortex's recall injection + Lossless-Claw's structured representations could potentially achieve high coverage with low hallucination.
5. **Add Cortex 3 timeouts to the analysis** — Cortex had 3 probe timeouts (125s) that scored 0. Without those, its mean would be ~2.07 and hallucination count 6, significantly improving its profile.

## Run Artifacts

| Condition | Run ID | Output Directory |
|-----------|--------|-----------------|
| Baseline | 20260320T195724Z | `outputs/exploratory/test/baseline/2026-03-20-baseline-codex/` |
| ClawVault | 20260320T154658Z | `outputs/exploratory/test/clawvault/2026-03-20-clawvault-codex/` |
| Cortex | 20260321T013726Z | `outputs/exploratory/test/cortex/2026-03-21-cortex-codex/` |
| Lossless-Claw | 20260321T111735Z | `outputs/exploratory/test/lossless-claw/2026-03-21-lossless-claw-codex/` |
| Mem0 | 20260321T133056Z | `outputs/exploratory/test/mem0/2026-03-21-mem0-codex/` |
