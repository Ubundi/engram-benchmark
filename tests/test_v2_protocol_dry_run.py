"""Dry-run integration test for V2 protocol mode."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_v2_protocol_dry_run_writes_phase_artifacts(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "openclaw-memory-benchmark-v2.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "benchmark.run",
            "--protocol",
            "v2",
            "--condition",
            "baseline",
            "--agent",
            "bench-baseline",
            "--data-path",
            str(data_path),
            "--max-tasks",
            "2",
            "--dry-run",
            "--output-dir",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    summary = json.loads(proc.stdout)
    run_dir = Path(summary["run_dir"])
    assert run_dir.exists()
    assert (run_dir / "predictions.jsonl").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "run_metadata.json").exists()
    assert (run_dir / "seed_turns.jsonl").exists()
    assert (run_dir / "probes.jsonl").exists()
    assert (run_dir / "judgments.jsonl").exists()
    assert (run_dir / "v2_report.json").exists()
