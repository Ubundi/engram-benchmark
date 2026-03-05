.PHONY: setup lint format test check run-dev run-v2

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
	python3 -m benchmark.run --protocol v2 --condition baseline --agent bench-baseline --dry-run --output-dir outputs
