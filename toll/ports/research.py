from __future__ import annotations

from abc import ABC, abstractmethod

from .research_source import ResearchQuery, ResearchResult, ResearchSource


class ResearchProvider(ABC):
    name: str = "abstract"
    supported_styles: list[str] | None = None
    max_sources_per_query: int = 10

    @abstractmethod
    def search(self, query: ResearchQuery) -> ResearchResult:
        ...

    def search_by_ids(self, ids: list[str]) -> list[ResearchSource]:
        return []

    @abstractmethod
    def cite(self, source: ResearchSource, style: str = "apa") -> str:
        ...

    @abstractmethod
    def synthesize(
        self, sources: list[ResearchSource], topic: str
    ) -> str:
        ...

    def is_available(self) -> bool:
        return True

    def rate_limit_remaining(self) -> int | None:
        return None
