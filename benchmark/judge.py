"""LLM judge for scoring agent responses on the 0-3 Engram scale."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from benchmark.config import RunConfig

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Score the agent response against the reference answer on a 0-3 scale:
  3 = grounded correct: right answer, cites a specific detail from the haystack
  2 = generic correct: right direction but missing the specific detail
  1 = abstained: honest admission of not knowing
  0 = hallucinated: wrong specific detail stated confidently

Respond ONLY with JSON: {"score": <int 0-3>, "rationale": "<one sentence>"}\
"""


def _call_judge(
    question: str,
    reference: str,
    response: str,
    config: RunConfig,
) -> dict[str, Any]:
    """Single LLM call to the judge. Returns parsed JSON dict."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Question: {question}\nReference answer: {reference}\nAgent response: {response}"
            ),
        },
    ]
    body: dict[str, Any] = {
        "model": config.judge_model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    temperature = config.judge_temperature
    if temperature is None:
        temperature = 0.3 if config.judge_passes > 1 else 0.0
    body["temperature"] = temperature

    data = json.dumps(body).encode("utf-8")
    url = f"{config.judge_base_url.rstrip('/')}/chat/completions"
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.judge_api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    content = result["choices"][0]["message"]["content"]
    return json.loads(content)


def judge_response(
    question: str,
    reference: str,
    response: str,
    config: RunConfig,
) -> dict[str, Any]:
    """Run judge_passes LLM calls and average the scores."""
    scores: list[int] = []
    rationales: list[str] = []
    errors: list[str] = []

    for _ in range(config.judge_passes):
        try:
            result = _call_judge(question, reference, response, config)
            score = int(result["score"])
            if score not in (0, 1, 2, 3):
                raise ValueError(f"score out of range: {score}")
            scores.append(score)
            rationales.append(result.get("rationale", ""))
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            KeyError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            errors.append(str(exc))
            logger.warning("judge pass failed: %s", exc)

    if not scores:
        return {"score": None, "error": "; ".join(errors) or "all passes failed"}

    avg = sum(scores) / len(scores)
    return {
        "score": avg,
        "scores": scores,
        "rationale": rationales[0] if rationales else "",
        "pass_count": len(scores),
    }


def judge_all(
    tasks: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    config: RunConfig,
) -> list[dict[str, Any]]:
    """Judge every prediction. Returns one judgment dict per prediction."""
    pred_by_task: dict[str, dict[str, Any]] = {p["task_id"]: p for p in predictions}
    judgments: list[dict[str, Any]] = []

    for task in tasks:
        task_id = task["id"]
        pred = pred_by_task.get(task_id)
        if pred is None:
            judgments.append({"task_id": task_id, "score": None, "error": "no prediction"})
            continue

        question = task.get("input", "")
        reference = task.get("reference_answer", "")
        response = pred.get("output", "")

        judgment = judge_response(question, reference, response, config)
        judgment["task_id"] = task_id
        judgments.append(judgment)
        logger.debug("judged %s: score=%s", task_id, judgment.get("score"))

    return judgments
