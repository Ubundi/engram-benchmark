"""HTTP adapter that calls a user's local agent server."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from benchmark.adapters.base import BaseAdapter


class HttpAdapter(BaseAdapter):
    """Adapter that POSTs to a user-hosted agent HTTP server.

    The server must expose two endpoints:
    - POST /seed  — body: {"task_id": str, "sessions": list}
    - POST /probe — body: {"task_id": str, "question": str}
    """

    def __init__(self, base_url: str, timeout: int = 60) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def name(self) -> str:
        return f"http:{self._base_url}"

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach agent server at {url}: {exc.reason}") from exc

    def seed(self, task: dict[str, Any]) -> dict[str, Any]:
        sessions = task.get("metadata", {}).get("haystack_sessions", [])
        if not sessions:
            return {"seeded": False, "session_count": 0}
        result = self._post("/seed", {"task_id": task["id"], "sessions": sessions})
        return {
            "seeded": result.get("seeded", True),
            "session_count": result.get("session_count", len(sessions)),
        }

    def predict(self, task: dict[str, Any]) -> dict[str, Any]:
        result = self._post("/probe", {"task_id": task["id"], "question": task["input"]})
        return {
            "output": result.get("output", ""),
            "metadata": result.get("metadata", {}),
        }
