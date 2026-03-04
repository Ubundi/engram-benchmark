# OpenClaw Memory Benchmark v2

A comprehensive benchmark dataset for evaluating long-term memory in multi-agent AI assistant systems, derived from real OpenClaw conversation transcripts.

**File size:** ~105KB (comparable to LongMemEval)
**Questions:** 30 test cases
**Session data:** 2 weeks of real multi-agent conversations

## Purpose

This benchmark tests memory capabilities across three configurations:
1. **OpenClaw Native** — No external memory system (baseline)
2. **OpenClaw + Cortex** — Semantic memory with automatic recall
3. **OpenClaw + ClawVault** — Alternative memory architecture (TBD)

## Dataset Structure

Each test case follows the LongMemEval format with OpenClaw-specific extensions:

```json
{
  "question_id": "oc_temporal_001",
  "question_type": "temporal-reasoning",
  "question": "The memory query",
  "answer": "Ground truth answer",
  "question_date": "When the question is asked",
  "haystack_dates": ["Timestamps of relevant sessions"],
  "haystack_session_ids": ["Session identifiers"],
  "haystack_sessions": [
    [{"role": "user", "content": "...", "has_answer": true/false}]
  ],
  "answer_session_ids": ["Sessions containing the answer"],
  "metadata": {
    "agents_involved": ["main", "trustalign", "engage-x"],
    "memory_type": "temporal_ordering|cross_agent_fact|...",
    "difficulty": "easy|medium|hard"
  }
}
```

## Question Distribution

| Type | Count | Description |
|------|-------|-------------|
| `temporal-reasoning` | 5 | Event ordering, duration tracking, staleness detection |
| `cross-agent-memory` | 4 | Facts from sub-agent sessions |
| `fact-recall` | 14 | Specific details (codex, projects, configs, teams) |
| `multi-hop-reasoning` | 2 | Connecting facts across sessions |
| `recurring-pattern` | 1 | System behaviors (circuit breaker) |

**Total: 30 questions**

## Difficulty Distribution

| Difficulty | Count | Weight |
|------------|-------|--------|
| Easy | 6 | 1x |
| Medium | 16 | 2x |
| Hard | 8 | 3x |

**Weighted total: 62 points**

## Memory Types Tested

- `temporal_ordering` — Sequence of events
- `temporal_span` — Duration between events
- `cross_agent_fact` — Information from sub-agent sessions
- `structured_fact` — Organized data (counts, lists, configs)
- `multi_hop_entity` — Entity relationships across sessions
- `system_pattern` — Behavioral patterns
- `system_architecture` — Multi-agent structure
- `staleness_detection` — Detecting missed recurring tasks
- `evaluation_recall` — Past evaluations/scores
- `integration_config` — Technical configuration details
- `lesson_learned` — Corrections and improvements
- `task_detail` — Operational specifics
- `research_summary` — Research findings
- `financial_detail` — Investment/cost information
- `skill_definition` — Skill workflows
- `self_improvement` — Agent self-analysis
- `development_task` — GitHub issues/features
- `product_milestone` — Launch dates, user counts
- `error_correction` — Mistakes and fixes
- `process_definition` — Workflow contracts
- `org_structure` — Team information
- `market_research` — Business opportunities
- `learning_extraction` — Tips from external sources
- `monitoring_summary` — Engagement metrics

## Agents Covered

| Agent | Sessions | Description |
|-------|----------|-------------|
| main (Echo) | 18 | Primary planning agent |
| trustalign | 4 | Alignment observer sub-agent |
| engage-x | 3 | Social platform engagement |
| contentway | 1 | Professional content creation |
| worker | 2 | Low-cost tool execution |

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
| Real names | Peter Chen, Mike Kim, etc. |
| Real credentials | [REMOVED] |

## Key Differentiators from LongMemEval

1. **Multi-agent context** — Tests recall across main + 4 sub-agent sessions
2. **System patterns** — Circuit breakers, staleness detection, recurring tasks
3. **Real operational data** — Not synthetic conversations
4. **Lesson learning** — Error corrections and self-improvement
5. **Cross-session delegation** — Agent spawning and handoffs
6. **Values alignment** — Codex-based alignment checking

## Evaluation Metrics

1. **Accuracy** — Correct answers / Total questions
2. **Precision** — Key facts retrieved correctly
3. **Recall** — Required facts retrieved vs. available
4. **Latency** — Time to answer
5. **Token efficiency** — Context tokens used per answer

## Usage

```python
import json

with open('openclaw-memory-benchmark-v2.json') as f:
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

## Source Data

Generated from 2 weeks of real OpenClaw conversation transcripts:
- 75 session files
- 5 agent types
- Feb 16 - Mar 4, 2026
- ~105KB of test data

---

*Created: 2026-03-04*
*Version: 2.0*
