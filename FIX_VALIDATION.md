# Fix Validation Failures in v3 Benchmark

The generated `openclaw-memory-benchmark-v3.json` (517 questions after anonymization) has **3 failing validation checks** out of 10. This document describes each failure and how to fix it.

**Target file:** `openclaw-memory-benchmark-v3.json`
**Validation command:** `python3 -m scripts.generate_v3 --validate-only`

---

## Failure 1: Answer Grounding (16 questions)

### Problem

16 questions have no message with `has_answer: true` in any of their `haystack_sessions`. The validator requires at least one message to be marked as containing the answer.

### Affected question IDs

```
oc_cross_agent_006
oc_cross_agent_025
oc_cross_agent_028
oc_cross_agent_031
oc_cross_agent_044
oc_cross_agent_064
oc_cross_agent_071
oc_knowledge_update_031
oc_knowledge_update_032
oc_knowledge_update_041
oc_knowledge_update_050
oc_multi_session_009
oc_single_asst_005
oc_single_asst_011
oc_single_asst_025
oc_single_asst_028
```

### How to fix

For each question ID above:

1. Read the question's `answer` field.
2. Search through `haystack_sessions` for the message(s) whose `content` contains or supports that answer.
3. Set `has_answer: true` on that message.

Each message in a session has this structure:
```json
{
  "role": "user" | "assistant",
  "content": "...",
  "has_answer": false
}
```

Change `has_answer` from `false` to `true` on the message(s) that contain the answer evidence.

**If no message in the sessions actually contains the answer**, the question itself is broken — delete it from the array entirely.

### Validation check (from `validate_v3.py` line 192-218)

The check iterates every message in every session and looks for at least one `msg.get("has_answer", False) == True`.

---

## Failure 2: Invalid Session Roles (14 questions)

### Problem

14 questions contain messages with `role: "prioritize_request"` instead of the only valid values: `"user"` or `"assistant"`. This is a hallucinated role value from the LLM that generated the sessions.

### Affected questions and locations

| question_id | session index | message index |
|---|---|---|
| `oc_knowledge_update_006` | 1 | 5 |
| `oc_knowledge_update_012` | 3 | 5 |
| `oc_knowledge_update_027` | 3 | 5 |
| `oc_multi_hop_002` | 4 | 5 |
| `oc_multi_hop_004` | 1 | 5 |
| `oc_multi_hop_058` | 4 | 5 |
| `oc_multi_session_026` | 1 | 5 |
| `oc_recurring_001` | 3 | 5 |
| `oc_recurring_004` | 0 | 5 |
| `oc_recurring_028` | 3 | 5 |
| `oc_recurring_046` | 1 | 5 |
| `oc_recurring_048` | 3 | 5 |
| `oc_single_asst_006` | 0 | 5 |
| `oc_temporal_004` | 2 | 5 |

### How to fix

For each row above, navigate to `question.haystack_sessions[session_index][message_index]` and change the `role` field to `"user"`.

These messages read like user requests (e.g., "prioritize the fixes", "give me a sequenced plan"), so `"user"` is the correct role. Example of an affected message:

```json
{
  "role": "prioritize_request",   // <-- change to "user"
  "content": "Okay, that's clear. Given we're mid-sprint...",
  "has_answer": false
}
```

A script to do this automatically:

```python
import json

with open("openclaw-memory-benchmark-v3.json") as f:
    data = json.load(f)

for q in data:
    for session in q.get("haystack_sessions", []):
        for msg in session:
            if msg.get("role") not in ("user", "assistant"):
                msg["role"] = "user"

with open("openclaw-memory-benchmark-v3.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Validation check (from `validate_v3.py` line 240-242)

```python
if msg.get("role") not in ("user", "assistant"):
    r.error(...)
```

---

## Failure 3: Duplicate Questions (6 exact + 9 near-duplicates)

### Problem

**6 exact duplicate IDs** — two questions share the same `question_id`:

| Duplicate `question_id` | Occurrences |
|---|---|
| `oc_cross_agent_001` | 2 |
| `oc_cross_agent_002` | 2 |
| `oc_multi_hop_001` | 2 |
| `oc_recurring_001` | 2 |
| `oc_temporal_001` | 2 |
| `oc_temporal_002` | 2 |

These are likely v2-preserved questions that also got regenerated in v3. One copy of each pair should be removed.

**9 near-duplicate pairs** (similarity >= 0.85) — these are questions with nearly identical text:

| Question A | Question B | Similarity |
|---|---|---|
| `oc_cross_agent_001` | `oc_cross_agent_037` | 1.00 |
| `oc_cross_agent_001` | `oc_cross_agent_066` | 1.00 |
| `oc_cross_agent_002` | `oc_cross_agent_015` | 0.95 |
| `oc_cross_agent_011` | `oc_cross_agent_065` | 0.91 |
| `oc_cross_agent_026` | `oc_cross_agent_040` | 0.92 |
| `oc_cross_agent_037` | `oc_cross_agent_066` | 1.00 |
| `oc_cross_agent_039` | `oc_cross_agent_073` | 0.93 |
| `oc_knowledge_update_005` | `oc_knowledge_update_046` | 0.85 |
| `oc_knowledge_update_028` | `oc_knowledge_update_048` | 0.90 |

### How to fix

**Step 1 — Remove exact ID duplicates:**

For each duplicate ID pair, keep the **first** occurrence and delete the second. If one of the two is a v2-preserved question (check `openclaw-memory-benchmark-v2.json`), keep the v2 version.

**Step 2 — Remove near-duplicates:**

For each near-duplicate pair, compare the two questions and delete the lower-quality one (shorter sessions, fewer details, or less specific answer). If both are equal quality, delete the one with the higher-numbered ID.

Questions to delete (the "B" side in most cases):

```
oc_cross_agent_037   (duplicate of 001, similarity 1.00)
oc_cross_agent_066   (duplicate of 001, similarity 1.00)
oc_cross_agent_015   (near-dup of 002, similarity 0.95)
oc_cross_agent_065   (near-dup of 011, similarity 0.91)
oc_cross_agent_040   (near-dup of 026, similarity 0.92)
oc_cross_agent_073   (near-dup of 039, similarity 0.93)
oc_knowledge_update_046  (near-dup of 005, similarity 0.85)
oc_knowledge_update_048  (near-dup of 028, similarity 0.90)
```

**Step 3 — Re-number remaining question IDs** (optional but recommended):

After removing duplicates, the IDs will have gaps. You may re-number sequentially per type (e.g., `oc_cross_agent_001` through `oc_cross_agent_0XX`).

A script to remove exact duplicates:

```python
import json

with open("openclaw-memory-benchmark-v3.json") as f:
    data = json.load(f)

seen_ids = set()
deduped = []
for q in data:
    qid = q["question_id"]
    if qid not in seen_ids:
        seen_ids.add(qid)
        deduped.append(q)

print(f"Removed {len(data) - len(deduped)} exact duplicates")

with open("openclaw-memory-benchmark-v3.json", "w") as f:
    json.dump(deduped, f, indent=2)
```

### Validation check (from `validate_v3.py` line 351-385)

- Exact duplicates: counts occurrences of each `question_id`
- Near-duplicates: uses `difflib.SequenceMatcher` on lowercased `question` text, threshold from `config.VALIDATION["dedup_similarity_threshold"]`

---

## Recommended fix order

1. **Fix invalid roles** (Failure 2) — safest, purely mechanical
2. **Remove duplicates** (Failure 3) — straightforward deletion
3. **Fix answer grounding** (Failure 1) — requires reading content to find the right message

## Verifying fixes

After applying all fixes, run:

```bash
python3 -m scripts.generate_v3 --validate-only
```

All 10 checks should pass. The target is **0 errors**. Warnings are acceptable.
