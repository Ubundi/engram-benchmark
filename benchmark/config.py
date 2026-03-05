"""Configuration helpers for benchmark runtime."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunConfig:
    agent: str
    split: str = "dev"
    data_path: str | None = None
    output_dir: str = "outputs"
    config_path: str | None = None
    max_tasks: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_config(path: str | None) -> dict[str, Any]:
    """Load JSON config from disk if provided, else return an empty mapping."""
    if path is None:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
