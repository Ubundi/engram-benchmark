"""Configuration helpers for benchmark runtime."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

BENCHMARK_RELEASE = "engram-v3.0"
PROTOCOL_VERSION = "engram-runtime-v1"
OFFICIAL_SPLIT = "v3"
OFFICIAL_JUDGE_MODEL = "gpt-4.1-mini"
OFFICIAL_JUDGE_PASSES = 3
OFFICIAL_JUDGE_TEMPERATURE = 0.3


@dataclass
class RunConfig:
    agent: str
    split: str = "v3"
    data_path: str | None = None
    output_dir: str = "outputs"
    config_path: str | None = None
    max_tasks: int | None = None
    skip_seed: bool = False
    settle_seconds: int = 120
    dry_run: bool = False
    judge_model: str = "gpt-4.1-mini"
    judge_base_url: str = "https://api.openai.com/v1"
    judge_api_key: str = ""
    judge_passes: int = 3
    judge_temperature: float | None = None
    openclaw_timeout: int = 120
    agent_id: str | None = None
    condition: str | None = None
    flush_sessions: bool = False
    judge_concurrency: int = 4

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_judge_temperature(config: RunConfig) -> float:
    """Resolve the effective judge temperature for the current run."""
    if config.judge_temperature is not None:
        return config.judge_temperature
    return OFFICIAL_JUDGE_TEMPERATURE if config.judge_passes > 1 else 0.0


def load_config(path: str | None) -> dict[str, Any]:
    """Load JSON config from disk if provided, else return an empty mapping."""
    if path is None:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
