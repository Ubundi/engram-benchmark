"""Tests for loading legacy OpenClaw V2 benchmark format."""

from __future__ import annotations

from pathlib import Path

from benchmark.tasks.loader import load_tasks


def test_load_legacy_v2_json() -> None:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "openclaw-memory-benchmark-v2.json"

    tasks = load_tasks(split="v2", data_path=str(data_path), max_tasks=2)

    assert len(tasks) == 2
    assert tasks[0]["id"]
    assert tasks[0]["input"]
    assert tasks[0]["reference_answer"]
    assert tasks[0]["metadata"]["source_format"] == "openclaw_v2_legacy"


def test_load_v2_split_sample_jsonl() -> None:
    tasks = load_tasks(split="v2", data_path=None, max_tasks=2)

    assert len(tasks) == 2
    assert all("id" in task for task in tasks)
    assert all("input" in task for task in tasks)
    assert all("reference_answer" in task for task in tasks)
