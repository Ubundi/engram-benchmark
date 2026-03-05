"""Abstention evaluator stub."""

from __future__ import annotations

from typing import Any


def evaluate_abstain(
    tasks: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> dict[str, float]:
    _ = tasks, predictions
    return {"abstain.rate": 0.0}
