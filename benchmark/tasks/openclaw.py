"""Normalization helpers for OpenClaw benchmark JSON format."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REQUIRED_KEYS = {"question_id", "question", "answer"}


def _format_context_snippets(task: dict[str, Any], max_snippets: int = 3) -> list[str]:
    snippets: list[str] = []
    haystack_sessions = task.get("haystack_sessions")
    if not isinstance(haystack_sessions, list):
        return snippets

    for session in haystack_sessions[:max_snippets]:
        if not isinstance(session, list):
            continue
        parts: list[str] = []
        for turn in session:
            if not isinstance(turn, dict):
                continue
            role = str(turn.get("role", "unknown"))
            content = str(turn.get("content", "")).strip()
            if not content:
                continue
            parts.append(f"{role}: {content}")
            if len(parts) >= 2:
                break
        if parts:
            snippets.append(" | ".join(parts))
    return snippets


def normalize_openclaw_task(task: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(_REQUIRED_KEYS - task.keys())
    if missing:
        raise ValueError(f"OpenClaw task is missing required keys: {missing}")

    metadata = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    context_snippets = _format_context_snippets(task)

    canonical_task: dict[str, Any] = {
        "id": str(task["question_id"]),
        "input": str(task["question"]),
        "reference_answer": str(task["answer"]),
        "metadata": {
            "source_format": "openclaw_v3",
            "question_type": task.get("question_type"),
            "question_date": task.get("question_date"),
            "haystack_dates": task.get("haystack_dates", []),
            "haystack_session_ids": task.get("haystack_session_ids", []),
            "answer_session_ids": task.get("answer_session_ids", []),
            "haystack_sessions": task.get("haystack_sessions", []),
            "source_metadata": metadata,
            "context_snippets": context_snippets,
        },
    }
    return canonical_task


def normalize_openclaw_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("OpenClaw task entries must be JSON objects")
        normalized.append(normalize_openclaw_task(task))
    return normalized


def load_openclaw_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"OpenClaw task file must contain a JSON list: {path}")

    records: list[dict[str, Any]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise ValueError("OpenClaw task entries must be JSON objects")
        missing = sorted(_REQUIRED_KEYS - entry.keys())
        if missing:
            raise ValueError(f"OpenClaw task is missing required keys: {missing}")
        records.append(entry)
    return records
