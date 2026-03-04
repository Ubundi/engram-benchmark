"""Base interface for benchmark agent adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Abstract adapter that maps a task into a model prediction payload."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable adapter name used in reports."""

    @abstractmethod
    def predict(self, task: dict[str, Any]) -> dict[str, Any]:
        """Return a prediction object with at least an `output` field."""
