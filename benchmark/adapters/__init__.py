"""Adapter registry and loader."""

from __future__ import annotations

from benchmark.adapters.base import BaseAdapter
from benchmark.adapters.codex import CodexAdapter
from benchmark.adapters.http import HttpAdapter
from benchmark.adapters.local_stub import LocalStubAdapter
from benchmark.adapters.openai import OpenAIAdapter


def get_adapter(name: str) -> BaseAdapter:
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
    raise ValueError(
        f"Unknown adapter '{name}'. "
        "Expected one of: local_stub, codex, openai, or an http(s):// URL"
    )
