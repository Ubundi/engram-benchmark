.PHONY: setup lint format test check run fetch

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

fetch:
	python3 -c "from benchmark.tasks.hf import fetch_engram_dataset; p = fetch_engram_dataset(); print(f'Dataset cached at: {p}')"
