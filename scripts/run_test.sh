#!/usr/bin/env bash
set -euo pipefail

python -m benchmark.run \
  --agent local_stub \
  --split test \
  --output-dir outputs \
  --max-tasks 2
