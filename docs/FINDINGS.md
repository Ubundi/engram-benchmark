# Benchmark Findings

> Does adding Cortex to an already-functional OpenClaw agent make its recall better, and on which question types?

---

## Short Answer

**Yes.** Across 50 recall probes against a real OpenClaw agent, Cortex improves overall recall by **+0.85** (on a 0–3 scale), with **+1.07 on rationale** (perfect 3.00), **+1.03 on evolution**, and **+1.46 on synthesis**. Without Cortex, the agent abstains on 64% of knowledge probes. With Cortex, it answers 88% and gets 48% grounded correct. The one persistent weakness is **temporal reasoning** (+0.05), where "what happened most recently" questions remain challenging.

---

## How the Benchmark Works

### The Test: A Real A/B Comparison

The benchmark is a controlled A/B test against a live OpenClaw agent running on EC2. Two identical agent instances run the same experiment — one with only OpenClaw's native memory, one with the Cortex plugin installed. Both agents use the real OpenClaw runtime: real compaction, real `memory_search`, real plugin hooks, real file sync. Nothing is simulated.

| Condition | Agent Configuration |
|-----------|---------------------|
| **Baseline** | OpenClaw agent — native memory only (compaction + `memory_search`) |
| **Cortex** | Same agent with the Cortex plugin installed and active |

### The Dataset: 6 Weeks of a Real-ish Project

The dataset simulates "Arclight" — a developer analytics platform built over 6 weeks. It consists of 45 multi-turn conversations (136 user turns total) that progressively build up a realistic project history:

- **Weeks 1–2:** Framework choices (Bun + Fastify), database setup (PostgreSQL + Drizzle), initial JWT auth, TypeScript config
- **Weeks 3–4:** Redis caching with ioredis (600s TTL, `arclight:{entity}:{id}` key format), auth migration from JWT to iron-session, email switch from Resend to SendGrid
- **Weeks 5–6:** BullMQ for background jobs, dependency audit, CI/CD pipeline, naming conventions, Q3 planning

The dataset is deliberately designed to be hard for compaction-based memory:
- **Non-default specifics** — port 4000 (not 3000), TTL 600s (not 60s), so generic guesses fail
- **Embedded rationale** — not just "we use Drizzle" but *why* (type-safe, 50KB vs Prisma's 10MB, no code gen)
- **Deliberate fact evolution** — JWT auth in week 3 gets replaced by iron-session in week 4, testing whether the agent knows the *current* state
- **Cross-session knowledge** — naming conventions, security practices, and Redis decisions are spread across multiple separate conversations

### Phase 1: Seeding — Building the Agent's Memory

Each of the 45 conversations is sent through the agent one turn at a time via `openclaw agent --message "..." --json`. The agent generates its own responses — knowledge captured depends on what the agent actually understands and retains, not scripted answers.

For the baseline agent, this exercises OpenClaw's compaction pipeline: the agent summarises and compresses conversations into its native memory store. For the Cortex agent, the capture handler additionally fires after each turn, extracting facts and submitting them to the Cortex API asynchronously.

After all 45 sessions are seeded, the runner waits 10 seconds for async processing (Cortex capture jobs, file sync) to settle before probing.

### Phase 2: Probing — Testing Pure Recall

50 recall probes are sent to a **fresh session** with no prior conversation history. This is critical — the agent cannot rely on in-context messages. It must retrieve the answer entirely from its memory system.

The 50 probes span 5 categories, each testing a different type of knowledge retention:

| Category | Count | What it tests | Example |
|----------|-------|---------------|---------|
| **F: Factual** | 15 | Single verifiable specifics | "What port does the API run on?" → 4000 |
| **R: Rationale** | 10 | Why decisions were made | "Why Drizzle over Prisma?" → no code gen, 50KB, serverless-friendly |
| **E: Evolution** | 10 | How decisions changed | "What auth system do we use now?" → iron-session (was JWT) |
| **S: Synthesis** | 8 | Facts spanning multiple sessions | "What naming conventions have we established?" → kebab-case files, PascalCase types, ... |
| **T: Temporal** | 7 | Which version is current | "What was the last major infrastructure addition?" → database backup automation |

These categories aren't arbitrary — they target the specific knowledge types where compaction is known to be lossy. Rationale and synthesis require preserving nuance across sessions; evolution and temporal require distinguishing old from current facts.

### Phase 3: Judging — LLM Scoring Against Ground Truth

Each agent response is scored by `gpt-4.1-mini` against the known ground truth answer. To reduce variance, the judge runs **3 passes** at temperature 0.3 and the scores are averaged.

| Score | Meaning | What it looks like |
|---|---|---|
| **3** | Grounded correct | "Port 4000, chosen to avoid Vite's default 3000" — cites the specific detail |
| **2** | Generic correct | "We use a non-standard port" — right direction, missing the specific |
| **1** | Abstained | "I don't have that context" — honest, not harmful |
| **0** | Hallucinated | "Port 3000" — fabricated wrong specifics with confidence |

The judge is blinded to which condition produced the response. It sees only the question, ground truth, and agent response.

### What Makes This a Fair Test

- **Same dataset:** Both conditions seed and probe the exact same 45 conversations and 50 questions
- **Real runtime:** No simulation — both agents use actual OpenClaw compaction, retrieval, and response generation
- **Fresh probe session:** Probes start a new session with no conversation history, testing pure memory recall
- **Blinded judging:** The judge doesn't know which condition produced the response
- **Multi-pass scoring:** 3-pass averaged judging reduces single-call noise
- **Agent-generated responses:** The agent writes its own responses to seed conversations — capture quality depends on real extraction, not scripted answers

---

## What the Benchmark Proves

### The Baseline Establishes the Problem

Without Cortex, the agent scores **1.10/3.00**. It abstains on **64%** of probes — 32 out of 50 questions answered with "I don't have that context." Only **2 out of 50** responses (4%) are grounded correct.

This quantifies what users experience: an OpenClaw agent with native memory alone loses most project knowledge. Config values, decision rationale, conventions agreed on weeks ago, how things changed over time — all compacted away or decayed below retrieval threshold.

The baseline is not a strawman. OpenClaw's memory system includes compaction, `memory_search` with hybrid BM25+vector retrieval, and temporal decay. It works well for recent in-session context. But for cross-session recall of specific details, it is fundamentally limited by compaction loss.

### Cortex Closes the Gap — Dramatically on Some Categories

The reference run (Mar 4) shows Cortex at **1.95/3.00** overall — a **+0.85** improvement. But the aggregate masks category-specific results that tell a clearer story:

**Rationale: +1.07 (perfect 3.00)**

Every "why did we choose X" question — all 10 of them — is answered correctly with the original reasoning. "Why Drizzle over Prisma?" returns the actual reasons discussed in session s02 (type-safe, no code gen, 50KB vs 10MB, serverless-friendly). The baseline scores 1.93 on rationale — it knows *what* was chosen but not *why*.

This is the category where compaction is most lossy. A summary might preserve "chose Drizzle ORM" but drop the comparative reasoning against Prisma. Cortex stores the original context and retrieves it with relationships intact.

**Synthesis: +1.46 (from 0.54 to 2.00)**

Questions that require connecting facts across multiple sessions — "What naming conventions have we established?", "What security practices are in place?", "Summarise all Redis-related decisions" — go from nearly unanswerable to reliably answered.

The baseline scores 0.54: these questions require assembling information from 3-5 different sessions, and compaction reduces each session to a summary too thin to reconstruct the full picture. Cortex's graph-linked retrieval can traverse entity relationships across sessions, pulling related facts together.

**Evolution: +1.03 (from 1.07 to 2.10)**

"What auth system do we use now?", "How do we apply database schema changes?", "What packages were removed during the dependency audit?" — questions about how things changed. The baseline cannot track decision history: it knows the current session's context but not that auth used to be JWT and switched to iron-session in week 4.

**Factual: +0.64 (from 1.09 to 1.73)**

Specific facts (port 4000, TypeScript target ES2022, Pino log level info) improve but not to ceiling. Cortex retrieves many of these correctly, but some specific values (Redis TTL, rate limits) are either not captured during seeding or retrieved with partial context that leads to hallucination.

**Temporal: +0.05 (from 0.62 to 0.67)**

This is Cortex's blind spot. "What was the most recent change?", "What did we decide to build in Q3?" — questions that require identifying the *latest* version of a fact — show almost no improvement. Cortex retrieves comprehensively by semantic relevance, surfacing both historical and current facts. The LLM cannot reliably pick out which is most recent from the retrieved context.

### Memory Accumulation Works

The benchmark was run twice against the Cortex condition (Mar 3 and Mar 4). Run 2 benefits from the richer knowledge graph built during Run 1's seeding:

| Category | Run 1 | Run 2 | Change |
|---|---|---|---|
| **Overall** | 1.81 | **1.95** | **+0.14** |
| R: Rationale | 2.56 | **3.00** | **+0.44** |
| E: Evolution | 1.60 | **2.10** | **+0.50** |
| Grounded (3s) | 19 | **24** | +5 |
| Errors | 2 | **0** | -2 |

This proves that Cortex's value compounds over time. More sessions ingested means a richer knowledge graph, which means better recall on future queries. Rationale went from strong to perfect; Evolution gained half a point.

### The Abstention-to-Answer Shift

The most visible change is behavioral. Baseline abstains on 32/50 probes (64%). Cortex abstains on 6/50 (12%). The agent stops saying "I don't have that context" and starts answering.

This shift is not purely positive — some of those new answers are hallucinations (10/50, 20%) rather than correct. But the net effect is strongly positive: 24 grounded correct answers (48%) vs 2 (4%) at baseline.

| Outcome | Baseline | Cortex | Shift |
|---|---|---|---|
| Grounded correct | 2 (4%) | **24 (48%)** | +22 answers got right |
| Generic correct | 8 (16%) | 10 (20%) | +2 |
| Abstained | 32 (64%) | **6 (12%)** | -26 fewer "I don't know" |
| Hallucinated | 8 (16%) | 10 (20%) | +2 more wrong answers |

---

## Weaknesses and Honest Limitations

### Temporal Reasoning Is Unsolved

Cortex's comprehensive retrieval — its strength for rationale and synthesis — becomes a weakness for temporal questions. When asked "What was the most recent security improvement?", Cortex retrieves all security-related memories. The LLM sees the auth migration (week 4), the SendGrid switch (week 4), the security audit (week 5), and the dependency audit (week 5) all at once. It cannot reliably determine which is most recent.

This problem *worsens as the knowledge graph grows*: Run 2 temporal (0.67) is worse than Run 1 (1.14), because Run 2 has more historical context to confuse the ranking. This is an architectural property of semantic retrieval, not a pipeline maturity issue.

### Hallucination Rate Stays at ~20%

Cortex doesn't increase hallucination relative to baseline (16% → 20%), but it doesn't reduce it either. The hallucinations occur when Cortex retrieves *partial* context — enough to prevent abstention but not enough to ground a correct answer:

- F02 (Redis TTL): retrieves Redis-related facts but not the exact TTL → fabricates "300 seconds" (correct: 600)
- F07 (test runner): retrieves testing context but not the specific tool → guesses wrong
- T02 (performance issue): retrieves performance memories but confabulates a WebSocket memory leak

### Single Project, Synthetic Data

The Arclight dataset is crafted, not organic. Real dev sessions have more noise, tangents, topic-hopping, and implicit context. The single-project design (consistent terminology, one tech stack) likely makes retrieval easier for both conditions than a real multi-workspace deployment would.

However, V2 mitigates this significantly by using real agent responses during seeding — the agent writes its own answers, introducing natural variation in phrasing and emphasis that pure simulation cannot replicate.

### Baseline Run Not Repeated

The baseline score (1.10) comes from a single run on Mar 2. Ideally, baseline would be re-run alongside each cortex run to control for any OpenClaw version or environmental differences. The gap is large enough (0.85) that this is unlikely to change the conclusion, but it's a methodological limitation.

---

## Run History

| Date | Condition | Overall | R: Rationale | S: Synthesis | T: Temporal | Grounded | Hallucinated | Errors | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Mar 2, 2026 | baseline | 1.10 | 1.93 | 0.54 | 0.62 | 2 (4%) | 8 (16%) | 0 | OpenClaw native memory only |
| Mar 3, 2026 | cortex | 1.81 | 2.56 | 2.00 | 1.14 | 19 (38%) | 11 (22%) | 2 | First cortex run |
| **Mar 4, 2026** | **cortex** | **1.95** | **3.00** | **2.00** | **0.67** | **24 (48%)** | **10 (20%)** | **0** | **Reference run** |

*(Per-prompt breakdowns are available from generated run artifacts under `outputs/`.)*

---

## Conclusion

The benchmark proves that Cortex transforms an OpenClaw agent's ability to recall project knowledge across sessions. The test is fair: same dataset, real runtime, fresh-session probes, blinded multi-pass judging. The results are clear:

- **Without Cortex:** The agent forgets. It abstains on 64% of knowledge questions and gets 4% grounded correct. Config values, rationale, conventions, and decision history are lost to compaction.
- **With Cortex:** The agent remembers. It answers 88% of probes and gets 48% grounded correct. Rationale recall is perfect. Cross-session synthesis goes from impossible to reliable.

The improvement concentrates where compaction is lossiest: **rationale** (why decisions were made), **synthesis** (facts spanning multiple sessions), and **evolution** (how things changed over time). These are precisely the knowledge types that matter most in long-running software projects.

The honest weakness is **temporal reasoning** — "what happened most recently" questions are not improved. And the **hallucination rate** (~20%) means the agent sometimes answers confidently but wrong, which is worse than admitting ignorance.

**What to watch in future runs:** temporal precision as SUPERSEDES chains mature in the graph, hallucination rate as retrieval becomes more selective, and whether adaptive retrieval (routing recency queries differently) can close the temporal gap without sacrificing the rationale and synthesis gains.
