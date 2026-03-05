"""Retrieval evaluator: hit rate based on judge score >= 2."""

from __future__ import annotations

from typing import Any


def evaluate_retrieval(
    tasks: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    judgments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not tasks:
        return {"retrieval.hit_rate": 0.0, "retrieval.judged_count": 0}

    if not judgments:
        return {"retrieval.hit_rate": 0.0, "retrieval.judged_count": 0}

    scored = [j for j in judgments if j.get("score") is not None]
    if not scored:
        return {"retrieval.hit_rate": 0.0, "retrieval.judged_count": 0}

    hits = sum(1 for j in scored if float(j["score"]) >= 2.0)
    return {
        "retrieval.hit_rate": hits / len(scored),
        "retrieval.judged_count": len(scored),
    }
