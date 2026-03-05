"""Logging helpers for consistent CLI output."""

from __future__ import annotations

import logging


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("benchmark")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
