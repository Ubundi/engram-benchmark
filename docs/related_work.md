# Related Work Matrix

This document positions Engram against prior long-term memory benchmarks with a comparison matrix intended for benchmark docs and paper writing.

## Positioning Summary

Engram is closest to a runtime benchmark for post-context-window agent memory, not a pure long-context reading benchmark. Compared with prior work, it is narrower in modality and domain breadth, but stronger on:

- a fixed runtime protocol (`seed -> settle -> probe -> judge`)
- fresh-session probing after memory ingestion
- system-neutral adapter support
- frozen release settings
- auditable per-run artifacts for every reported result

## Matrix

| Benchmark | Primary object of evaluation | Task design | Runtime setup | Memory horizon | Scoring | Public artifacts |
|---|---|---|---|---|---|---|
| **Engram** | Long-term memory behavior of an agent runtime under a fixed benchmark protocol | 498 tasks across 9 categories focused on grounded recall, updates, temporal reasoning, cross-session synthesis, abstention, and hallucination handling | Seed prior sessions into the target runtime, wait for memory to settle, then probe in a fresh session with no haystack in context | Multi-session project memory after the original context is gone; official public release is `engram-v3.0` with `engram-runtime-v1` | Multi-pass 0-3 judge rubric aggregated to mean score, plus abstention, hallucination, and per-category breakdowns | Frozen release policy, public dataset, reproducibility docs, submission validation, and required run artifacts (`metrics.json`, `run_metadata.json`, `predictions.jsonl`, `seed_turns.jsonl`, `probes.jsonl`, `judgments.jsonl`) |
| **LongMemEval** | Long-term memory of chat assistants over timestamped user-assistant histories | 500 QA instances over five abilities: information extraction, multi-session reasoning, knowledge updates, temporal reasoning, abstention | Test either by giving full history to the system or by running an indexing/retrieval/reading pipeline over released histories | `LongMemEval_S` is about 115k tokens and about 40 history sessions; `LongMemEval_M` is about 500 sessions | QA correctness is evaluated with a provided `gpt-4o` script that writes `autoeval_label`; retrieval is also measured at turn and session level | Public paper, code, datasets, and retrieval baselines are available, but the repo does not define a single frozen benchmark release or a standardized per-run artifact contract like Engram |
| **LoCoMo** | Very long-term conversational memory and comprehension in long dialogues | Three tasks: question answering, event summarization, and multimodal dialogue generation; QA includes multiple reasoning types and evidence spans | Evaluate models with long conversation context or with RAG over released dialogs, observations, and session summaries | Dialogues average about 300 turns and 9k tokens and span up to 35 sessions; current repo release is a 10-conversation subset of the original 50-conversation release | QA results are reported with F1; the benchmark also includes task-specific evaluation for event summarization and multimodal generation | Public paper, project page, code, and annotated data are available, including evidence labels and generated retrieval databases, but it is not packaged as a runtime benchmark harness with fixed run artifacts |
| **MemBench** | Memory capability of LLM-based agents across different memory levels and interaction settings | Covers factual vs reflective memory and participation vs observation scenarios; includes controllable noise to extend information flow length | Can be used either to mimic memory-flow evaluation or as a long-context setup over released data variants | Public repo exposes paper-sampled `0-10k` and `100k` conversation-length datasets and supports additional about-1k-token noise increments | Explicitly targets effectiveness, efficiency, and capacity rather than a single recall score | Public paper, code, and data links are available, but data access relies on external downloads and the public packaging is lighter than Engram's release-plus-artifact workflow |
| **MemoryAgentBench** | Memory agents under incremental multi-turn information accumulation | Reformulates existing datasets into multi-turn interactions and adds EventQA and FactConsolidation; README frames four competencies: accurate retrieval, test-time learning, long-range understanding, and conflict resolution | Uses an "inject once, query multiple times" setup to simulate incremental accumulation rather than a single long prompt | Horizon varies by transformed dataset; the benchmark is designed around chunked multi-turn accumulation instead of one fixed release setting | Uses mixed dataset-specific metrics; the public repo also ships `gpt-4o`-based evaluation paths for LongMemEval and InfBench summarization | Public paper, code, and processed-data download path are available, but there is no single benchmark release policy or auditable run-artifact schema comparable to Engram |

## What Engram Adds Relative To Prior Work

- **Relative to LongMemEval:** Engram moves from long-history QA over released chat logs to runtime-native evaluation after memory ingestion, settling, and fresh-session probing.
- **Relative to LoCoMo:** Engram is less broad in modality and narrative realism, but it is easier to operationalize as a benchmark standard because it fixes protocol, scoring, and output artifacts for outside evaluators.
- **Relative to MemBench:** Engram covers fewer memory dimensions, but it is more opinionated about benchmark comparability: one official release, one canonical protocol, and one audit trail per run.
- **Relative to MemoryAgentBench:** Engram is narrower in competency coverage, but stronger on benchmark packaging for external reproduction and leaderboard-style verification.

## Review-Safe Claim Language

Use claims of this form in the paper and README:

- Engram complements LongMemEval and LoCoMo by evaluating post-context-window recall inside the agent runtime rather than only long-context comprehension over released histories.
- Engram complements MemBench and MemoryAgentBench by prioritizing benchmark comparability, frozen settings, and auditable run artifacts over maximal competency coverage.
- Engram should not be presented as "the most comprehensive" memory benchmark; it should be presented as a reproducible runtime benchmark for long-term agent memory.

## Sources

- Engram benchmark docs: [benchmark_spec.md](./benchmark_spec.md), [evaluation_protocol.md](./evaluation_protocol.md), [benchmark_release_v3.md](./benchmark_release_v3.md), [reproducibility.md](./reproducibility.md)
- LongMemEval paper: [arXiv:2410.10813](https://arxiv.org/abs/2410.10813)
- LongMemEval code and data: [xiaowu0162/LongMemEval](https://github.com/xiaowu0162/LongMemEval)
- LoCoMo paper: [arXiv:2402.17753](https://arxiv.org/abs/2402.17753)
- LoCoMo project page: [snap-research.github.io/locomo](https://snap-research.github.io/locomo/)
- LoCoMo code and data: [snap-research/locomo](https://github.com/snap-research/locomo)
- MemBench paper: [ACL Anthology 2025.findings-acl.989](https://aclanthology.org/2025.findings-acl.989/)
- MemBench code and data links: [import-myself/Membench](https://github.com/import-myself/Membench)
- MemoryAgentBench paper: [arXiv:2507.05257](https://arxiv.org/abs/2507.05257)
- MemoryAgentBench code: [HUST-AI-HYZ/MemoryAgentBench](https://github.com/HUST-AI-HYZ/MemoryAgentBench)

## Notes On Inference

- The `Public artifacts` column includes one explicit inference: whether a benchmark exposes a standardized per-run artifact contract suitable for audit. That assessment is based on the public repo structure and documentation linked above as of March 6, 2026.
- LoCoMo's paper discusses a 50-conversation release, while the current public GitHub dataset page describes a 10-conversation subset retained for evaluation cost and annotation quality. The matrix reflects both facts.
