# Contributing

## Scope

This repository is a runtime-first benchmark package. Contributions should improve
execution quality, reproducibility, and documentation clarity for real agent runs.

## Development setup

```bash
python3 -m pip install -e ".[dev]"
pre-commit install
```

## Required checks

```bash
make format
make lint
make test
```

## Contribution rules

- Keep pull requests focused and reviewable.
- Add tests for behavior changes.
- Update docs for CLI, schema, or protocol changes.
- Do not commit private credentials or proprietary datasets.
- Do not commit generated benchmark outputs unless explicitly requested.

## Documentation standard

Any operator-facing change must update relevant docs:
- `README.md`
- `docs/evaluation_protocol.md`
- `docs/reproducibility.md`
- `docs/benchmark_spec.md`

## Commit guidance

- Use clear imperative commit messages.
- Keep unrelated refactors out of feature/fix commits.
- Preserve backward compatibility unless the PR explicitly proposes a breaking change.
