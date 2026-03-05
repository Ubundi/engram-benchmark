"""OpenAI adapter stub."""

from __future__ import annotations

from typing import Any

from benchmark.adapters.base import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "openai"

    def predict(self, task: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            "OpenAIAdapter is a scaffold stub. Implement API wiring before using --agent openai. "
            "Use --agent local_stub for offline runs."
        )
