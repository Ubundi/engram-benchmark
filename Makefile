.PHONY: setup lint format test check run ingest-v3

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

run:
	python3 -m benchmark.run --agent local_stub --output-dir outputs

ingest-v3:
	python3 -c "\
import json, sys; sys.path.insert(0, '.'); \
from benchmark.tasks.openclaw import load_openclaw_records, normalize_openclaw_task; \
from pathlib import Path; \
src = Path('data/raw/v3/openclaw-memory-benchmark-v3.json'); \
out = Path('data/splits/v3.jsonl'); \
records = load_openclaw_records(src); \
f = out.open('w'); \
[f.write(json.dumps(normalize_openclaw_task(r), ensure_ascii=False) + '\n') for r in records]; \
f.close(); print(f'Ingested {len(records)} tasks to {out}')"
