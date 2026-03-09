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

# Required health checks in ``openclaw cortex status`` output
_REQUIRED_STATUS_CHECKS = ("API Health:", "Knowledge:")

# Failure signals in ``openclaw cortex status`` output
_STATUS_FAILURE_SIGNALS = ("FAIL", "ERROR", "unreachable", "unknown command")


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
        """Check Cortex integration via ``openclaw cortex status``.

        Raises RuntimeError if the Cortex plugin is not installed, the
        API is unreachable, or any health check reports failure.
        Only meaningful when condition == 'cortex'.
        """
        logger.info("preflight: checking Cortex integration via CLI")
        args = ["openclaw", "cortex", "status"]

        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Cortex preflight failed: openclaw executable not found on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "Cortex preflight failed: `openclaw cortex status` timed out after 60s."
            ) from exc

        output = (proc.stdout + "\n" + proc.stderr).strip()

        # Check for basic failures (non-zero exit, unknown command)
        if proc.returncode != 0:
            preview = " ".join(output.split())[:300]
            raise RuntimeError(
                f"Cortex preflight failed: `openclaw cortex status` exited "
                f"with code {proc.returncode}. Output: {preview}"
            )

        # Verify required health checks are present and passing
        for check in _REQUIRED_STATUS_CHECKS:
            if check not in output:
                raise RuntimeError(
                    f"Cortex preflight failed: '{check}' not found in status output. "
                    "The Cortex plugin may not be installed or enabled."
                )

        # Scan for failure signals
        output_lower = output.lower()
        for signal in _STATUS_FAILURE_SIGNALS:
            if signal.lower() in output_lower:
                preview = " ".join(output.split())[:300]
                raise RuntimeError(
                    f"Cortex preflight failed: detected '{signal}' in status output. "
                    f"Preview: {preview}"
                )

        logger.info("preflight: Cortex integration healthy (status checks passed)")

    # ------------------------------------------------------------------
    # Date helpers (Engram V3 dataset)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_dataset_date(raw: str) -> str | None:
        """Extract YYYY-MM-DD from Engram V3 date format.

        The dataset uses formats like ``"2026/02/20 (Fri) 14:43"``.
        Returns ``"2026-02-20"`` or *None* if parsing fails.
        """
        import re

        match = re.match(r"(\d{4})/(\d{2})/(\d{2})", raw.strip())
        if not match:
            return None
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # ------------------------------------------------------------------
    # Seed phase
    # ------------------------------------------------------------------

    def seed(self, task: dict[str, Any]) -> dict[str, Any]:
        sessions = task.get("metadata", {}).get("haystack_sessions", [])
        if not sessions:
            return {"seeded": False, "session_count": 0}

        # Engram V3: haystack_dates is positionally aligned with sessions
        haystack_dates = task.get("metadata", {}).get("haystack_dates", [])

        errors: list[str] = []
        total_duration_ms = 0
        turn_count = 0

        for idx, session in enumerate(sessions):
            session_id = f"seed-{task['id']}-{idx}-{uuid.uuid4().hex[:8]}"

            # Extract session date from haystack_dates for cortex condition
            session_date: str | None = None
            if self._condition == "cortex" and idx < len(haystack_dates):
                session_date = self._parse_dataset_date(haystack_dates[idx])

            # Count user turns in this session for logging
            session_user_turns = sum(1 for t in session if t.get("role") == "user")
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
                duration = result.get("duration_ms", 0)
                total_duration_ms += duration
                turn_count += 1
                user_turn_idx += 1
                logger.info(
                    "  session %d/%d turn %d/%d (%dms)",
                    idx + 1,
                    len(sessions),
                    user_turn_idx,
                    session_user_turns,
                    duration,
                )

                if result.get("error"):
                    errors.append(f"session {idx}: {result['error']}")

            # Flush session to trigger memory hooks (V2 --flush-sessions)
            if self._flush_sessions:
                logger.info("  session %d/%d flushing (/new)", idx + 1, len(sessions))
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

    def predict(self, task: dict[str, Any]) -> dict[str, Any]:
        probe_session = f"probe-{task['id']}-{uuid.uuid4().hex[:8]}"

        content = task["input"]
        # Cortex date annotation for temporal accuracy — uses question_date
        # from the Engram dataset metadata
        if self._condition == "cortex":
            raw_date = task.get("metadata", {}).get("question_date", "")
            probe_date = self._parse_dataset_date(raw_date) if raw_date else None
            if probe_date:
                content = f"[cortex-date: {probe_date}]\n\n{content}"

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
