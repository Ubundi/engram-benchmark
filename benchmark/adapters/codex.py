"""Codex adapter stub."""

from __future__ import annotations

from typing import Any

from benchmark.adapters.base import BaseAdapter


class CodexAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "codex"

    def predict(self, task: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            "CodexAdapter is a scaffold stub. Implement API wiring before using --agent codex. "
            "Use --agent local_stub for offline runs."
        )
