"""Write benchmark run artifacts to disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmark.utils.io import ensure_dir, write_json, write_jsonl


def write_run_artifacts(
    output_root: Path,
    run_id: str,
    predictions: list[dict[str, Any]],
    metrics: dict[str, Any],
    run_metadata: dict[str, Any],
) -> Path:
    run_dir = ensure_dir(output_root / run_id)
    write_jsonl(run_dir / "predictions.jsonl", predictions)
    write_json(run_dir / "metrics.json", metrics)
    write_json(run_dir / "run_metadata.json", run_metadata)
    return run_dir
