"""Task loader for the OpenClaw v3 benchmark dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmark.tasks.openclaw import load_openclaw_records, normalize_openclaw_tasks
from benchmark.tasks.schemas import validate_task_dict
from benchmark.utils.io import read_jsonl


def _default_data_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "splits" / "v3.jsonl"


def _default_split_path(split: str) -> Path:
    root = Path(__file__).resolve().parents[2]
    # Canonical JSONL splits live in data/splits/
    canonical = root / "data" / "splits" / f"{split}.jsonl"
    if canonical.exists():
        return canonical
    # Small sample splits for CI (e.g. dev.sample.jsonl)
    sample = root / "data" / "splits" / f"{split}.sample.jsonl"
    if sample.exists():
        return sample
    return canonical


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
