"""Validate sample tasks against the task schema."""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.tasks.schemas import load_task_schema, validate_task_dict


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_sample_tasks_validate_against_schema() -> None:
    root = Path(__file__).resolve().parents[1]
    schema = load_task_schema()
    required = set(schema.get("required", []))

    for split in ("dev.sample.jsonl", "test.sample.jsonl", "v2.sample.jsonl"):
        tasks = _load_jsonl(root / "data" / "splits" / split)
        assert tasks, f"Expected at least one task in {split}"
        for task in tasks:
            assert required.issubset(task.keys())
            validate_task_dict(task)
