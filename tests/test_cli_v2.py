"""CLI smoke test for legacy V2 task loading path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_runs_with_legacy_v2_json(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "openclaw-memory-benchmark-v2.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "benchmark.run",
            "--agent",
            "local_stub",
            "--data-path",
            str(data_path),
            "--max-tasks",
            "1",
            "--output-dir",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert "task_count" in proc.stdout
    run_dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert run_dirs
