.PHONY: setup lint format test check run-dev run-v2 run-v3 ingest-v3

setup:
	python3 -m pip install -e ".[dev]"

lint:
	ruff check benchmark tests
	ruff format --check benchmark tests

format:
	ruff check --fix benchmark tests
	ruff format benchmark tests

test:
	pytest

check: lint test

run-dev:
	python3 -m benchmark.run --agent local_stub --split dev --output-dir outputs

run-v2:
	python3 -m benchmark.run --protocol v2 --agent bench-baseline --dry-run --output-dir outputs

run-v3:
	python3 -m benchmark.run --agent local_stub --split v3 --output-dir outputs

ingest-v3:
	python3 -c "\
import json, sys; sys.path.insert(0, '.'); \
from benchmark.tasks.legacy_v2 import load_legacy_v2_records, normalize_legacy_v2_task; \
from pathlib import Path; \
src = Path('data/raw/v3/openclaw-memory-benchmark-v3.json'); \
out = Path('data/splits/v3.jsonl'); \
records = load_legacy_v2_records(src); \
f = out.open('w'); \
[f.write(json.dumps({**normalize_legacy_v2_task(r), 'metadata': {**normalize_legacy_v2_task(r)['metadata'], 'source_format': 'openclaw_v3'}}, ensure_ascii=False) + '\n') for r in records]; \
f.close(); print(f'Ingested {len(records)} tasks → {out}')"
