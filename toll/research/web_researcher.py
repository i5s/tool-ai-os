from __future__ import annotations

from ..adapters.search.duckduckgo import DuckDuckGoSearch
from ..ports.research import ResearchProvider
from ..ports.research_source import ResearchQuery, ResearchResult, ResearchSource


class WebResearcher(ResearchProvider):
    name = "web"
    supported_styles = ["apa"]
    max_sources_per_query = 10

    def __init__(self, timeout: float = 10.0):
        self.searcher = DuckDuckGoSearch(timeout=timeout)

    def search(self, query: ResearchQuery) -> ResearchResult:
        try:
            raw_results = self.searcher.search_sync(
                query.query, max_results=query.max_sources
            )
        except Exception as e:
            return ResearchResult(error=str(e), provider=self.name)

        sources = []
        for r in raw_results:
            source = ResearchSource(
                title=r.title,
                url=r.url,
                relevance_score=0.5,
                confidence_score=0.3,
                source_type="web",
                provider=self.name,
                citation=r.snippet or "",
                language="en",
            )
            sources.append(source)

        return ResearchResult(sources=sources, provider=self.name)

    def cite(self, source: ResearchSource, style: str = "apa") -> str:
        from .citation_engine import CitationEngine

        engine = CitationEngine()
        return engine.format(source, style)

    def synthesize(
        self, sources: list[ResearchSource], topic: str
    ) -> str:
        parts = [f"Synthesis of {len(sources)} sources about '{topic}':\n"]
        for source in sources:
            title = source.title
            snippet = (
                (source.citation or "")[:200] if source.citation else ""
            )
            parts.append(f"- {title}: {snippet}")
        return "\n".join(parts)

    def is_available(self) -> bool:
        return True

    def rate_limit_remaining(self) -> int | None:
        return None
