"""Task loader for the Engram benchmark dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmark.tasks.openclaw import load_openclaw_records, normalize_openclaw_tasks
from benchmark.tasks.schemas import validate_task_dict
from benchmark.utils.io import read_jsonl

_FULL_SPLIT_ALIASES = {"v3", "engram-v3", "engram-v3.json"}
_TEST_SPLIT_ALIASES = {"test", "engram-v3-test", "engram-v3-test.json"}


def _fetch_from_hf(test: bool = False) -> Path:
    from benchmark.tasks.hf import fetch_engram_dataset, fetch_engram_test_dataset

    return fetch_engram_test_dataset() if test else fetch_engram_dataset()


def _read_tasks(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return read_jsonl(path)
    if path.suffix == ".json":
        return normalize_openclaw_tasks(load_openclaw_records(path))
    raise ValueError(f"Unsupported task file extension for {path}. Use .jsonl or .json")


def _canonicalize_split(split: str) -> str:
    normalized = split.strip().lower()
    if normalized in _FULL_SPLIT_ALIASES:
        return "v3"
    if normalized in _TEST_SPLIT_ALIASES:
        return "test"
    return split


def load_tasks(
    split: str = "v3",
    data_path: str | None = None,
    max_tasks: int | None = None,
) -> list[dict[str, Any]]:
    resolved_split = _canonicalize_split(split)

    if data_path:
        path = Path(data_path)
        if not path.exists():
            raise FileNotFoundError(f"Task file not found: {path}")
    else:
        # "test" is a named HF split — always fetch from HuggingFace.
        # For other splits, check for a local JSONL override first (useful for CI).
        root = Path(__file__).resolve().parents[2]
        local_jsonl = root / "data" / "splits" / f"{resolved_split}.jsonl"
        local_sample = root / "data" / "splits" / f"{resolved_split}.sample.jsonl"
        if resolved_split != "test" and local_jsonl.exists():
            path = local_jsonl
        elif resolved_split != "test" and local_sample.exists():
            path = local_sample
        else:
            # Fall back to HuggingFace
            path = _fetch_from_hf(test=(resolved_split == "test"))

    tasks = _read_tasks(path)
    validated: list[dict[str, Any]] = []
    for task in tasks:
        validate_task_dict(task)
        validated.append(task)

    if max_tasks is not None:
        return validated[:max_tasks]
    return validated
