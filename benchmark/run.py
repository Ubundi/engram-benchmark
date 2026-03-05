"""CLI entrypoint for benchmark execution."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark.adapters import get_adapter
from benchmark.config import RunConfig, load_config
from benchmark.evaluators.abstain import evaluate_abstain
from benchmark.evaluators.qa import evaluate_qa
from benchmark.evaluators.retrieval import evaluate_retrieval
from benchmark.reports.writer import write_run_artifacts
from benchmark.tasks.loader import load_tasks
from benchmark.utils.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the OpenClaw memory benchmark against an agent."
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="Agent adapter name (local_stub) or OpenClaw agent ID for live runs.",
    )
    parser.add_argument(
        "--split",
        default="v3",
        help="Dataset split to load (default: v3).",
    )
    parser.add_argument(
        "--data-path",
        default=None,
        help="Optional explicit path to task data (.jsonl or .json).",
    )
    parser.add_argument("--output-dir", default="outputs", help="Directory for run artifacts.")
    parser.add_argument("--config", default=None, help="Optional JSON config file path.")
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Optional cap on number of tasks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate inference without external agent calls.",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip the seed phase and only run probe + judge.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=int,
        default=120,
        help="Wait time between seed and probe phases (default: 120).",
    )
    parser.add_argument(
        "--openclaw-timeout",
        type=int,
        default=int(os.getenv("OPENCLAW_TIMEOUT", "120")),
        help="Timeout in seconds for openclaw CLI calls.",
    )
    parser.add_argument(
        "--judge-model",
        default=os.getenv("JUDGE_MODEL", "gpt-4.1-mini"),
        help="Judge model name.",
    )
    parser.add_argument(
        "--judge-base-url",
        default=os.getenv("JUDGE_BASE_URL", "https://api.openai.com/v1"),
        help="Judge API base URL.",
    )
    parser.add_argument(
        "--judge-api-key",
        default=os.getenv("JUDGE_API_KEY", ""),
        help="Judge API key (falls back to JUDGE_API_KEY env var).",
    )
    parser.add_argument(
        "--judge-passes",
        type=int,
        default=3,
        help="Number of judge passes per response (default: 3).",
    )
    parser.add_argument(
        "--judge-temperature",
        type=float,
        default=None,
        help="Judge temperature (default: 0.3 for multi-pass, 0.0 for single-pass).",
    )
    return parser


def _build_run_config(args: argparse.Namespace) -> RunConfig:
    file_config = load_config(args.config)
    merged: dict[str, Any] = {
        "agent": args.agent,
        "split": args.split,
        "data_path": args.data_path,
        "output_dir": args.output_dir,
        "config_path": args.config,
        "max_tasks": args.max_tasks,
    }
    for key, value in file_config.items():
        if key in merged and merged[key] is None:
            merged[key] = value
    return RunConfig(**merged)


def run_benchmark(config: RunConfig) -> dict[str, Any]:
    logger = configure_logging()
    logger.info("loading tasks from split: %s", config.split)
    tasks = load_tasks(split=config.split, data_path=config.data_path, max_tasks=config.max_tasks)

    logger.info("initializing adapter: %s", config.agent)
    adapter = get_adapter(config.agent)

    predictions: list[dict[str, Any]] = []
    for task in tasks:
        result = adapter.predict(task)
        prediction = {
            "id": f"pred-{task['id']}",
            "task_id": task["id"],
            "agent": adapter.name,
            "output": result.get("output", ""),
            "metadata": result.get("metadata", {}),
        }
        predictions.append(prediction)

    metrics: dict[str, Any] = {}
    metrics.update(evaluate_qa(tasks, predictions))
    metrics.update(evaluate_retrieval(tasks, predictions))
    metrics.update(evaluate_abstain(tasks, predictions))

    run_id = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_metadata = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "config": config.to_dict(),
        "task_count": len(tasks),
        "prediction_count": len(predictions),
    }

    run_dir = write_run_artifacts(
        output_root=Path(config.output_dir),
        run_id=run_id,
        predictions=predictions,
        metrics=metrics,
        run_metadata=run_metadata,
    )

    logger.info("run complete: %s", run_dir)
    return {
        "run_dir": str(run_dir),
        "metrics": metrics,
        "task_count": len(tasks),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = _build_run_config(args)
        summary = run_benchmark(config)
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"benchmark run failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
