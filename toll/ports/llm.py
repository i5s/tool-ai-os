"""Abstract port for Large Language Model providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str | None = None
    finish_reason: str | None = None


class LLMProvider(ABC):
    """Port for LLM providers."""

    name: str = "abstract"

    @abstractmethod
    async def ask(self, prompt: str, system: str | None = None) -> LLMResponse:
        """Send a prompt and return the response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
        ...
