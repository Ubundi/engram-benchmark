from __future__ import annotations

import json
from pathlib import Path

from benchmark.config import RunConfig
from benchmark.tasks import loader


def _write_openclaw_dataset(path: Path, question_id: str) -> None:
    payload = [
        {
            "question_id": question_id,
            "question": f"What is {question_id}?",
            "answer": f"Answer for {question_id}",
            "question_type": "fact-recall",
            "question_date": "2026-03-01",
            "haystack_dates": ["2026-02-28"],
            "haystack_session_ids": ["session-1"],
            "answer_session_ids": ["session-1"],
            "haystack_sessions": [
                [
                    {"role": "user", "content": "Seed fact"},
                    {"role": "assistant", "content": "Stored"},
                ]
            ],
            "metadata": {"source": "test"},
        }
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_run_config_defaults_to_v3() -> None:
    assert RunConfig(agent="local_stub").split == "v3"


def test_canonicalize_split_supports_engram_v3_aliases() -> None:
    assert loader._canonicalize_split("v3") == "v3"
    assert loader._canonicalize_split("engram-v3") == "v3"
    assert loader._canonicalize_split("engram-v3.json") == "v3"
    assert loader._canonicalize_split("test") == "test"
    assert loader._canonicalize_split("engram-v3-test") == "test"
    assert loader._canonicalize_split("engram-v3-test.json") == "test"


def test_load_tasks_supports_engram_v3_test_aliases(tmp_path: Path, monkeypatch) -> None:
    test_path = tmp_path / "engram-v3-test.json"
    _write_openclaw_dataset(test_path, "test-task")

    monkeypatch.setattr(
        loader,
        "_fetch_from_hf",
        lambda test=False: test_path,
    )

    test_tasks = loader.load_tasks(split="engram-v3-test")
    test_json_tasks = loader.load_tasks(split="engram-v3-test.json")

    assert test_tasks[0]["id"] == "test-task"
    assert test_json_tasks[0]["id"] == "test-task"
