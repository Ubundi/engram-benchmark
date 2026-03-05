"""
LLM Client — Thin wrapper around `claude -p` CLI for text generation.

Uses the Claude Code CLI (which works with Claude Max subscriptions)
instead of the Anthropic API directly.
"""

import logging
import subprocess
import time
from typing import List, Optional

from scripts.config import (
    API_REQUESTS_PER_MINUTE,
    API_RETRY_BACKOFF,
    API_RETRY_MAX,
    CLI_MAX_BUDGET_PER_CALL,
    CLI_MODEL,
    CLI_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Module-level rate limiter state
_request_times: List[float] = []


def _rate_limit() -> None:
    """Enforce rate limiting across all calls."""
    global _request_times
    now = time.time()
    _request_times = [t for t in _request_times if now - t < 60]
    if len(_request_times) >= API_REQUESTS_PER_MINUTE:
        sleep_time = 60 - (now - _request_times[0]) + 0.1
        if sleep_time > 0:
            logger.info(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
    _request_times.append(time.time())


def call(system_prompt: str, user_prompt: str, model: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """
    Call Claude via the CLI and return the response text.

    Args:
        system_prompt: System prompt for the model.
        user_prompt: User prompt (piped via stdin to handle long prompts).
        model: Model alias (default from config).
        timeout: Timeout in seconds (default from config).

    Returns:
        The model's text response.

    Raises:
        RuntimeError: If the call fails after all retries.
    """
    model = model or CLI_MODEL
    timeout = timeout or CLI_TIMEOUT

    cmd = [
        "claude",
        "-p",
        "--model", model,
        "--no-session-persistence",
        "--output-format", "text",
        "--max-budget-usd", str(CLI_MAX_BUDGET_PER_CALL),
    ]

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    for attempt in range(API_RETRY_MAX):
        try:
            _rate_limit()
            logger.debug(f"CLI call attempt {attempt + 1}/{API_RETRY_MAX} (model={model})")

            result = subprocess.run(
                cmd,
                input=user_prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                logger.warning(
                    f"CLI exited with code {result.returncode}: {stderr} "
                    f"(attempt {attempt + 1}/{API_RETRY_MAX})"
                )
                if attempt < API_RETRY_MAX - 1:
                    wait = API_RETRY_BACKOFF * (attempt + 1)
                    time.sleep(wait)
                    continue
                raise RuntimeError(f"CLI call failed after {API_RETRY_MAX} retries: {stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            logger.warning(f"CLI call timed out after {timeout}s (attempt {attempt + 1})")
            if attempt < API_RETRY_MAX - 1:
                wait = API_RETRY_BACKOFF * (attempt + 1)
                time.sleep(wait)
            else:
                raise RuntimeError(f"CLI call timed out after {API_RETRY_MAX} retries")

        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Install it with: npm install -g @anthropic-ai/claude-code"
            )

    raise RuntimeError(f"CLI call failed after {API_RETRY_MAX} retries")
