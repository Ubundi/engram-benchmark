"""CI step: fetch engram-v3.json from HuggingFace and run the repo validator."""

from __future__ import annotations

import subprocess
import sys

from benchmark.tasks.hf import fetch_engram_dataset


def main() -> int:
    path = fetch_engram_dataset()
    result = subprocess.run(
        [sys.executable, "-m", "scripts.validate_v3", str(path)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
