"""CLI help test."""

from __future__ import annotations

import subprocess
import sys


def test_cli_help_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "benchmark.run", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--agent" in proc.stdout
