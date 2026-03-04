#!/usr/bin/env bash
set -euo pipefail

python3 -m benchmark.run \
  --protocol v2 \
  --condition cortex \
  --agent bench-cortex \
  --data-path openclaw-memory-benchmark-v2.json \
  --max-tasks 2 \
  --dry-run \
  --output-dir outputs
