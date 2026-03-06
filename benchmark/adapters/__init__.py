"""Adapter registry and loader."""

from __future__ import annotations

from typing import TYPE_CHECKING

from benchmark.adapters.base import BaseAdapter
from benchmark.adapters.codex import CodexAdapter
from benchmark.adapters.http import HttpAdapter
from benchmark.adapters.local_stub import LocalStubAdapter
from benchmark.adapters.openai import OpenAIAdapter
from benchmark.adapters.openclaw_cli import OpenClawCLIAdapter

if TYPE_CHECKING:
    from benchmark.config import RunConfig


def get_adapter(name: str, config: RunConfig | None = None) -> BaseAdapter:
    stripped = name.strip()
    if stripped.startswith("http://") or stripped.startswith("https://"):
        return HttpAdapter(base_url=stripped)
    normalized = stripped.lower()
    if normalized == "local_stub":
        return LocalStubAdapter()
    if normalized == "codex":
        return CodexAdapter()
    if normalized == "openai":
        return OpenAIAdapter()
    if normalized == "openclaw":
        agent_id = getattr(config, "agent_id", None)
        timeout = getattr(config, "openclaw_timeout", 120)
        condition = getattr(config, "condition", None)
        flush = getattr(config, "flush_sessions", False)
        return OpenClawCLIAdapter(
            agent_id=agent_id,
            timeout=timeout,
            condition=condition,
            flush_sessions=flush,
        )
    raise ValueError(
        f"Unknown adapter '{name}'. "
        "Expected one of: local_stub, codex, openai, openclaw, "
        "or an http(s):// URL"
    )
