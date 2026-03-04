# Submission Format

## Purpose

Define a reproducible submission payload for benchmark ranking and audit.

## Required metadata

Each submission must include:
- `submission_id`: unique submission identifier
- `run_id`: run directory identifier
- `agent_name`: evaluated system name
- `agent_version`: version, image tag, or commit SHA
- `timestamp_utc`: ISO-8601 timestamp
- `task_split`: evaluated split or dataset identifier
- `metrics`: numeric metrics object

## Required companion artifacts

A valid submission must also provide (or reference) these files:
- `run_metadata.json`
- `metrics.json`
- `predictions.jsonl`
- protocol-specific evidence (for V2: `probes.jsonl`, `judgments.jsonl`)

## Submission JSON schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LeaderboardSubmission",
  "type": "object",
  "required": [
    "submission_id",
    "run_id",
    "agent_name",
    "agent_version",
    "timestamp_utc",
    "task_split",
    "metrics"
  ],
  "properties": {
    "submission_id": { "type": "string", "minLength": 1 },
    "run_id": { "type": "string", "minLength": 1 },
    "agent_name": { "type": "string", "minLength": 1 },
    "agent_version": { "type": "string", "minLength": 1 },
    "timestamp_utc": { "type": "string", "format": "date-time" },
    "task_split": { "type": "string", "minLength": 1 },
    "metrics": {
      "type": "object",
      "minProperties": 1,
      "additionalProperties": { "type": "number" }
    },
    "artifacts": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "notes": { "type": "string" }
  },
  "additionalProperties": false
}
```

## Validation rules

- Submissions without required fields are invalid.
- Metric keys must match documented protocol metrics.
- Submission must be reproducible from attached artifacts.
- Any known run failures must be disclosed in `notes`.
