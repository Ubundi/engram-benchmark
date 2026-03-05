"""Abstention evaluator: keyword-based detection plus judgment score."""

from __future__ import annotations

from typing import Any

_ABSTAIN_PHRASES = (
    "don't have",
    "dont have",
    "don't know",
    "dont know",
    "no information",
    "cannot recall",
    "can't recall",
    "cant recall",
    "i don't",
    "i dont",
    "i'm not sure",
    "im not sure",
    "not aware",
    "unable to find",
    "no record",
    "i cannot",
    "i can't",
    "i cant",
)


def _is_abstention(output: str, score: float | None) -> bool:
    lowered = output.strip().lower()
    if any(phrase in lowered for phrase in _ABSTAIN_PHRASES):
        return True
    if score is not None and round(score) == 1:
        return True
    return False


def evaluate_abstain(
    tasks: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    judgments: list[dict[str, Any]] | None = None,
) -> dict[str, float]:
    if not tasks:
        return {"abstain.rate": 0.0}

    pred_by_task: dict[str, str] = {p["task_id"]: p.get("output", "") for p in predictions}
    judgment_by_task: dict[str, float | None] = {}
    if judgments:
        for j in judgments:
            s = j.get("score")
            judgment_by_task[j["task_id"]] = float(s) if s is not None else None

    abstain_count = 0
    for task in tasks:
        task_id = task["id"]
        output = pred_by_task.get(task_id, "")
        score = judgment_by_task.get(task_id)
        if _is_abstention(output, score):
            abstain_count += 1

    return {"abstain.rate": abstain_count / len(tasks)}
