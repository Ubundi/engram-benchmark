"""Schema utilities for task and prediction objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    """Raised when an object does not satisfy the expected scaffold schema."""


def _schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "schemas"


def load_task_schema() -> dict[str, Any]:
    with (_schema_dir() / "task.schema.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_prediction_schema() -> dict[str, Any]:
    with (_schema_dir() / "prediction.schema.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_task_dict(task: dict[str, Any]) -> None:
    required = {"id", "input", "reference_answer"}
    missing = sorted(required - task.keys())
    if missing:
        raise SchemaValidationError(f"Task missing required fields: {missing}")
    if not isinstance(task["id"], str):
        raise SchemaValidationError("Task field 'id' must be a string")
    if not isinstance(task["input"], str):
        raise SchemaValidationError("Task field 'input' must be a string")
    if not isinstance(task["reference_answer"], str):
        raise SchemaValidationError("Task field 'reference_answer' must be a string")
