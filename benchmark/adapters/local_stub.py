"""Deterministic local adapter for tests and CI."""

from __future__ import annotations

import hashlib
from typing import Any

from benchmark.adapters.base import BaseAdapter


class LocalStubAdapter(BaseAdapter):
    @property
    def name(self) -> str:
        return "local_stub"

    def predict(self, task: dict[str, Any]) -> dict[str, Any]:
        task_id = str(task.get("id", "unknown"))
        prompt_text = str(task.get("input", ""))
        digest = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:8]
        output = task.get("reference_answer") or f"stub:{task_id}:{digest}"
        return {
            "output": output,
            "metadata": {
                "deterministic": True,
                "digest": digest,
            },
        }
