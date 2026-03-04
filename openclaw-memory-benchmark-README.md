# OpenClaw Memory Benchmark v1

A benchmark dataset for evaluating long-term memory in multi-agent AI assistant systems, derived from real OpenClaw conversation transcripts.

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

## Question Types

| Type | Description | Example |
|------|-------------|---------|
| `temporal-reasoning` | Order/timing of events across sessions | "Which happened first?" |
| `cross-agent-memory` | Facts from sub-agent sessions | "What model does X run on?" |
| `fact-recall` | Specific details from past conversations | "How many entries in the codex?" |
| `multi-hop-reasoning` | Connecting facts across multiple sessions | "Who works at X company?" |
| `recurring-pattern` | System behaviors and patterns | "What triggers the circuit breaker?" |

## Memory Types

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

## Anonymization

All personal and sensitive information has been anonymized:

| Original | Anonymized |
|----------|------------|
| Adii | Alex |
| Ubundi | Beacon Studio |
| Rune | Echo |
| tootoo | codexai |
| Cortex | MemorySync |
| Kwanda | Catalyst |
| rune-x | engage-x |
| runingway | contentway |
| tootoo (sub-agent) | trustalign |
| Real email domains | @beaconstudio.io, @example.com |
| Real names | Peter Chen, Mike Kim |

Credentials, API keys, and other sensitive data have been removed entirely.

## Benchmark Metrics

Evaluate each configuration on:

1. **Accuracy** — Correct answers / Total questions
2. **Precision** — Key facts retrieved correctly
3. **Recall** — Required facts retrieved vs. available
4. **Latency** — Time to answer (relevant for real-time use)
5. **Token efficiency** — Context tokens used per answer

### Scoring by Difficulty

| Difficulty | Weight |
|------------|--------|
| Easy | 1x |
| Medium | 2x |
| Hard | 3x |

## Usage

### Basic Evaluation

```python
import json

with open('openclaw-memory-benchmark-v1.json') as f:
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
```

### Cross-Agent Evaluation

For `cross-agent-memory` questions, ensure the benchmark setup:
1. Loads sessions from multiple agent workspaces
2. Tests whether the main agent can recall sub-agent context
3. Measures context window pressure from multi-agent history

## Question Distribution

| Type | Count | Difficulty Distribution |
|------|-------|------------------------|
| temporal-reasoning | 3 | 1 medium, 2 hard |
| cross-agent-memory | 3 | 1 easy, 2 medium |
| fact-recall | 4 | 2 easy, 2 medium |
| multi-hop-reasoning | 1 | 1 hard |
| recurring-pattern | 1 | 1 medium |

**Total: 12 questions**

## Future Extensions

1. **Longer time spans** — Add 30-day and 90-day memory tests
2. **Higher cardinality** — More sessions per haystack
3. **Contradiction detection** — Conflicting facts across sessions
4. **Preference drift** — Changing user preferences over time
5. **Multi-agent delegation** — Chain of sub-agent handoffs

## Source Data

Generated from 2 weeks of real OpenClaw conversation transcripts:
- 75 session files
- 5 agent types (main, engage-x, contentway, trustalign, worker)
- Feb 19 - Mar 4, 2026

---

*Created: 2026-03-04*
*Version: 1.0*
