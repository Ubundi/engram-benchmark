"""Tests for the submission validation script."""

import json
import sys
import tempfile
from pathlib import Path

# scripts/ is not an installed package — add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.config import BENCHMARK_RELEASE, PROTOCOL_VERSION
from scripts.validate_submission import validate


def _write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path, records):
    lines = [json.dumps(r, ensure_ascii=False) for r in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _valid_dir():
    d = Path(tempfile.mkdtemp())
    _write(
        d / "metrics.json",
        {
            "qa.mean_score": 2.0,
            "qa.exact_match": 0.5,
            "qa.judged_count": 2,
            "qa.error_count": 0,
            "retrieval.hit_rate": 0.5,
            "retrieval.judged_count": 2,
            "abstain.rate": 0.1,
        },
    )
    _write(
        d / "run_metadata.json",
        {
            "benchmark_release": BENCHMARK_RELEASE,
            "protocol_version": PROTOCOL_VERSION,
            "official_setting": {
                "split": "v3",
                "judge_model": "gpt-4.1-mini",
                "judge_passes": 3,
                "judge_temperature": 0.3,
            },
            "run_id": "20260304T093015Z",
            "timestamp_utc": "2026-03-04T09:30:15Z",
            "config": {"agent": "test", "split": "v3", "skip_seed": False, "dry_run": False},
            "task_count": 2,
            "prediction_count": 2,
        },
    )
    _write_jsonl(
        d / "predictions.jsonl",
        [
            {"id": "pred-t1", "task_id": "t1", "agent": "test", "output": "a"},
            {"id": "pred-t2", "task_id": "t2", "agent": "test", "output": "b"},
        ],
    )
    return d


class TestSubmissionValidator:
    def test_valid_directory_passes(self):
        d = _valid_dir()
        result = validate(d)
        assert result.passed

    def test_missing_metrics_fails(self):
        d = _valid_dir()
        (d / "metrics.json").unlink()
        result = validate(d)
        assert not result.passed
        assert any("metrics.json" in e for e in result.errors)

    def test_missing_predictions_fails(self):
        d = _valid_dir()
        (d / "predictions.jsonl").unlink()
        result = validate(d)
        assert not result.passed

    def test_score_out_of_range(self):
        d = _valid_dir()
        _write(
            d / "metrics.json",
            {
                "qa.mean_score": 5.0,
                "qa.exact_match": 0.5,
                "qa.judged_count": 2,
                "qa.error_count": 0,
                "retrieval.hit_rate": 0.5,
                "retrieval.judged_count": 2,
                "abstain.rate": 0.1,
            },
        )
        result = validate(d)
        assert not result.passed
        assert any("out of range" in e for e in result.errors)

    def test_missing_metric_key(self):
        d = _valid_dir()
        _write(d / "metrics.json", {"qa.mean_score": 2.0})
        result = validate(d)
        assert not result.passed
        assert any("missing required key" in e for e in result.errors)

    def test_prediction_count_mismatch(self):
        d = _valid_dir()
        _write(
            d / "run_metadata.json",
            {
                "benchmark_release": BENCHMARK_RELEASE,
                "protocol_version": PROTOCOL_VERSION,
                "official_setting": {
                    "split": "v3",
                    "judge_model": "gpt-4.1-mini",
                    "judge_passes": 3,
                    "judge_temperature": 0.3,
                },
                "run_id": "test",
                "timestamp_utc": "2026-03-04T00:00:00Z",
                "config": {"agent": "test", "split": "v3", "skip_seed": False, "dry_run": False},
                "task_count": 2,
                "prediction_count": 99,
            },
        )
        result = validate(d)
        assert not result.passed
        assert any("Consistency" in e for e in result.errors)

    def test_missing_official_release_metadata_fails(self):
        d = _valid_dir()
        _write(
            d / "run_metadata.json",
            {
                "run_id": "20260304T093015Z",
                "timestamp_utc": "2026-03-04T09:30:15Z",
                "config": {"agent": "test", "split": "v3"},
                "task_count": 2,
                "prediction_count": 2,
            },
        )
        result = validate(d)
        assert not result.passed
        assert any("benchmark_release" in e for e in result.errors)

    def test_non_official_judge_config_fails(self):
        d = _valid_dir()
        _write(
            d / "run_metadata.json",
            {
                "benchmark_release": BENCHMARK_RELEASE,
                "protocol_version": PROTOCOL_VERSION,
                "official_setting": {
                    "split": "v3",
                    "judge_model": "gpt-4.1",
                    "judge_passes": 1,
                    "judge_temperature": 0.0,
                },
                "run_id": "20260304T093015Z",
                "timestamp_utc": "2026-03-04T09:30:15Z",
                "config": {"agent": "test", "split": "v3", "skip_seed": False, "dry_run": False},
                "task_count": 2,
                "prediction_count": 2,
            },
        )
        result = validate(d)
        assert not result.passed
        assert any("official_setting.judge_model" in e for e in result.errors)

    def test_missing_phase_artifacts_are_warnings(self):
        d = _valid_dir()
        result = validate(d)
        assert result.passed  # warnings don't fail
        assert any("seed_turns.jsonl" in w for w in result.warnings)

    def test_judgment_null_score_without_error(self):
        d = _valid_dir()
        _write_jsonl(
            d / "judgments.jsonl",
            [{"task_id": "t1", "score": None}],
        )
        result = validate(d)
        assert not result.passed
        assert any("no 'error' field" in e for e in result.errors)

    def test_not_a_directory(self):
        result = validate(Path("/nonexistent/path"))
        assert not result.passed
