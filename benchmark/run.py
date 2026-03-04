"""CLI entrypoint for runtime-first benchmark execution."""

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
from benchmark.v2 import V2RunConfig, run_v2_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run benchmark tasks in standard or V2 protocol mode."
    )
    parser.add_argument(
        "--protocol",
        choices=["standard", "v2"],
        default="standard",
        help="Execution protocol (default: standard).",
    )
    parser.add_argument(
        "--agent",
        required=True,
        help="Standard mode: adapter name (local_stub/codex/openai). V2 mode: OpenClaw agent id.",
    )
    parser.add_argument(
        "--split",
        default="dev",
        help="Dataset split to load (default: dev). Use 'v2' for legacy V2 fallback.",
    )
    parser.add_argument(
        "--data-path",
        default=None,
        help="Optional path to task data (.jsonl canonical, .json legacy V2).",
    )
    parser.add_argument("--output-dir", default="outputs", help="Directory for run artifacts.")
    parser.add_argument("--config", default=None, help="Optional JSON config file path.")
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Optional cap on number of tasks.",
    )

    # V2 protocol options.
    parser.add_argument(
        "--condition",
        choices=["baseline", "cortex"],
        default="baseline",
        help="V2 mode only: runtime condition label (baseline or cortex).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "V2 mode only: simulate seed/probe/judge without external OpenClaw or judge API calls."
        ),
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="V2 mode only: skip the seed phase and only run probe + judge.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=int,
        default=10,
        help="V2 mode only: wait time between seed and probe (default: 10).",
    )
    parser.add_argument(
        "--openclaw-timeout",
        type=int,
        default=int(os.getenv("OPENCLAW_TIMEOUT", "120")),
        help="V2 mode only: timeout in seconds for openclaw CLI calls.",
    )
    parser.add_argument(
        "--judge-model",
        default=os.getenv("JUDGE_MODEL", "gpt-4.1-mini"),
        help="V2 mode only: judge model name.",
    )
    parser.add_argument(
        "--judge-base-url",
        default=os.getenv("JUDGE_BASE_URL", "https://api.openai.com/v1"),
        help="V2 mode only: judge API base URL.",
    )
    parser.add_argument(
        "--judge-api-key",
        default=os.getenv("JUDGE_API_KEY", ""),
        help="V2 mode only: judge API key (falls back to JUDGE_API_KEY env var).",
    )
    parser.add_argument(
        "--judge-passes",
        type=int,
        default=3,
        help="V2 mode only: number of judge passes per response (default: 3).",
    )
    parser.add_argument(
        "--judge-temperature",
        type=float,
        default=None,
        help="V2 mode only: judge temperature (default: 0.3 for multi-pass, 0.0 for single-pass).",
    )
    return parser


def merge_config(args: argparse.Namespace) -> RunConfig:
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


def build_v2_config(args: argparse.Namespace) -> V2RunConfig:
    judge_temperature: float
    if args.judge_temperature is not None:
        judge_temperature = args.judge_temperature
    elif args.judge_passes > 1:
        judge_temperature = 0.3
    else:
        judge_temperature = 0.0

    return V2RunConfig(
        condition=args.condition,
        agent_id=args.agent,
        data_path=args.data_path,
        output_dir=args.output_dir,
        max_tasks=args.max_tasks,
        dry_run=args.dry_run,
        skip_seed=args.skip_seed,
        settle_seconds=args.settle_seconds,
        openclaw_timeout=args.openclaw_timeout,
        judge_model=args.judge_model,
        judge_base_url=args.judge_base_url,
        judge_api_key=args.judge_api_key,
        judge_passes=args.judge_passes,
        judge_temperature=judge_temperature,
    )


def run_benchmark(config: RunConfig) -> dict[str, Any]:
    logger = configure_logging()
    logger.info("loading tasks")
    tasks = load_tasks(split=config.split, data_path=config.data_path, max_tasks=config.max_tasks)

    logger.info("initializing adapter: %s", config.agent)
    adapter = get_adapter(config.agent)

    predictions: list[dict[str, Any]] = []
    logger.info("running placeholder inference loop")
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
        "protocol": "standard",
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
        "protocol": "standard",
        "metrics": metrics,
        "task_count": len(tasks),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.protocol == "v2":
            config = build_v2_config(args)
            summary = run_v2_benchmark(config)
        else:
            config = merge_config(args)
            summary = run_benchmark(config)
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:  # pragma: no cover - fallback for runtime diagnostics.
        print(f"benchmark run failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
