"""Task loader for the Engram benchmark dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmark.tasks.openclaw import load_openclaw_records, normalize_openclaw_tasks
from benchmark.tasks.schemas import validate_task_dict
from benchmark.utils.io import read_jsonl


def _fetch_from_hf(test: bool = False) -> Path:
    from benchmark.tasks.hf import fetch_engram_dataset, fetch_engram_test_dataset

    return fetch_engram_test_dataset() if test else fetch_engram_dataset()


def _read_tasks(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return read_jsonl(path)
    if path.suffix == ".json":
        return normalize_openclaw_tasks(load_openclaw_records(path))
    raise ValueError(f"Unsupported task file extension for {path}. Use .jsonl or .json")


def load_tasks(
    split: str = "v3",
    data_path: str | None = None,
    max_tasks: int | None = None,
) -> list[dict[str, Any]]:
    if data_path:
        path = Path(data_path)
        if not path.exists():
            raise FileNotFoundError(f"Task file not found: {path}")
    else:
        # Check for a local JSONL override (useful for CI sample splits)
        root = Path(__file__).resolve().parents[2]
        local_jsonl = root / "data" / "splits" / f"{split}.jsonl"
        local_sample = root / "data" / "splits" / f"{split}.sample.jsonl"
        if local_jsonl.exists():
            path = local_jsonl
        elif local_sample.exists():
            path = local_sample
        else:
            # Fall back to HuggingFace
            path = _fetch_from_hf(test=(split == "test"))

    tasks = _read_tasks(path)
    validated: list[dict[str, Any]] = []
    for task in tasks:
        validate_task_dict(task)
        validated.append(task)

    if max_tasks is not None:
        return validated[:max_tasks]
    return validated
