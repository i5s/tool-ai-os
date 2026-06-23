from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AgentAdapter(ABC):
    """Abstract interface for executing tasks via an external agent."""

    @abstractmethod
    def execute(self, task_id: str, title: str, description: str | None, context: dict | None = None) -> dict:
        """Run the task and return a result dict.

        Expected shape:
        {
            "status": "success" | "failed",
            "output": str,
            "duration_ms": int,
            "metadata": dict | None,
        }
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self) -> bool:
        """Return True if the adapter is usable (binary available, env set, etc)."""
        raise NotImplementedError
