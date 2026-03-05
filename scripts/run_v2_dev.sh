#!/usr/bin/env bash
set -euo pipefail

python3 -m benchmark.run \
  --protocol v2 \
  --condition baseline \
  --agent bench-baseline \
  --data-path openclaw-memory-benchmark-v2.json \
  --max-tasks 10 \
  --dry-run \
  --output-dir outputs
