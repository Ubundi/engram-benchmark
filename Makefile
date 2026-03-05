.PHONY: setup lint format test check run fetch

setup:
	python3 -m pip install -e ".[dev]"

lint:
	uv run ruff check benchmark tests
	uv run ruff format --check benchmark tests

format:
	uv run ruff check --fix benchmark tests
	uv run ruff format benchmark tests

test:
	uv run pytest

check: lint test

run:
	python3 -m benchmark.run --agent local_stub --output-dir outputs

fetch:
	python3 -c "from benchmark.tasks.hf import fetch_engram_dataset; p = fetch_engram_dataset(); print(f'Dataset cached at: {p}')"
