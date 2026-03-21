"""OpenClaw CLI adapter — invokes ``openclaw agent`` as a subprocess."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from benchmark.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

# Valid condition labels (matches V2)
VALID_CONDITIONS = ("baseline", "clawvault", "cortex", "lossless-claw", "mem0")

# Required health checks in ``openclaw cortex status`` output
_REQUIRED_STATUS_CHECKS = ("API Health:", "Knowledge:")

# Failure signals in ``openclaw cortex status`` output
_STATUS_FAILURE_SIGNALS = ("FAIL", "ERROR", "unreachable", "unknown command")

# Transient error patterns that warrant a retry (API-side, not our fault)
_TRANSIENT_ERROR_PATTERNS = ("overloaded", "529", "rate_limit", "capacity")

# Retry settings — only for transient API errors (overload, rate limit)
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 5  # seconds

# Inter-turn delay to avoid burst-loading the API (seconds)
_INTER_TURN_DELAY = 1.5


def _is_transient_error(text: str) -> bool:
    """Check if error text matches a known transient API error."""
    lower = text.lower()
    return any(p in lower for p in _TRANSIENT_ERROR_PATTERNS)


class OpenClawCLIAdapter(BaseAdapter):
    """Adapter that calls the OpenClaw CLI for seed and probe phases.

    Each call invokes ``openclaw agent --message <msg> --json`` as a
    subprocess, mirroring the V2 TypeScript runner's ``sendToAgent()``.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        timeout: int = 240,
        condition: str | None = None,
        flush_sessions: bool = False,
    ) -> None:
        self._agent_id = agent_id
        self._timeout = timeout
        self._condition = condition
        self._flush_sessions = flush_sessions
        self._call_count = 0

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
        """Invoke ``openclaw agent`` and return parsed response with timing.

        Retries only on transient API errors (overloaded, rate limit) with
        short exponential backoff.  Timeouts and other errors fail immediately.
        """
        args = ["openclaw", "agent", "--message", message, "--json"]
        if self._agent_id:
            args.extend(["--agent", self._agent_id])
        if session_id:
            args.extend(["--session-id", session_id])
        if self._timeout:
            args.extend(["--timeout", str(self._timeout)])

        # Process timeout adds 5s buffer over the agent timeout (V2 pattern)
        process_timeout = self._timeout + 5

        # Inter-turn delay to smooth out API request bursts
        if self._call_count > 0:
            time.sleep(_INTER_TURN_DELAY)
        self._call_count += 1

        for attempt in range(_MAX_RETRIES + 1):
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
                stderr = proc.stderr.strip()

                if not stdout:
                    error_msg = stderr or "empty response"
                    # Retry only on transient API errors
                    if _is_transient_error(error_msg) and attempt < _MAX_RETRIES:
                        wait = _RETRY_BACKOFF_BASE * (2**attempt)
                        logger.warning(
                            "transient API error (attempt %d/%d): %s — retrying in %ds",
                            attempt + 1,
                            _MAX_RETRIES + 1,
                            error_msg[:200],
                            wait,
                        )
                        time.sleep(wait)
                        continue
                    return {
                        "response": None,
                        "error": error_msg,
                        "duration_ms": duration_ms,
                    }

                # Check if the response itself contains a transient error
                if _is_transient_error(stdout) and attempt < _MAX_RETRIES:
                    wait = _RETRY_BACKOFF_BASE * (2**attempt)
                    logger.warning(
                        "transient API error in response (attempt %d/%d) — retrying in %ds",
                        attempt + 1,
                        _MAX_RETRIES + 1,
                        wait,
                    )
                    time.sleep(wait)
                    continue

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

        # All retries exhausted on transient error
        return {
            "response": None,
            "error": "max retries exhausted (transient API errors)",
            "duration_ms": 0,
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

        Plugin log lines (e.g. ``[plugins] Cortex v2.5.0 ready``) and ANSI
        escape codes are stripped before JSON parsing.
        """
        # Strip ANSI escape codes (all CSI sequences, not just color)
        ansi_re = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
        cleaned = ansi_re.sub("", raw)

        # Strip non-JSON lines (plugin banners before and after the JSON body).
        # Find the first line starting with '{' and the last line ending with
        # '}' or ']' to bracket the JSON payload.
        lines = cleaned.split("\n")
        json_start = None
        json_end = None
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("{"):
                json_start = i
                break
        if json_start is not None:
            for i in range(len(lines) - 1, json_start - 1, -1):
                stripped = lines[i].rstrip()
                if stripped.endswith("}") or stripped.endswith("]"):
                    json_end = i
                    break
            end = json_end + 1 if json_end is not None else len(lines)
            cleaned = "\n".join(lines[json_start:end])

        try:
            parsed = json.loads(cleaned)
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

        Retries up to 3 times on transient failures (e.g. AbortError on
        Knowledge check) since the API can be briefly unstable after a reset.
        """
        logger.info("preflight: checking Cortex integration via CLI")
        args = ["openclaw", "cortex", "status"]

        last_error: str | None = None
        for attempt in range(3):
            if attempt > 0:
                wait = 5 * attempt
                logger.info("preflight: retrying in %ds (attempt %d/3)", wait, attempt + 1)
                time.sleep(wait)

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
            except subprocess.TimeoutExpired:
                last_error = "`openclaw cortex status` timed out after 60s"
                continue

            output = (proc.stdout + "\n" + proc.stderr).strip()

            if proc.returncode != 0:
                last_error = (
                    f"`openclaw cortex status` exited with code {proc.returncode}. "
                    f"Output: {' '.join(output.split())[:300]}"
                )
                continue

            # Verify required health checks are present
            missing = [c for c in _REQUIRED_STATUS_CHECKS if c not in output]
            if missing:
                raise RuntimeError(
                    f"Cortex preflight failed: {missing} not found in status output. "
                    "The Cortex plugin may not be installed or enabled."
                )

            # Scan for failure signals
            output_lower = output.lower()
            failed_signals = [s for s in _STATUS_FAILURE_SIGNALS if s.lower() in output_lower]
            if failed_signals:
                last_error = (
                    f"detected {failed_signals} in status output. "
                    f"Preview: {' '.join(output.split())[:300]}"
                )
                continue

            logger.info("preflight: Cortex integration healthy (status checks passed)")
            self._patch_agents_md_memory_glob()
            return

        raise RuntimeError(f"Cortex preflight failed after 3 attempts: {last_error}")

    # ------------------------------------------------------------------
    # Workspace patching (cortex condition)
    # ------------------------------------------------------------------

    _AGENTS_MD_PATH = Path.home() / ".openclaw" / "workspace" / "AGENTS.md"
    _AGENTS_MD_BACKUP = Path.home() / ".openclaw" / "workspace" / ".AGENTS.md.bench-backup"

    def _patch_agents_md_memory_glob(self) -> None:
        """Patch AGENTS.md to glob memory files by date prefix.

        The default AGENTS.md instructs the agent to read exact files like
        ``memory/YYYY-MM-DD.md``, but the cortex condition creates
        topic-specific files (e.g. ``memory/2026-03-19-arclight-setup.md``).
        This patch changes the instruction to match all files with the date
        prefix so the agent finds its own captured knowledge during probes.

        A backup is saved so ``restore_agents_md`` can revert the change
        after the benchmark run, avoiding cross-condition contamination.
        """
        if not self._AGENTS_MD_PATH.exists():
            logger.debug("AGENTS.md not found, skipping memory glob patch")
            return

        content = self._AGENTS_MD_PATH.read_text()

        old = "Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context"
        new = (
            "Read all files in `memory/` matching today's or yesterday's "
            "date prefix (e.g. `memory/2026-03-19-*.md`) for recent context"
        )

        if old not in content:
            logger.debug("AGENTS.md memory instruction already patched or not found")
            return

        # Save backup before mutating
        self._AGENTS_MD_BACKUP.write_text(content)
        content = content.replace(old, new)
        self._AGENTS_MD_PATH.write_text(content)
        logger.info("patched AGENTS.md: memory file read uses date-prefix glob")

    def restore_agents_md(self) -> None:
        """Restore AGENTS.md from the pre-benchmark backup.

        Called after the run completes (success or failure) to avoid
        leaking condition-specific patches into subsequent runs.
        """
        if not self._AGENTS_MD_BACKUP.exists():
            return
        self._AGENTS_MD_BACKUP.replace(self._AGENTS_MD_PATH)
        logger.info("restored AGENTS.md from pre-benchmark backup")

    # ------------------------------------------------------------------
    # ClawVault observer (clawvault condition)
    # ------------------------------------------------------------------

    def _run_clawvault_observe(self) -> None:
        """Run ``clawvault observe --cron`` to process session transcripts.

        ClawVault's OpenClaw plugin hooks don't fire on gateway v2026.3.x
        (async registration issue), so the adapter calls the observer CLI
        directly after each session flush during seeding.
        """
        vault_path = os.environ.get("CLAWVAULT_PATH")
        if not vault_path:
            logger.warning("clawvault observe: CLAWVAULT_PATH not set, skipping")
            return

        agent_id = self._agent_id or "main"
        args = [
            "clawvault",
            "observe",
            "--cron",
            "--agent",
            agent_id,
            "-v",
            vault_path,
            "--min-new",
            "1",
        ]
        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = proc.stdout.strip()
            if output:
                logger.info("clawvault observe: %s", output)
        except Exception as exc:
            logger.warning("clawvault observe failed: %s", exc)

    # ------------------------------------------------------------------
    # Memory-core reindex
    # ------------------------------------------------------------------

    def reindex_memory(self) -> None:
        """Run ``openclaw memory index`` to reindex memory-core files.

        Should be called after seeding + settle so that memory files
        written during seed sessions are searchable during probes.
        """
        logger.info("reindex: updating memory-core index")
        try:
            proc = subprocess.run(
                ["openclaw", "memory", "index"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = proc.stdout.strip()
            if "updated" in output.lower() or "index" in output.lower():
                logger.info("reindex: memory-core index updated")
            else:
                logger.warning("reindex: unexpected output: %s", output[:200])
        except Exception as exc:
            logger.warning("reindex: failed (%s), continuing", exc)

    # ------------------------------------------------------------------
    # Date helpers (Engram V3 dataset)
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_dataset_date(raw: str) -> str | None:
        """Extract YYYY-MM-DD from Engram V3 date format.

        The dataset uses formats like ``"2026/02/20 (Fri) 14:43"``.
        Returns ``"2026-02-20"`` or *None* if parsing fails.
        """
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

                # ClawVault: run observer to process session transcripts
                # (plugin hooks don't fire on gateway v2026.3.x)
                if self._condition == "clawvault":
                    self._run_clawvault_observe()

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

        # Start a fresh session so prior probe Q&A doesn't leak into context.
        # ``--session-id`` alone doesn't isolate; ``/new`` forces a reset.
        self._call("/new", session_id=probe_session)

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
