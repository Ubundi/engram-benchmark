# OpenClaw Memory Benchmark v3

A comprehensive benchmark dataset for evaluating long-term memory in multi-agent AI assistant systems, derived from real OpenClaw conversation transcripts and expanded with realistic generated sessions.

**File size:** ~10-15 MB (comparable to LongMemEval)
**Questions:** 500 test cases across 8 question types
**Session data:** 4 weeks of multi-agent conversations (Feb 19 - Mar 18, 2026)
**Sessions:** ~300 unique sessions, avg 11+ messages per session

## What's New in v3

- **500 questions** (up from 29 in v2) across **8 question types** (up from 5)
- **4-week date range** (up from 2 weeks) capturing rapid AI startup evolution
- **~300 sessions** with avg 11+ messages each (up from 2.2 in v2)
- **Knowledge updates**: Facts that change over time (metrics shift, configs evolve, decisions reverse)
- **Temporal complexity**: Agent configs change mid-week, project statuses update frequently
- **6 new memory types**: knowledge_update, config_change, decision_reversal, metric_drift, strategy_shift, agent_evolution
- **All 29 v2 questions preserved** with enriched session contexts

## Purpose

This benchmark tests memory capabilities across three configurations:
1. **OpenClaw Native** — No external memory system (baseline)
2. **OpenClaw + Cortex** — Semantic memory with automatic recall
3. **OpenClaw + ClawVault** — Alternative memory architecture

## Dataset Structure

Each test case follows the LongMemEval format with OpenClaw-specific extensions:

```json
{
  "question_id": "oc_temporal_001",
  "question_type": "temporal-reasoning",
  "question": "The memory query",
  "answer": "Ground truth answer",
  "question_date": "2026/03/19 (Thu) 15:00",
  "haystack_dates": ["Timestamps of relevant sessions"],
  "haystack_session_ids": ["Session identifiers"],
  "haystack_sessions": [
    [{"role": "user", "content": "...", "has_answer": true/false}]
  ],
  "answer_session_ids": ["Sessions containing the answer"],
  "metadata": {
    "agents_involved": ["main", "trustalign"],
    "memory_type": "temporal_ordering",
    "difficulty": "easy|medium|hard"
  }
}
```

## Question Types (8)

| Type | Count | Description |
|------|-------|-------------|
| `temporal-reasoning` | 80 | Event ordering, duration tracking, staleness detection |
| `multi-session` | 80 | Synthesizing information across 3+ sessions |
| `knowledge-update` | 55 | Facts that changed over time |
| `single-session-user` | 45 | Facts stated by the user |
| `single-session-assistant` | 35 | Facts provided by the assistant |
| `cross-agent-memory` | 80 | Facts from sub-agent sessions |
| `multi-hop-reasoning` | 70 | Chaining 2-4 facts via entity links |
| `recurring-pattern` | 55 | System behaviors, heartbeats, circuit breakers |

**Total: 500 questions**

## Difficulty Distribution

| Difficulty | Count | Weight | Total Points |
|------------|-------|--------|--------------|
| Easy | 100 | 1x | 100 |
| Medium | 250 | 2x | 500 |
| Hard | 150 | 3x | 450 |
| **Total** | **500** | — | **1,050 points** |

## Memory Types (30)

**Existing (24 from v2):**
temporal_ordering, temporal_span, staleness_detection, cross_agent_fact, multi_hop_entity, system_architecture, structured_fact, org_structure, integration_config, process_definition, skill_definition, task_detail, product_milestone, financial_detail, market_research, development_task, research_summary, evaluation_recall, lesson_learned, self_improvement, error_correction, monitoring_summary, system_pattern, operational_detail

**New in v3 (6):**
knowledge_update, config_change, decision_reversal, metric_drift, strategy_shift, agent_evolution

## Agents Covered

| Agent | Role | Model | Sessions |
|-------|------|-------|----------|
| **main** (Echo) | Primary planner | Claude Opus | ~135 |
| **engage-x** | Social engagement | Sonnet 4.5 | ~54 |
| **contentway** | Content creation | Sonnet 4.5 | ~30 |
| **trustalign** | Alignment observer | Sonnet 4.5 | ~45 |
| **worker** | Tool execution | GLM-4.7 | ~36 |

## 4-Week Timeline

| Week | Dates | Theme | Key Changes |
|------|-------|-------|-------------|
| Week 1 | Feb 19-25 | System setup & launch | TrustAlign created, CodexAI live, browser issues start |
| Week 2 | Feb 26 - Mar 4 | Operational maturity | Circuit breaker, worker output contract, self-improvement |
| Week 3 | Mar 5-11 | Rapid iteration | MemorySync benchmarks, agent config changes, CodexAI pivots |
| Week 4 | Mar 12-18 | Course correction | Lessons learned, architecture review, strategy shifts |

## Anonymization

All personal and sensitive information has been anonymized:

| Original | Anonymized |
|----------|------------|
| Adii | Alex |
| Ubundi | Beacon Studio |
| Rune | Echo |
| tootoo | CodexAI |
| Cortex | MemorySync |
| Kwanda | Catalyst |
| rune-x | engage-x |
| runingway | contentway |
| tootoo (sub-agent) | trustalign |
| Real email domains | @beaconstudio.io |
| Real credentials | [REMOVED] |

## Key Differentiators from LongMemEval

1. **Multi-agent context** — Tests recall across main + 4 sub-agent sessions
2. **Knowledge updates** — Facts change over time, testing staleness awareness
3. **System patterns** — Circuit breakers, retry policies, recurring tasks
4. **Real operational data** — Based on real multi-agent conversations
5. **Temporal complexity** — Fast-moving AI startup with weekly pivots
6. **Cross-session delegation** — Agent spawning and handoffs
7. **Values alignment** — Codex-based alignment checking (TrustAlign)
8. **8 question types** vs LongMemEval's 5

## Evaluation Metrics

1. **Accuracy** — Correct answers / Total questions
2. **Precision** — Key facts retrieved correctly
3. **Recall** — Required facts retrieved vs. available
4. **Latency** — Time to answer
5. **Token efficiency** — Context tokens used per answer

**Weighted scoring:**
```python
weight = {'easy': 1, 'medium': 2, 'hard': 3}[difficulty]
weighted_score = accuracy * weight
total = sum(weighted_scores) / max_possible_points
```

## Usage

```python
import json

with open('openclaw-memory-benchmark-v3.json') as f:
    benchmark = json.load(f)

for test_case in benchmark:
    # Inject haystack_sessions as context
    context = flatten_sessions(test_case['haystack_sessions'])

    # Query the system
    response = query_memory_system(
        question=test_case['question'],
        context=context
    )

    # Evaluate against ground truth
    score = evaluate(response, test_case['answer'])

    # Weight by difficulty
    weight = {'easy': 1, 'medium': 2, 'hard': 3}[test_case['metadata']['difficulty']]
    weighted_score = score * weight
```

## Generation Pipeline

The v3 benchmark was generated using a reusable Python pipeline:

```bash
# Generate everything (requires ANTHROPIC_API_KEY)
python -m scripts.generate_v3

# Use cached sessions (skip API calls for sessions)
python -m scripts.generate_v3 --skip-sessions

# Validate existing output
python -m scripts.generate_v3 --validate-only

# Print statistics
python -m scripts.generate_v3 --stats-only
```

### Pipeline Phases:
1. **Entity Registry** — Load seed entities, track fact consistency
2. **Session Generation** — 300 sessions via Claude API with entity-aware context
3. **Question Generation** — 500 questions using 8 type-specific strategies
4. **Validation** — 10 automated checks (schema, grounding, distributions, etc.)
5. **Export** — Final JSON output
6. **Statistics** — Comparison against LongMemEval targets

## Validation Checks

The pipeline runs 10 automated validation checks:

1. Schema validation (all required fields present)
2. Answer grounding (every answer supported by has_answer=true messages)
3. Session consistency (no empty messages, valid roles)
4. Cross-reference integrity (answer_session_ids ⊆ haystack_session_ids)
5. Distribution checks (question types, difficulties match targets)
6. Deduplication (no duplicate or near-duplicate questions)
7. Length checks (messages, answers, questions within ranges)
8. Date consistency (chronological order, valid formats)
9. Entity consistency (facts in answers exist in sessions)
10. Anonymization safety (no sensitive data leaked)

## Source Data

- **v2 base:** 29 questions from real OpenClaw transcripts (preserved)
- **Generated:** ~471 new questions against ~300 generated sessions
- **Date range:** Feb 19 - Mar 18, 2026 (4 weeks)
- **5 agent types**, 8 session types, 30 memory types
- **~10-15 MB** of test data

---

*Created: 2026-03-04*
*Version: 3.0*
