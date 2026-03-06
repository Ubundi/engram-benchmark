"""CLI entrypoint for benchmark execution."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark.adapters import get_adapter
from benchmark.adapters.openclaw_cli import VALID_CONDITIONS
from benchmark.config import (
    BENCHMARK_RELEASE,
    OFFICIAL_SPLIT,
    PROTOCOL_VERSION,
    RunConfig,
    load_config,
    resolve_judge_temperature,
)
from benchmark.evaluators.abstain import evaluate_abstain
from benchmark.evaluators.qa import evaluate_qa
from benchmark.evaluators.retrieval import evaluate_retrieval
from benchmark.judge import judge_all
from benchmark.reports.writer import write_run_artifacts
from benchmark.tasks.loader import load_tasks
from benchmark.utils.logging import configure_logging

# Condition-aware settle defaults (matches V2)
_SETTLE_DEFAULTS = {"cortex": 180, "baseline": 10, "clawvault": 10}
_SETTLE_DEFAULT_GENERIC = 120


def _get_git_commit() -> str:
    """Return short git commit SHA, or 'unknown' if unavailable."""
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            or "unknown"
        )
    except Exception:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Engram memory benchmark against an agent."
    )
    parser.add_argument(
        "--agent",
        required=True,
        help=("Agent adapter: local_stub, openclaw, codex, openai, or an http(s):// URL."),
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
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for run artifacts.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional JSON config file path.",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=None,
        help="Optional cap on number of tasks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Simulate inference (skips settle, generates random judge "
            "scores to test the full pipeline)."
        ),
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip the seed phase and only run probe + judge.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=int,
        default=None,
        help=(
            "Wait time between seed and probe phases. "
            "Defaults: cortex=180s, baseline/clawvault=10s, other=120s."
        ),
    )
    parser.add_argument(
        "--openclaw-timeout",
        type=int,
        default=int(os.getenv("OPENCLAW_TIMEOUT", "120")),
        help="Timeout in seconds for openclaw CLI calls.",
    )
    parser.add_argument(
        "--agent-id",
        default=None,
        help="OpenClaw agent ID (passed to openclaw agent --agent).",
    )
    parser.add_argument(
        "--condition",
        default=None,
        help=("Condition label (baseline/cortex/clawvault). Enables condition-specific behavior."),
    )
    parser.add_argument(
        "--flush-sessions",
        action="store_true",
        help=("Send /new after each seed session to trigger session-close memory hooks."),
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
        help=("Judge temperature (default: 0.3 for multi-pass, 0.0 for single-pass)."),
    )
    parser.add_argument(
        "--judge-concurrency",
        type=int,
        default=4,
        help="Number of concurrent judge workers (default: 4).",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar="RUN_DIR",
        default=None,
        help=(
            "Compare two run directories offline. Example: --compare outputs/run-a outputs/run-b"
        ),
    )
    return parser


def _resolve_settle_seconds(explicit: int | None, condition: str | None) -> int:
    """Pick settle time: explicit flag > condition default > generic."""
    if explicit is not None:
        return explicit
    if condition and condition in _SETTLE_DEFAULTS:
        return _SETTLE_DEFAULTS[condition]
    return _SETTLE_DEFAULT_GENERIC


def _build_run_config(args: argparse.Namespace) -> RunConfig:
    file_config = load_config(args.config)
    settle = _resolve_settle_seconds(args.settle_seconds, args.condition)
    merged: dict[str, Any] = {
        "agent": args.agent,
        "split": args.split,
        "data_path": args.data_path,
        "output_dir": args.output_dir,
        "config_path": args.config,
        "max_tasks": args.max_tasks,
        "skip_seed": args.skip_seed,
        "settle_seconds": settle,
        "dry_run": args.dry_run,
        "openclaw_timeout": args.openclaw_timeout,
        "agent_id": args.agent_id,
        "condition": args.condition,
        "flush_sessions": args.flush_sessions,
        "judge_model": args.judge_model,
        "judge_base_url": args.judge_base_url,
        "judge_api_key": args.judge_api_key,
        "judge_passes": args.judge_passes,
        "judge_temperature": args.judge_temperature,
        "judge_concurrency": args.judge_concurrency,
    }
    for key, value in file_config.items():
        if key in merged and merged[key] is None:
            merged[key] = value
    return RunConfig(**merged)


def _validate_condition(condition: str | None) -> None:
    """Validate condition against the allowlist, if set."""
    if condition is None:
        return
    if condition not in VALID_CONDITIONS:
        valid = ", ".join(VALID_CONDITIONS)
        raise ValueError(f"--condition must be one of: {valid} (got '{condition}')")


def run_benchmark(config: RunConfig) -> dict[str, Any]:
    logger = configure_logging()

    # Validate condition
    _validate_condition(config.condition)

    # Warn early if judge key is missing
    if not config.dry_run and not config.judge_api_key:
        logger.warning(
            "JUDGE_API_KEY is not set — judging will be skipped. "
            "Set JUDGE_API_KEY for scored results."
        )

    git_commit = _get_git_commit()
    logger.info("loading tasks from split: %s", config.split)
    tasks = load_tasks(
        split=config.split,
        data_path=config.data_path,
        max_tasks=config.max_tasks,
    )

    logger.info("initializing adapter: %s", config.agent)
    adapter = get_adapter(config.agent, config=config)

    # Cortex preflight check (V2 pattern)
    from benchmark.adapters.openclaw_cli import OpenClawCLIAdapter

    if (
        isinstance(adapter, OpenClawCLIAdapter)
        and config.condition == "cortex"
        and not config.dry_run
    ):
        adapter.run_preflight()

    # Phase 1: Seed
    seed_turns: list[dict[str, Any]] = []
    if not config.skip_seed:
        logger.info("phase 1: seeding %d tasks", len(tasks))
        for task in tasks:
            result = adapter.seed(task)
            seed_turns.append({"task_id": task["id"], **result})
    else:
        logger.info("phase 1: skipped (--skip-seed)")

    # Phase 2: Settle
    if not config.skip_seed and config.settle_seconds > 0 and not config.dry_run:
        settle_reason = ""
        if config.condition == "cortex":
            settle_reason = " (async Cortex ingest: extraction + embedding + graph build)"
        logger.info(
            "phase 2: settling for %ds%s...",
            config.settle_seconds,
            settle_reason,
        )
        settle_start = time.monotonic()
        time.sleep(config.settle_seconds)
        elapsed = int((time.monotonic() - settle_start) * 1000)
        logger.info("phase 2: settled (%dms)", elapsed)
    else:
        logger.info("phase 2: skipped")

    # Phase 3: Probe
    logger.info("phase 3: probing %d tasks", len(tasks))
    predictions: list[dict[str, Any]] = []
    probes: list[dict[str, Any]] = []
    probe_latencies: list[int] = []
    for i, task in enumerate(tasks):
        if (i + 1) % 50 == 0:
            logger.info("probe: [%d/%d]", i + 1, len(tasks))
        result = adapter.predict(task)
        output = result.get("output", "")
        duration_ms = result.get("metadata", {}).get("duration_ms", 0)
        prediction = {
            "id": f"pred-{task['id']}",
            "task_id": task["id"],
            "agent": adapter.name,
            "output": output,
            "metadata": result.get("metadata", {}),
        }
        predictions.append(prediction)
        probes.append(
            {
                "task_id": task["id"],
                "question": task["input"],
                "output": output,
                "duration_ms": duration_ms,
            }
        )
        if duration_ms > 0:
            probe_latencies.append(duration_ms)

    # Log probe latency stats
    if probe_latencies:
        probe_latencies.sort()
        n = len(probe_latencies)
        p50 = probe_latencies[n // 2]
        p95 = probe_latencies[int(n * 0.95)]
        avg = sum(probe_latencies) // n
        logger.info(
            "probe latency: avg=%dms p50=%dms p95=%dms max=%dms",
            avg,
            p50,
            p95,
            probe_latencies[-1],
        )

    # Phase 4: Judge
    judgments: list[dict[str, Any]] = []
    if config.dry_run:
        logger.info("phase 4: dry-run — generating random judge scores")
        judgments = judge_all(tasks, predictions, config)
    elif config.judge_api_key:
        logger.info(
            "phase 4: judging %d predictions (model=%s, passes=%d, concurrency=%d)",
            len(predictions),
            config.judge_model,
            config.judge_passes,
            config.judge_concurrency,
        )
        judgments = judge_all(tasks, predictions, config)
    else:
        logger.info("phase 4: skipped (no JUDGE_API_KEY)")

    metrics: dict[str, Any] = {}
    metrics.update(evaluate_qa(tasks, predictions, judgments or None))
    metrics.update(evaluate_retrieval(tasks, predictions, judgments or None))
    metrics.update(evaluate_abstain(tasks, predictions, judgments or None))

    run_id = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_metadata: dict[str, Any] = {
        "benchmark_release": BENCHMARK_RELEASE,
        "protocol_version": PROTOCOL_VERSION,
        "official_setting": {
            "split": OFFICIAL_SPLIT,
            "judge_model": config.judge_model,
            "judge_passes": config.judge_passes,
            "judge_temperature": resolve_judge_temperature(config),
        },
        "run_id": run_id,
        "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        "condition": config.condition,
        "git_commit": git_commit,
        "config": config.to_dict(),
        "task_count": len(tasks),
        "prediction_count": len(predictions),
        "seed_count": len(seed_turns),
        "judgment_count": len(judgments),
    }

    run_dir = write_run_artifacts(
        output_root=Path(config.output_dir),
        run_id=run_id,
        predictions=predictions,
        metrics=metrics,
        run_metadata=run_metadata,
        seed_turns=seed_turns if not config.skip_seed else None,
        probes=probes,
        judgments=judgments if judgments else None,
    )

    # Write Markdown report
    from benchmark.reports.markdown import write_markdown_report

    md_path = write_markdown_report(
        run_dir=run_dir,
        run_metadata=run_metadata,
        metrics=metrics,
        tasks=tasks,
        predictions=predictions,
        judgments=judgments,
        probes=probes,
        seed_turns=seed_turns if not config.skip_seed else None,
    )
    logger.info("markdown report: %s", md_path)

    logger.info("run complete: %s", run_dir)
    return {
        "run_dir": str(run_dir),
        "metrics": metrics,
        "task_count": len(tasks),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Handle --compare mode (offline, no agent needed)
    if args.compare:
        from benchmark.compare import run_comparison

        return run_comparison(args.compare[0], args.compare[1])

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
