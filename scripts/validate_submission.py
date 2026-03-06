"""Validate a benchmark run output directory for leaderboard submission.

Checks:
  1. All required files are present
  2. metrics.json matches the metrics schema
  3. run_metadata.json matches the run_metadata schema
  4. predictions.jsonl records match the prediction schema
  5. judgments.jsonl records match the judgment schema
  6. Counts are consistent across files
  7. Score ranges are valid

Usage:
    python scripts/validate_submission.py outputs/20260304T093015Z
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from benchmark.config import (
    BENCHMARK_RELEASE,
    OFFICIAL_JUDGE_MODEL,
    OFFICIAL_JUDGE_PASSES,
    OFFICIAL_JUDGE_TEMPERATURE,
    OFFICIAL_SPLIT,
    PROTOCOL_VERSION,
)

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "data" / "schemas"

REQUIRED_FILES = [
    "metrics.json",
    "run_metadata.json",
    "predictions.jsonl",
]

PHASE_ARTIFACTS = [
    "seed_turns.jsonl",
    "probes.jsonl",
    "judgments.jsonl",
]


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def _load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None  # noqa: RET503 — caller handles None


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _check_files(run_dir: Path, result: ValidationResult) -> None:
    for name in REQUIRED_FILES:
        if not (run_dir / name).exists():
            result.error(f"Missing required file: {name}")

    for name in PHASE_ARTIFACTS:
        if not (run_dir / name).exists():
            result.warn(f"Missing phase artifact: {name}")


def _check_metrics(run_dir: Path, result: ValidationResult) -> None:
    path = run_dir / "metrics.json"
    if not path.exists():
        return

    metrics = _load_json(path)
    if not isinstance(metrics, dict):
        result.error("metrics.json: must be a JSON object")
        return

    required = [
        "qa.mean_score",
        "qa.exact_match",
        "qa.judged_count",
        "qa.error_count",
        "retrieval.hit_rate",
        "retrieval.judged_count",
        "abstain.rate",
    ]
    for key in required:
        if key not in metrics:
            result.error(f"metrics.json: missing required key '{key}'")

    score = metrics.get("qa.mean_score")
    if score is not None and not (0 <= score <= 3):
        result.error(f"metrics.json: qa.mean_score={score} out of range [0, 3]")

    for key in ("qa.exact_match", "retrieval.hit_rate", "abstain.rate"):
        val = metrics.get(key)
        if val is not None and not (0 <= val <= 1):
            result.error(f"metrics.json: {key}={val} out of range [0, 1]")

    for key, val in metrics.items():
        if key.startswith("qa.category.") and key.endswith(".mean_score"):
            if val is not None and not (0 <= val <= 3):
                result.error(f"metrics.json: {key}={val} out of range [0, 3]")


def _check_run_metadata(run_dir: Path, result: ValidationResult) -> None:
    path = run_dir / "run_metadata.json"
    if not path.exists():
        return

    meta = _load_json(path)
    if not isinstance(meta, dict):
        result.error("run_metadata.json: must be a JSON object")
        return

    required = [
        "benchmark_release",
        "protocol_version",
        "answer_model",
        "run_id",
        "timestamp_utc",
        "config",
        "task_count",
        "prediction_count",
    ]
    for key in required:
        if key not in meta:
            result.error(f"run_metadata.json: missing required key '{key}'")

    config = meta.get("config")
    if isinstance(config, dict):
        for key in ("agent", "split", "answer_model"):
            if key not in config:
                result.error(f"run_metadata.json: config missing required key '{key}'")
    elif config is not None:
        result.error("run_metadata.json: config must be an object")

    official_setting = meta.get("official_setting")
    if not isinstance(official_setting, dict):
        result.error("run_metadata.json: missing or invalid 'official_setting'")
        return

    if meta.get("benchmark_release") != BENCHMARK_RELEASE:
        result.error(
            "run_metadata.json: benchmark_release must be "
            f"'{BENCHMARK_RELEASE}' for official submissions"
        )
    if meta.get("protocol_version") != PROTOCOL_VERSION:
        result.error(
            "run_metadata.json: protocol_version must be "
            f"'{PROTOCOL_VERSION}' for official submissions"
        )

    if isinstance(config, dict):
        if config.get("split") != OFFICIAL_SPLIT:
            result.error(
                f"run_metadata.json: config.split must be '{OFFICIAL_SPLIT}' "
                "for official submissions"
            )
        config_answer_model = config.get("answer_model")
        if not isinstance(config_answer_model, str) or not config_answer_model.strip():
            result.error(
                "run_metadata.json: official submissions must record a non-empty "
                "config.answer_model"
            )
        if config.get("skip_seed") is True:
            result.error("run_metadata.json: official submissions may not use skip_seed")
        if config.get("dry_run") is True:
            result.error("run_metadata.json: official submissions may not use dry_run")

    answer_model = meta.get("answer_model")
    if not isinstance(answer_model, str) or not answer_model.strip():
        result.error(
            "run_metadata.json: official submissions must record a non-empty 'answer_model'"
        )
    elif isinstance(config, dict) and answer_model != config.get("answer_model"):
        result.error("run_metadata.json: answer_model must match config.answer_model")

    if official_setting.get("split") != OFFICIAL_SPLIT:
        result.error(
            "run_metadata.json: official_setting.split must be "
            f"'{OFFICIAL_SPLIT}'"
        )
    if official_setting.get("judge_model") != OFFICIAL_JUDGE_MODEL:
        result.error(
            "run_metadata.json: official_setting.judge_model must be "
            f"'{OFFICIAL_JUDGE_MODEL}'"
        )
    if official_setting.get("judge_passes") != OFFICIAL_JUDGE_PASSES:
        result.error(
            "run_metadata.json: official_setting.judge_passes must be "
            f"{OFFICIAL_JUDGE_PASSES}"
        )
    if official_setting.get("judge_temperature") != OFFICIAL_JUDGE_TEMPERATURE:
        result.error(
            "run_metadata.json: official_setting.judge_temperature must be "
            f"{OFFICIAL_JUDGE_TEMPERATURE}"
        )


def _check_predictions(run_dir: Path, result: ValidationResult) -> int:
    path = run_dir / "predictions.jsonl"
    if not path.exists():
        return 0

    records = _load_jsonl(path)
    required = {"id", "task_id", "agent", "output"}

    for i, rec in enumerate(records):
        missing = required - rec.keys()
        if missing:
            result.error(f"predictions.jsonl line {i + 1}: missing keys {sorted(missing)}")

    return len(records)


def _check_judgments(run_dir: Path, result: ValidationResult) -> int:
    path = run_dir / "judgments.jsonl"
    if not path.exists():
        return 0

    records = _load_jsonl(path)

    for i, rec in enumerate(records):
        if "task_id" not in rec:
            result.error(f"judgments.jsonl line {i + 1}: missing 'task_id'")

        score = rec.get("score")
        if score is None:
            if "error" not in rec:
                result.error(f"judgments.jsonl line {i + 1}: score is null but no 'error' field")
        else:
            if not (0 <= score <= 3):
                result.error(f"judgments.jsonl line {i + 1}: score={score} out of range [0, 3]")
            if "scores" not in rec:
                result.warn(f"judgments.jsonl line {i + 1}: missing 'scores' array")

    return len(records)


def _check_consistency(
    run_dir: Path,
    prediction_count: int,
    judgment_count: int,
    result: ValidationResult,
) -> None:
    meta_path = run_dir / "run_metadata.json"
    if not meta_path.exists():
        return

    meta = _load_json(meta_path)
    if not isinstance(meta, dict):
        return

    declared_predictions = meta.get("prediction_count")
    if declared_predictions is not None and declared_predictions != prediction_count:
        result.error(
            f"Consistency: run_metadata says {declared_predictions} "
            f"predictions but predictions.jsonl has {prediction_count}"
        )

    declared_judgments = meta.get("judgment_count")
    if declared_judgments is not None and declared_judgments != judgment_count:
        result.error(
            f"Consistency: run_metadata says {declared_judgments} "
            f"judgments but judgments.jsonl has {judgment_count}"
        )

    metrics_path = run_dir / "metrics.json"
    if metrics_path.exists():
        metrics = _load_json(metrics_path)
        if isinstance(metrics, dict):
            judged = metrics.get("qa.judged_count", 0)
            errors = metrics.get("qa.error_count", 0)
            if judgment_count > 0 and (judged + errors) != judgment_count:
                result.warn(
                    f"Consistency: judged_count ({judged}) + "
                    f"error_count ({errors}) != "
                    f"judgment records ({judgment_count})"
                )


def validate(run_dir: Path) -> ValidationResult:
    result = ValidationResult()

    if not run_dir.is_dir():
        result.error(f"Not a directory: {run_dir}")
        return result

    _check_files(run_dir, result)
    _check_metrics(run_dir, result)
    _check_run_metadata(run_dir, result)
    prediction_count = _check_predictions(run_dir, result)
    judgment_count = _check_judgments(run_dir, result)
    _check_consistency(run_dir, prediction_count, judgment_count, result)

    return result


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <run_output_dir>")
        return 2

    run_dir = Path(sys.argv[1])
    result = validate(run_dir)

    print(f"Validating: {run_dir}\n")

    if result.errors:
        print(f"ERRORS ({len(result.errors)}):")
        for err in result.errors:
            print(f"  - {err}")
        print()

    if result.warnings:
        print(f"WARNINGS ({len(result.warnings)}):")
        for warn in result.warnings:
            print(f"  - {warn}")
        print()

    if result.passed:
        print("RESULT: PASS — submission is valid")
    else:
        print("RESULT: FAIL — fix errors above before submitting")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
