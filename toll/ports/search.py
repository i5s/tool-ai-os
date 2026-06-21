"""Abstract port for search providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchPort(ABC):
    """Port for search providers."""

    name: str = "abstract"

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Execute a search and return results."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
        ...
