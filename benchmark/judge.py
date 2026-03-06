"""LLM judge for scoring agent responses on the 0-3 Engram scale."""

from __future__ import annotations

import json
import logging
import random
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from benchmark.config import RunConfig

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an evaluation judge. Given a question, expected ground truth \
answer, and an AI agent's response, score the response:

3 = Grounded correct — contains the specific project detail from the \
ground truth
2 = Generic correct — gives a reasonable answer but lacks the specific \
detail
1 = Abstained — says it doesn't have the context or gives a non-answer
0 = Hallucinated — fabricated specific but wrong details

The AI agent may give a longer, more conversational response than a \
direct answer. Focus on whether the key factual content from the ground \
truth is present.

Respond with ONLY a JSON object: \
{"score": <0-3>, "rationale": "<brief explanation>"}\
"""


def _parse_judge_json(raw: str) -> dict[str, Any]:
    """Parse judge response, stripping code fences if present."""
    cleaned = re.sub(r"```json\n?", "", raw)
    cleaned = re.sub(r"```\n?", "", cleaned).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError(f"Judge returned non-JSON: {cleaned[:200]}")
    return json.loads(match.group(0))


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
                f"Question: {question}\n\nGround Truth: {reference}\n\nAI Response: {response}"
            ),
        },
    ]
    body: dict[str, Any] = {
        "model": config.judge_model,
        "messages": messages,
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
    return _parse_judge_json(content)


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
            score = max(0, min(3, score))
            scores.append(score)
            rationales.append(result.get("rationale", "No rationale provided"))
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
        return {
            "score": None,
            "error": "; ".join(errors) or "all passes failed",
        }

    avg = sum(scores) / len(scores)
    out: dict[str, Any] = {
        "score": avg,
        "rationale": rationales[0] if rationales else "",
        "pass_count": len(scores),
    }
    if config.judge_passes > 1:
        out["pass_scores"] = scores
    return out


def _judge_dry_run(task_id: str) -> dict[str, Any]:
    """Generate a random score for dry-run mode (tests full pipeline)."""
    return {
        "task_id": task_id,
        "score": random.randint(0, 3),
        "rationale": "[dry-run] Simulated judgment",
        "pass_count": 1,
    }


def _judge_one(
    task: dict[str, Any],
    pred: dict[str, Any],
    config: RunConfig,
) -> dict[str, Any]:
    """Judge a single task-prediction pair. Thread-safe."""
    task_id = task["id"]
    question = task.get("input", "")
    reference = task.get("reference_answer", "")
    response = pred.get("output", "")

    judgment = judge_response(question, reference, response, config)
    judgment["task_id"] = task_id
    return judgment


def judge_all(
    tasks: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    config: RunConfig,
) -> list[dict[str, Any]]:
    """Judge every prediction with optional concurrency."""
    pred_by_task: dict[str, dict[str, Any]] = {p["task_id"]: p for p in predictions}

    # Dry-run: generate random scores (tests full report pipeline)
    if config.dry_run:
        logger.info("judge: dry-run mode — generating random scores")
        return [_judge_dry_run(t["id"]) for t in tasks]

    concurrency = getattr(config, "judge_concurrency", 1)
    judgments: list[dict[str, Any]] = []

    # Build work items, filtering out missing predictions
    work: list[tuple[dict[str, Any], dict[str, Any]]] = []
    skipped: list[dict[str, Any]] = []
    for task in tasks:
        pred = pred_by_task.get(task["id"])
        if pred is None or pred.get("output") is None:
            skipped.append(
                {
                    "task_id": task["id"],
                    "score": None,
                    "error": "no prediction",
                }
            )
        else:
            work.append((task, pred))

    if concurrency <= 1 or len(work) <= 1:
        # Serial path
        for i, (task, pred) in enumerate(work):
            if (i + 1) % 10 == 0:
                logger.info("judge: [%d/%d]", i + 1, len(work))
            judgments.append(_judge_one(task, pred, config))
    else:
        # Parallel path using ThreadPoolExecutor
        logger.info(
            "judge: using %d concurrent workers for %d tasks",
            concurrency,
            len(work),
        )
        futures = {}
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            for i, (task, pred) in enumerate(work):
                future = pool.submit(_judge_one, task, pred, config)
                futures[future] = i

            results_by_idx: dict[int, dict[str, Any]] = {}
            done = 0
            for future in as_completed(futures):
                idx = futures[future]
                done += 1
                if done % 10 == 0:
                    logger.info("judge: [%d/%d]", done, len(work))
                try:
                    results_by_idx[idx] = future.result()
                except Exception as exc:
                    task_id = work[idx][0]["id"]
                    results_by_idx[idx] = {
                        "task_id": task_id,
                        "score": None,
                        "error": str(exc),
                    }

        # Preserve original order
        for i in range(len(work)):
            judgments.append(results_by_idx[i])

    all_judgments = skipped + judgments
    failures = sum(1 for j in all_judgments if j.get("score") is None)
    logger.info(
        "judge: completed %d judgments (%d failures)",
        len(all_judgments),
        failures,
    )
    return all_judgments
