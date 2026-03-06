"""OpenClaw CLI adapter — invokes ``openclaw agent`` as a subprocess."""

from __future__ import annotations

import json
import logging
import subprocess
import time
import uuid
from typing import Any

from benchmark.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

# Valid condition labels (matches V2)
VALID_CONDITIONS = ("baseline", "clawvault", "cortex")

# Unhealthy signals for cortex preflight (matches V2)
_UNHEALTHY_SIGNALS = (
    "cortex status check failed",
    "memory search failed",
    "cortex offline",
    "api unreachable",
    "__openclaw_api_key__",
    "unknown command",
)


class OpenClawCLIAdapter(BaseAdapter):
    """Adapter that calls the OpenClaw CLI for seed and probe phases.

    Each call invokes ``openclaw agent --message <msg> --json`` as a
    subprocess, mirroring the V2 TypeScript runner's ``sendToAgent()``.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        timeout: int = 120,
        condition: str | None = None,
        flush_sessions: bool = False,
    ) -> None:
        self._agent_id = agent_id
        self._timeout = timeout
        self._condition = condition
        self._flush_sessions = flush_sessions

    @property
    def name(self) -> str:
        if self._agent_id:
            return f"openclaw:{self._agent_id}"
        return "openclaw"

    # ------------------------------------------------------------------
    # Core CLI call
    # ------------------------------------------------------------------

    def _call(
        self,
        message: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Invoke ``openclaw agent`` and return parsed response with timing."""
        args = ["openclaw", "agent", "--message", message, "--json"]
        if self._agent_id:
            args.extend(["--agent", self._agent_id])
        if session_id:
            args.extend(["--session-id", session_id])
        if self._timeout:
            args.extend(["--timeout", str(self._timeout)])

        # Process timeout adds 5s buffer over the agent timeout (V2 pattern)
        process_timeout = self._timeout + 5
        start = time.monotonic()

        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=process_timeout,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            stdout = proc.stdout.strip()
            if not stdout:
                return {
                    "response": None,
                    "error": proc.stderr.strip() or "empty response",
                    "duration_ms": duration_ms,
                }
            result = self._parse_response(stdout)
            result["duration_ms"] = duration_ms
            return result
        except FileNotFoundError:
            duration_ms = int((time.monotonic() - start) * 1000)
            return {
                "response": None,
                "error": (
                    "openclaw executable not found on PATH. "
                    "Install OpenClaw or use a different adapter."
                ),
                "duration_ms": duration_ms,
            }
        except subprocess.TimeoutExpired:
            duration_ms = int((time.monotonic() - start) * 1000)
            return {
                "response": None,
                "error": f"openclaw timed out after {process_timeout}s",
                "duration_ms": duration_ms,
            }
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            return {
                "response": None,
                "error": str(exc),
                "duration_ms": duration_ms,
            }

    # ------------------------------------------------------------------
    # Response parsing — mirrors V2 sendToAgent() fallback chain
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(raw: str) -> dict[str, Any]:
        """Parse JSON output from ``openclaw agent --json``.

        Fallback chain (matches V2 TypeScript runner):
        1. ``result.payloads[].text`` joined
        2. ``parsed.text``
        3. ``parsed.message``
        4. ``parsed.response``
        5. Raw stdout
        """
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"response": raw, "raw": raw}

        # Try result.payloads[].text first
        payloads = None
        tool_names = None
        if isinstance(parsed, dict):
            result = parsed.get("result", {})
            if isinstance(result, dict):
                payloads = result.get("payloads")
                # Extract tool names for preflight checks
                tools = (
                    result.get("meta", {})
                    .get("systemPromptReport", {})
                    .get("tools", {})
                    .get("entries", [])
                )
                if isinstance(tools, list):
                    tool_names = [
                        e["name"]
                        for e in tools
                        if isinstance(e, dict) and isinstance(e.get("name"), str)
                    ]
            if payloads is None:
                payloads = parsed.get("payloads")

        if isinstance(payloads, list):
            texts = [
                p["text"].strip()
                for p in payloads
                if isinstance(p, dict) and isinstance(p.get("text"), str) and p["text"].strip()
            ]
            if texts:
                out: dict[str, Any] = {
                    "response": "\n\n".join(texts),
                    "raw": parsed,
                }
                if tool_names:
                    out["tool_names"] = tool_names
                return out

        # Fallback chain
        if isinstance(parsed, dict):
            for key in ("text", "message", "response"):
                val = parsed.get(key)
                if isinstance(val, str):
                    out = {"response": val, "raw": parsed}
                    if tool_names:
                        out["tool_names"] = tool_names
                    return out

        if isinstance(parsed, str):
            return {"response": parsed, "raw": parsed}

        out = {"response": raw, "raw": parsed}
        if tool_names:
            out["tool_names"] = tool_names
        return out

    # ------------------------------------------------------------------
    # Cortex preflight health check
    # ------------------------------------------------------------------

    def run_preflight(self) -> None:
        """Check Cortex integration by sending /memories to the agent.

        Raises RuntimeError if the agent lacks Cortex tools or reports
        unhealthy status. Only meaningful when condition == 'cortex'.
        """
        logger.info("preflight: checking Cortex integration via /memories")
        session_id = f"benchmark-preflight-cortex-{int(time.time())}"
        check = self._call("/memories", session_id=session_id)

        if check.get("error"):
            raise RuntimeError(
                f"Cortex preflight failed: could not run /memories ({check['error']})"
            )

        response = (check.get("response") or "").strip()
        tool_names = check.get("tool_names", [])
        has_search = "cortex_search_memory" in tool_names
        has_save = "cortex_save_memory" in tool_names

        if not has_search or not has_save:
            raise RuntimeError(
                f"Cortex preflight failed: cortex tools not present "
                f"(search={has_search}, save={has_save}). "
                "The Cortex plugin is likely not installed/enabled."
            )

        resp_lower = response.lower()
        for signal in _UNHEALTHY_SIGNALS:
            if signal in resp_lower:
                preview = " ".join(response.split())[:240]
                raise RuntimeError(
                    "Cortex preflight failed: /memories reported "
                    f"unhealthy status. Preview: {preview}"
                )

        logger.info("preflight: Cortex integration healthy (tools present, /memories succeeded)")

    # ------------------------------------------------------------------
    # Cortex date helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_session_date(
        session_meta: dict[str, Any],
        base_date_ms: int,
    ) -> str | None:
        """Compute YYYY-MM-DD from a session description's 'Day N'.

        Mirrors V2's getSessionDate() — derives the date from the Arclight
        base date (2024-10-07) plus the day offset in the description.
        """
        import re
        from datetime import datetime, timedelta, timezone

        desc = session_meta.get("description", "")
        match = re.search(r"Day (\d+)", desc, re.IGNORECASE)
        if not match:
            return None
        day = int(match.group(1))
        base = datetime.fromtimestamp(base_date_ms / 1000, tz=timezone.utc)
        dt = base + timedelta(days=day - 1)
        return dt.strftime("%Y-%m-%d")

    # ------------------------------------------------------------------
    # Seed phase
    # ------------------------------------------------------------------

    def seed(self, task: dict[str, Any]) -> dict[str, Any]:
        sessions = task.get("metadata", {}).get("haystack_sessions", [])
        if not sessions:
            return {"seeded": False, "session_count": 0}

        # Cortex date injection constants (Arclight dataset)
        arclight_base_ms = 1728259200000  # 2024-10-07T00:00:00Z

        errors: list[str] = []
        total_duration_ms = 0
        turn_count = 0

        for idx, session in enumerate(sessions):
            session_id = f"seed-{task['id']}-{idx}-{uuid.uuid4().hex[:8]}"

            # Compute session date for cortex condition
            session_date: str | None = None
            if self._condition == "cortex":
                session_meta = task.get("metadata", {}).get("haystack_session_meta", [{}])
                meta = session_meta[idx] if idx < len(session_meta) else {}
                session_date = self._get_session_date(meta, arclight_base_ms)

            user_turn_idx = 0
            for turn in session:
                if turn.get("role") != "user":
                    continue

                content = turn["content"]
                # Inject date into first user turn for cortex condition
                if session_date and self._condition == "cortex" and user_turn_idx == 0:
                    content = (
                        f"[Context: This conversation took place on "
                        f"{session_date}. Use this as the date anchor "
                        f"for all events and decisions discussed.]\n\n"
                        f"{content}"
                    )

                result = self._call(content, session_id=session_id)
                total_duration_ms += result.get("duration_ms", 0)
                turn_count += 1
                user_turn_idx += 1

                if result.get("error"):
                    errors.append(f"session {idx}: {result['error']}")

            # Flush session to trigger memory hooks (V2 --flush-sessions)
            if self._flush_sessions:
                logger.debug("flushing session %d (sending /new)", idx)
                self._call("/new", session_id=session_id)

        meta: dict[str, Any] = {
            "seeded": True,
            "session_count": len(sessions),
            "turn_count": turn_count,
            "total_duration_ms": total_duration_ms,
        }
        if errors:
            meta["errors"] = errors
        return meta

    # ------------------------------------------------------------------
    # Probe phase
    # ------------------------------------------------------------------

    # Arclight project end date — one day after last session (Day 42)
    _ARCLIGHT_END_DATE = "2024-11-18"

    def predict(self, task: dict[str, Any]) -> dict[str, Any]:
        probe_session = f"probe-{task['id']}-{uuid.uuid4().hex[:8]}"

        content = task["input"]
        # Cortex date annotation for temporal accuracy (V2 pattern)
        if self._condition == "cortex":
            content = f"[cortex-date: {self._ARCLIGHT_END_DATE}]\n\n{content}"

        result = self._call(content, session_id=probe_session)

        metadata: dict[str, Any] = {
            "duration_ms": result.get("duration_ms", 0),
        }
        if result.get("error"):
            metadata["error"] = result["error"]
        if result.get("raw"):
            metadata["raw"] = result["raw"]

        return {
            "output": result.get("response") or "",
            "metadata": metadata,
        }
