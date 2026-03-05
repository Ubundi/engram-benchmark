#!/usr/bin/env bash
set -euo pipefail

python3 -m benchmark.run \
  --agent local_stub \
  --split dev \
  --output-dir outputs
