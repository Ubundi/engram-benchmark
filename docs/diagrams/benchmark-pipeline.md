# Benchmark Pipeline

## General Pipeline

All conditions follow the same four-phase pipeline. Condition-specific behavior is injected at well-defined points within each phase.

```mermaid
flowchart TD
    START([benchmark.run]) --> LOAD[Load tasks from split<br/><i>test: 50 tasks, v3: 498 tasks</i>]
    LOAD --> ADAPTER[Initialize adapter<br/><i>OpenClaw CLI</i>]
    ADAPTER --> PREFLIGHT{Condition?}

    PREFLIGHT -->|cortex| PF_CORTEX[Cortex preflight<br/><i>openclaw cortex status</i><br/>Verify API health, 0 memories]
    PREFLIGHT -->|baseline / other| PF_SKIP[Skip preflight]
    PF_CORTEX --> SEED
    PF_SKIP --> SEED

    subgraph PHASE1 [Phase 1: Seed]
        SEED[For each task 1..N] --> SESSIONS[For each haystack session]
        SESSIONS --> DATE_INJ{Cortex?}
        DATE_INJ -->|yes| INJ_DATE[Inject date context<br/>into first user turn]
        DATE_INJ -->|no| NO_INJ[Send turns as-is]
        INJ_DATE --> TURNS
        NO_INJ --> TURNS
        TURNS[Send each user turn<br/><i>openclaw agent --message</i>] --> FLUSH{--flush-sessions?}
        FLUSH -->|yes| NEW[Send /new<br/><i>Triggers session-memory hook</i>]
        FLUSH -->|no| NEXT
        NEW --> HOOK[session-memory hook writes<br/>workspace/memory/*.md files]
        HOOK --> NEXT[Next session]
        NEXT --> SESSIONS
    end

    PHASE1 --> SETTLE

    subgraph PHASE2 [Phase 2: Settle]
        SETTLE{Condition?}
        SETTLE -->|baseline| S10[Wait 10s]
        SETTLE -->|cortex| S180[Wait 180s<br/><i>Async Cortex ingest:<br/>extraction + embedding + graph</i>]
        SETTLE -->|mem0| S60[Wait 60s]
    end

    PHASE2 --> REINDEX

    subgraph REINDEX_PHASE [Reindex]
        REINDEX[openclaw memory index<br/><i>Rebuild memory-core index<br/>All conditions</i>]
    end

    REINDEX_PHASE --> PROBE

    subgraph PHASE3 [Phase 3: Probe]
        PROBE[For each task 1..N] --> NEW_SESSION[Send /new<br/><i>Isolate probe session</i>]
        NEW_SESSION --> PROBE_DATE{Cortex?}
        PROBE_DATE -->|yes| ADD_DATE[Prepend cortex-date tag]
        PROBE_DATE -->|no| NO_DATE[Send question as-is]
        ADD_DATE --> ASK
        NO_DATE --> ASK
        ASK[Send probe question<br/><i>openclaw agent --message</i>]
        ASK --> AGENT_TOOLS

        subgraph AGENT_TOOLS [Agent has access to]
            direction LR
            MC_SEARCH[memory_search<br/><i>memory-core</i>]
            MC_GET[memory_get<br/><i>memory-core</i>]
            CORTEX_SEARCH[cortex_search_memory<br/><i>cortex only</i>]
            CORTEX_SAVE[cortex_save_memory<br/><i>cortex only</i>]
        end

        AGENT_TOOLS --> COLLECT[Collect response + metadata]
    end

    PHASE3 --> JUDGE

    subgraph PHASE4 [Phase 4: Judge]
        JUDGE[For each prediction] --> SCORE[GPT-4.1-mini scores 0-3<br/><i>3 passes, temp 0.3</i>]
        SCORE --> AGG[Aggregate: mean of pass scores]
    end

    PHASE4 --> EVAL

    subgraph EVAL_PHASE [Evaluation]
        EVAL[Compute metrics] --> QA[qa.mean_score<br/>qa.exact_match<br/>qa.category.*]
        EVAL --> RET[retrieval.hit_rate]
        EVAL --> ABS[abstain.rate]
    end

    EVAL_PHASE --> REPORT[Write artifacts<br/><i>predictions.jsonl, judgments.jsonl,<br/>run_metadata.json, report.md</i>]
    REPORT --> DONE([Run complete])
```

## Baseline Condition

The baseline measures memory-core (OpenClaw's built-in memory system) in isolation. No external memory service is involved.

```mermaid
flowchart LR
    subgraph SEED [Seed Phase]
        direction TB
        S1[User turns sent<br/>to OpenClaw agent] --> S2[/new flushes session]
        S2 --> S3[session-memory hook<br/>extracts summaries]
        S3 --> S4[Writes workspace/memory/*.md]
    end

    subgraph SETTLE [Settle: 10s]
        direction TB
        W1[Brief wait for<br/>file I/O completion]
    end

    subgraph REINDEX [Reindex]
        direction TB
        R1[openclaw memory index]
        R1 --> R2[Embeds memory files<br/>text-embedding-3-small]
        R2 --> R3[Stores in SQLite<br/>main.sqlite]
    end

    subgraph PROBE [Probe Phase]
        direction TB
        P1[/new — fresh session] --> P2[Question sent to agent]
        P2 --> P3{Agent decides}
        P3 -->|search| P4[memory_search<br/><i>semantic over indexed .md</i>]
        P3 -->|read| P5[memory_get<br/><i>read specific file/lines</i>]
        P3 -->|no tool| P6[Answer from<br/>system prompt context]
        P4 --> P7[Response]
        P5 --> P7
        P6 --> P7
    end

    SEED --> SETTLE --> REINDEX --> PROBE
```

### Memory flow

```mermaid
flowchart TD
    CONV[Seed conversation] -->|/new| HOOK[session-memory hook]
    HOOK --> MD[workspace/memory/<br/>2026-03-16-topic.md]
    MD -->|reindex| SQLITE[(main.sqlite<br/>vector + FTS index)]
    SQLITE -->|memory_search| AGENT[Agent probe session]
    MD -->|memory_get| AGENT
```

## Cortex Condition

The cortex condition adds Cortex (server-side long-term memory) on top of memory-core. The agent has access to both memory systems during probes.

```mermaid
flowchart LR
    subgraph SEED [Seed Phase]
        direction TB
        S1[User turns sent with<br/>date context injected] --> S2[/new flushes session]
        S2 --> S3[session-memory hook<br/>writes workspace/memory/*.md]
        S2 --> S4[Cortex auto-capture hook<br/>extracts facts to server]
    end

    subgraph SETTLE [Settle: 180s]
        direction TB
        W1[Cortex async pipeline]
        W1 --> W2[Extraction]
        W2 --> W3[Embedding]
        W3 --> W4[Graph build]
    end

    subgraph REINDEX [Reindex]
        direction TB
        R1[openclaw memory index<br/><i>memory-core files</i>]
    end

    subgraph PROBE [Probe Phase]
        direction TB
        P0[/new — fresh session] --> P0A[Cortex auto-recall<br/>injects memories block]
        P0A --> P1[Question with<br/>cortex-date tag]
        P1 --> P2{Agent decides}
        P2 -->|memory-core| P3[memory_search / memory_get]
        P2 -->|cortex| P4[cortex_search_memory]
        P2 -->|no tool| P5[Answer from context<br/>+ auto-recalled memories]
        P3 --> P6[Response]
        P4 --> P6
        P5 --> P6
    end

    SEED --> SETTLE --> REINDEX --> PROBE
```

### Dual memory architecture

```mermaid
flowchart TD
    CONV[Seed conversation] -->|/new| HOOK_LOCAL[session-memory hook]
    CONV -->|agent_end| HOOK_CORTEX[Cortex auto-capture]

    HOOK_LOCAL --> MD[workspace/memory/*.md]
    HOOK_CORTEX --> API[Cortex API /v1/jobs/ingest]

    MD -->|reindex| SQLITE[(main.sqlite)]
    API -->|async pipeline| CORTEX_DB[(Cortex server<br/>memories + graph)]

    subgraph PROBE_SESSION [Probe session]
        direction TB
        NEW[/new] --> AUTO_RECALL[Cortex auto-recall<br/>/v1/recall]
        AUTO_RECALL --> INJECT["&lt;cortex_memories&gt; block<br/>prepended to prompt"]
        INJECT --> QUESTION[Probe question]
        QUESTION --> AGENT{Agent}
    end

    SQLITE -->|memory_search| AGENT
    MD -->|memory_get| AGENT
    CORTEX_DB -->|cortex_search_memory| AGENT
    CORTEX_DB -->|auto-recall| AUTO_RECALL
```

## Judge Scoring Rubric

```mermaid
flowchart LR
    subgraph SCORES [Score Definitions]
        direction TB
        S3["**3 — Grounded recall**<br/>Correct, specific, matches ground truth"]
        S2["**2 — Partial recall**<br/>Directionally correct but missing key details"]
        S1["**1 — Abstained**<br/>Declined to answer / said 'I don't know'"]
        S0["**0 — Hallucinated**<br/>Stated incorrect facts with confidence"]
    end

    PRED[Agent prediction] --> JUDGE[GPT-4.1-mini]
    GT[Ground truth] --> JUDGE
    JUDGE -->|pass 1| S_A[Score]
    JUDGE -->|pass 2| S_B[Score]
    JUDGE -->|pass 3| S_C[Score]
    S_A --> MEAN[Mean of 3 passes]
    S_B --> MEAN
    S_C --> MEAN
```

## Condition Comparison

| Aspect | Baseline | Cortex |
|--------|----------|--------|
| Memory write | session-memory hook only | session-memory + Cortex auto-capture |
| Memory storage | Local .md files + SQLite index | Local files + Cortex server (cloud) |
| Settle time | 10s | 180s (async ingest pipeline) |
| Auto-recall injection | No | Yes (before each turn) |
| Date context in seeds | No | Yes (haystack_dates injected) |
| Date context in probes | No | Yes (cortex-date tag) |
| Tools available | memory_search, memory_get | memory_search, memory_get, cortex_search_memory, cortex_save_memory |
| Preflight check | None | Cortex status verified |
