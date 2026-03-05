"""QA evaluator: exact match, mean judge score, per-category breakdown."""

from __future__ import annotations

from typing import Any


def evaluate_qa(
    tasks: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    judgments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not tasks:
        return {
            "qa.exact_match": 0.0,
            "qa.mean_score": None,
            "qa.judged_count": 0,
            "qa.error_count": 0,
        }

    pred_by_task: dict[str, str] = {p["task_id"]: p.get("output", "") for p in predictions}
    judgment_by_task: dict[str, dict[str, Any]] = {}
    if judgments:
        for j in judgments:
            judgment_by_task[j["task_id"]] = j

    exact_hits = 0
    scores: list[float] = []
    error_count = 0
    category_scores: dict[str, list[float]] = {}

    for task in tasks:
        task_id = task["id"]
        reference = task.get("reference_answer", "")
        output = pred_by_task.get(task_id, "")
        question_type = task.get("metadata", {}).get("question_type") or "unknown"

        if output.strip().lower() == reference.strip().lower():
            exact_hits += 1

        j = judgment_by_task.get(task_id)
        if j:
            score = j.get("score")
            if score is None:
                error_count += 1
            else:
                scores.append(float(score))
                category_scores.setdefault(question_type, []).append(float(score))

    metrics: dict[str, Any] = {
        "qa.exact_match": exact_hits / len(tasks),
        "qa.mean_score": sum(scores) / len(scores) if scores else None,
        "qa.judged_count": len(scores),
        "qa.error_count": error_count,
    }

    for cat, cat_scores in category_scores.items():
        metrics[f"qa.category.{cat}.mean_score"] = sum(cat_scores) / len(cat_scores)

    return metrics
