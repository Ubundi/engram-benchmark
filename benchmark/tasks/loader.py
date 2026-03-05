"""Task loader for canonical JSONL tasks and legacy V2 JSON fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmark.tasks.legacy_v2 import load_legacy_v2_records, normalize_legacy_v2_tasks
from benchmark.tasks.schemas import validate_task_dict
from benchmark.utils.io import read_jsonl


def _default_split_path(split: str) -> Path:
    root = Path(__file__).resolve().parents[2]
    # Canonical JSONL splits live in data/splits/
    canonical = root / "data" / "splits" / f"{split}.jsonl"
    if canonical.exists():
        return canonical
    # Legacy sample splits (dev.sample.jsonl, test.sample.jsonl, etc.)
    sample = root / "data" / "splits" / f"{split}.sample.jsonl"
    if sample.exists():
        return sample
    # Legacy v2 fallback at repo root
    if split == "v2":
        return root / "openclaw-memory-benchmark-v2.json"
    return canonical


def _read_tasks(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return read_jsonl(path)
    if path.suffix == ".json":
        return normalize_legacy_v2_tasks(load_legacy_v2_records(path))
    raise ValueError(f"Unsupported task file extension for {path}. Use .jsonl or .json")


def load_tasks(
    split: str,
    data_path: str | None = None,
    max_tasks: int | None = None,
) -> list[dict[str, Any]]:
    path = Path(data_path) if data_path else _default_split_path(split)
    if not path.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    tasks = _read_tasks(path)
    validated: list[dict[str, Any]] = []
    for task in tasks:
        validate_task_dict(task)
        validated.append(task)

    if max_tasks is not None:
        return validated[:max_tasks]
    return validated
