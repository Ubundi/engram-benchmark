"""Runtime protocol for the legacy V2 OpenClaw benchmark."""

from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark.reports.writer import write_run_artifacts
from benchmark.tasks.legacy_v2 import load_legacy_v2_records
from benchmark.utils.io import write_json, write_jsonl
from benchmark.utils.logging import configure_logging


@dataclass
class V2RunConfig:
    condition: str
    agent_id: str | None
    data_path: str | None
    output_dir: str
    max_tasks: int | None
    dry_run: bool
    skip_seed: bool
    settle_seconds: int
    openclaw_timeout: int
    judge_model: str
    judge_base_url: str
    judge_api_key: str
    judge_passes: int
    judge_temperature: float

    def to_metadata_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["judge_api_key"] = "***" if self.judge_api_key else ""
        payload["judge_api_key_set"] = bool(self.judge_api_key)
        return payload


def run_v2_benchmark(config: V2RunConfig) -> dict[str, Any]:
    logger = configure_logging()
    data_path = _resolve_data_path(config.data_path)
    records = load_legacy_v2_records(data_path)
    if config.max_tasks is not None:
        records = records[: config.max_tasks]

    if not config.dry_run and not config.judge_api_key:
        raise ValueError("JUDGE_API_KEY is required for V2 protocol unless --dry-run is set")

    _run_cortex_preflight(config, logger)

    seed_sessions = _extract_seed_sessions(records)
    seed_turns = _run_seed_phase(config, seed_sessions, logger)
    _run_settle_phase(config, logger)
    probes = _run_probe_phase(config, records, logger)
    judgments = _run_judge_phase(config, probes, logger)

    metrics = _compute_metrics(probes, judgments)
    predictions = _build_predictions(config.condition, probes, judgments)

    run_id = f"v2-{config.condition}-{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    run_metadata = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "protocol": "v2",
        "condition": config.condition,
        "config": config.to_metadata_dict(),
        "data_path": str(data_path),
        "seed_session_count": len(seed_sessions),
        "seed_turn_count": len(seed_turns),
        "probe_count": len(probes),
    }

    run_dir = write_run_artifacts(
        output_root=Path(config.output_dir),
        run_id=run_id,
        predictions=predictions,
        metrics=metrics,
        run_metadata=run_metadata,
    )

    write_jsonl(run_dir / "seed_turns.jsonl", seed_turns)
    write_jsonl(run_dir / "probes.jsonl", probes)
    write_jsonl(run_dir / "judgments.jsonl", judgments)
    write_json(
        run_dir / "v2_report.json",
        {
            "run_id": run_id,
            "condition": config.condition,
            "seed_sessions": len(seed_sessions),
            "seed_turns": seed_turns,
            "probes": probes,
            "judgments": judgments,
            "metrics": metrics,
        },
    )

    logger.info("v2 run complete: %s", run_dir)
    return {
        "run_dir": str(run_dir),
        "protocol": "v2",
        "condition": config.condition,
        "task_count": len(records),
        "mean_score": metrics.get("v2.mean_score", 0.0),
    }


def _resolve_data_path(path: str | None) -> Path:
    if path:
        return Path(path)
    root = Path(__file__).resolve().parents[2]
    return root / "openclaw-memory-benchmark-v2.json"


def _extract_seed_sessions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sessions: dict[str, list[dict[str, str]]] = {}
    for record in records:
        haystack_ids = record.get("haystack_session_ids", [])
        haystack_sessions = record.get("haystack_sessions", [])
        if not isinstance(haystack_sessions, list):
            continue

        for idx, session in enumerate(haystack_sessions):
            if not isinstance(session, list):
                continue
            if idx < len(haystack_ids) and isinstance(haystack_ids[idx], str):
                session_id = haystack_ids[idx]
            else:
                session_id = f"legacy-session-{idx}"
            if session_id in sessions:
                continue

            cleaned: list[dict[str, str]] = []
            for turn in session:
                if not isinstance(turn, dict):
                    continue
                role = str(turn.get("role", "user"))
                content = str(turn.get("content", "")).strip()
                if not content:
                    continue
                cleaned.append({"role": role, "content": content})
            if cleaned:
                sessions[session_id] = cleaned

    return [
        {"session_id": session_id, "messages": messages}
        for session_id, messages in sorted(sessions.items(), key=lambda item: item[0])
    ]


def _run_seed_phase(
    config: V2RunConfig,
    seed_sessions: list[dict[str, Any]],
    logger: Any,
) -> list[dict[str, Any]]:
    if config.skip_seed:
        logger.info("v2 seed phase skipped (--skip-seed)")
        return []

    logger.info("v2 seed phase: %d sessions", len(seed_sessions))
    seed_turns: list[dict[str, Any]] = []

    for idx, session in enumerate(seed_sessions, start=1):
        session_id = str(session["session_id"])
        runtime_session_id = f"benchmark-seed-{session_id}-{int(time.time())}"
        messages = session.get("messages", [])
        user_turns = [
            str(m.get("content", ""))
            for m in messages
            if isinstance(m, dict) and str(m.get("role", "")) == "user"
        ]
        logger.info(
            "v2 seed [%d/%d] %s (%d turns)",
            idx,
            len(seed_sessions),
            session_id,
            len(user_turns),
        )

        for turn_index, turn in enumerate(user_turns, start=1):
            if config.dry_run:
                result = {
                    "response": f"[dry-run] seeded turn {turn_index}",
                    "duration_ms": 0,
                    "error": None,
                    "tool_names": [],
                }
            else:
                result = _send_to_openclaw(
                    message=turn,
                    agent_id=config.agent_id,
                    session_id=runtime_session_id,
                    timeout_seconds=config.openclaw_timeout,
                )

            seed_turns.append(
                {
                    "seed_session_id": session_id,
                    "runtime_session_id": runtime_session_id,
                    "turn_index": turn_index,
                    "message": turn,
                    "response": result["response"],
                    "error": result["error"],
                    "duration_ms": result["duration_ms"],
                }
            )

    return seed_turns


def _run_settle_phase(config: V2RunConfig, logger: Any) -> None:
    if config.dry_run:
        logger.info("v2 settle phase skipped in dry-run")
        return
    logger.info("v2 settle phase: waiting %ds", config.settle_seconds)
    time.sleep(config.settle_seconds)


def _run_probe_phase(
    config: V2RunConfig,
    records: list[dict[str, Any]],
    logger: Any,
) -> list[dict[str, Any]]:
    logger.info("v2 probe phase: %d prompts", len(records))
    probe_session_id = f"benchmark-probe-{config.condition}-{int(time.time())}"
    probes: list[dict[str, Any]] = []

    for idx, record in enumerate(records, start=1):
        prompt_id = str(record.get("question_id", f"question-{idx:04d}"))
        prompt = str(record.get("question", ""))
        ground_truth = str(record.get("answer", ""))
        question_type = str(record.get("question_type", "unknown"))

        logger.info("v2 probe [%d/%d] %s", idx, len(records), prompt_id)

        if config.dry_run:
            response = f"[dry-run] answer for {prompt_id}"
            duration_ms = 0
            error = None
        else:
            result = _send_to_openclaw(
                message=prompt,
                agent_id=config.agent_id,
                session_id=probe_session_id,
                timeout_seconds=config.openclaw_timeout,
            )
            response = result["response"]
            duration_ms = result["duration_ms"]
            error = result["error"]

        probes.append(
            {
                "prompt_id": prompt_id,
                "question_type": question_type,
                "prompt": prompt,
                "ground_truth": ground_truth,
                "response": response,
                "error": error,
                "duration_ms": duration_ms,
            }
        )

    return probes


def _run_judge_phase(
    config: V2RunConfig,
    probes: list[dict[str, Any]],
    logger: Any,
) -> list[dict[str, Any]]:
    logger.info("v2 judge phase: %d probes", len(probes))
    judgments: list[dict[str, Any]] = []

    for probe in probes:
        if probe.get("error"):
            judgments.append(
                {
                    "prompt_id": probe["prompt_id"],
                    "score": None,
                    "rationale": None,
                    "pass_scores": [],
                    "error": str(probe["error"]),
                }
            )
            continue

        if config.dry_run:
            score = 2.0
            judgments.append(
                {
                    "prompt_id": probe["prompt_id"],
                    "score": score,
                    "rationale": "dry-run placeholder score",
                    "pass_scores": [score],
                    "error": None,
                }
            )
            continue

        pass_scores: list[float] = []
        rationale = ""
        error: str | None = None

        for _ in range(config.judge_passes):
            try:
                score, parsed_rationale = _judge_once(
                    prompt=str(probe["prompt"]),
                    ground_truth=str(probe["ground_truth"]),
                    response=str(probe["response"]),
                    api_key=config.judge_api_key,
                    base_url=config.judge_base_url,
                    model=config.judge_model,
                    temperature=config.judge_temperature,
                )
                pass_scores.append(score)
                if not rationale:
                    rationale = parsed_rationale
            except Exception as exc:  # pragma: no cover - runtime path.
                error = str(exc)
                break

        if error is not None:
            judgments.append(
                {
                    "prompt_id": probe["prompt_id"],
                    "score": None,
                    "rationale": None,
                    "pass_scores": pass_scores,
                    "error": error,
                }
            )
            continue

        mean_score = sum(pass_scores) / len(pass_scores) if pass_scores else 0.0
        judgments.append(
            {
                "prompt_id": probe["prompt_id"],
                "score": mean_score,
                "rationale": rationale,
                "pass_scores": pass_scores,
                "error": None,
            }
        )

    return judgments


def _judge_once(
    prompt: str,
    ground_truth: str,
    response: str,
    api_key: str,
    base_url: str,
    model: str,
    temperature: float,
) -> tuple[float, str]:
    system_prompt = (
        "You are an evaluation judge. Score responses against ground truth. "
        "Use this rubric: 3 grounded correct, 2 generic correct, 1 abstained, 0 hallucinated. "
        'Return JSON only: {"score": <0-3>, "rationale": "..."}.'
    )
    user_prompt = f"Question: {prompt}\n\nGround Truth: {ground_truth}\n\nAI Response: {response}"

    completion = _call_judge_chat_completion(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return _parse_judge_output(completion)


def _call_judge_chat_completion(
    api_key: str,
    base_url: str,
    model: str,
    temperature: float,
    messages: list[dict[str, str]],
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 512,
    }
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:  # pragma: no cover - runtime path.
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Judge API returned {exc.code}: {details[:300]}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - runtime path.
        raise RuntimeError(f"Judge API request failed: {exc}") from exc

    payload_obj = json.loads(body)
    choices = payload_obj.get("choices", [])
    if not choices:
        raise RuntimeError("Judge API returned no choices")
    message = choices[0].get("message", {})
    content = message.get("content")
    if not isinstance(content, str):
        raise RuntimeError("Judge API returned no text content")
    return content


def _parse_judge_output(output: str) -> tuple[float, str]:
    cleaned = output.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"Judge output did not contain JSON: {cleaned[:200]}")

    payload = json.loads(match.group(0))
    score = payload.get("score")
    if not isinstance(score, (int, float)):
        raise RuntimeError("Judge score is missing or non-numeric")
    rationale = payload.get("rationale")
    if not isinstance(rationale, str):
        rationale = "No rationale provided"

    clamped = max(0.0, min(3.0, float(score)))
    return clamped, rationale


def _build_predictions(
    condition: str,
    probes: list[dict[str, Any]],
    judgments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_prompt = {j["prompt_id"]: j for j in judgments}
    predictions: list[dict[str, Any]] = []

    for probe in probes:
        prompt_id = str(probe["prompt_id"])
        judgment = by_prompt.get(prompt_id, {})
        predictions.append(
            {
                "id": f"pred-{prompt_id}",
                "task_id": prompt_id,
                "agent": condition,
                "output": str(probe.get("response") or ""),
                "metadata": {
                    "question_type": probe.get("question_type", "unknown"),
                    "judge_score": judgment.get("score"),
                    "judge_error": judgment.get("error"),
                },
            }
        )

    return predictions


def _compute_metrics(
    probes: list[dict[str, Any]],
    judgments: list[dict[str, Any]],
) -> dict[str, Any]:
    score_by_prompt = {
        str(item["prompt_id"]): float(item["score"])
        for item in judgments
        if item.get("score") is not None
    }

    scores = list(score_by_prompt.values())
    mean_score = sum(scores) / len(scores) if scores else 0.0

    metrics: dict[str, Any] = {
        "v2.mean_score": mean_score,
        "v2.prompt_count": len(probes),
        "v2.judged_count": len(scores),
        "v2.error_count": sum(1 for item in judgments if item.get("score") is None),
    }

    distribution = {"0": 0, "1": 0, "2": 0, "3": 0}
    for score in scores:
        bucket = str(int(round(score)))
        distribution[bucket] = distribution.get(bucket, 0) + 1
    for key, value in distribution.items():
        metrics[f"v2.score_{key}"] = value

    category_scores: dict[str, list[float]] = {}
    for probe in probes:
        prompt_id = str(probe["prompt_id"])
        if prompt_id not in score_by_prompt:
            continue
        question_type = str(probe.get("question_type", "unknown"))
        category_scores.setdefault(question_type, []).append(score_by_prompt[prompt_id])

    for category, category_values in sorted(category_scores.items(), key=lambda item: item[0]):
        slug = _slugify_metric_key(category)
        metrics[f"v2.category.{slug}.mean_score"] = sum(category_values) / len(category_values)
        metrics[f"v2.category.{slug}.count"] = len(category_values)

    return metrics


def _slugify_metric_key(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "unknown"


def _run_cortex_preflight(config: V2RunConfig, logger: Any) -> None:
    if config.dry_run or config.condition != "cortex":
        return

    logger.info("v2 preflight: checking cortex tools via /memories")
    result = _send_to_openclaw(
        message="/memories",
        agent_id=config.agent_id,
        session_id=f"benchmark-preflight-{int(time.time())}",
        timeout_seconds=config.openclaw_timeout,
    )
    if result["error"]:
        raise RuntimeError(f"Cortex preflight failed: {result['error']}")

    tool_names = set(result.get("tool_names", []))
    required_tools = {"cortex_search_memory", "cortex_save_memory"}
    if not required_tools.issubset(tool_names):
        raise RuntimeError(
            "Cortex preflight failed: required tools missing in prompt metadata "
            f"(found={sorted(tool_names)})"
        )


def _send_to_openclaw(
    message: str,
    agent_id: str | None,
    session_id: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    args = ["openclaw", "agent", "--message", message, "--json", "--session-id", session_id]
    if agent_id:
        args.extend(["--agent", agent_id])
    args.extend(["--timeout", str(timeout_seconds)])

    started = time.time()
    try:
        proc = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 5,
        )
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - runtime path.
        duration_ms = int((time.time() - started) * 1000)
        return {
            "response": None,
            "duration_ms": duration_ms,
            "error": f"timeout: {exc}",
            "tool_names": [],
        }

    duration_ms = int((time.time() - started) * 1000)
    if proc.returncode != 0:
        error = proc.stderr.strip() or proc.stdout.strip() or "openclaw command failed"
        return {
            "response": None,
            "duration_ms": duration_ms,
            "error": error,
            "tool_names": [],
        }

    raw = proc.stdout.strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "response": raw,
            "duration_ms": duration_ms,
            "error": None,
            "tool_names": [],
        }

    payloads = []
    if isinstance(parsed, dict):
        result = parsed.get("result")
        if isinstance(result, dict) and isinstance(result.get("payloads"), list):
            payloads = result.get("payloads", [])
        elif isinstance(parsed.get("payloads"), list):
            payloads = parsed.get("payloads", [])

    texts: list[str] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        text_value = payload.get("text")
        if isinstance(text_value, str) and text_value.strip():
            texts.append(text_value.strip())

    response_text: str | None
    if texts:
        response_text = "\n\n".join(texts)
    elif isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
        response_text = parsed["text"]
    elif isinstance(parsed, dict) and isinstance(parsed.get("message"), str):
        response_text = parsed["message"]
    else:
        response_text = raw

    tool_names = _extract_tool_names(parsed)
    return {
        "response": response_text,
        "duration_ms": duration_ms,
        "error": None,
        "tool_names": tool_names,
    }


def _extract_tool_names(parsed: Any) -> list[str]:
    if not isinstance(parsed, dict):
        return []
    result = parsed.get("result")
    if not isinstance(result, dict):
        return []
    meta = result.get("meta")
    if not isinstance(meta, dict):
        return []
    report = meta.get("systemPromptReport")
    if not isinstance(report, dict):
        return []
    tools = report.get("tools")
    if not isinstance(tools, dict):
        return []
    entries = tools.get("entries")
    if not isinstance(entries, list):
        return []

    names: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names
