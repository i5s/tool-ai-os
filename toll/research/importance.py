from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..ports.research_source import ResearchSource
from ..memory.graph import Memory


@dataclass
class ImportanceSignal:
    memory_id: str
    source_id: str | None
    topic: str
    initial_score: int
    current_score: int
    times_accessed: int
    last_boosted_at: str | None
    created_at: str


class ImportanceScorer:
    WEIGHTS = {
        "relevance": 0.4,
        "confidence": 0.3,
        "citations": 0.3,
    }

    CONTEXT_THRESHOLD = 4
    STALE_DAYS = 90

    def compute(self, source: ResearchSource) -> int:
        raw = (
            source.relevance_score * self.WEIGHTS["relevance"]
            + source.confidence_score * self.WEIGHTS["confidence"]
            + min(source.citation_count / 100, 1.0) * self.WEIGHTS["citations"]
        )
        return max(1, min(10, round(raw * 10)))

    def compute_from_findings(self, findings: list[str], source_count: int) -> int:
        if not findings:
            return 1
        base = min(len(findings), 5)
        source_bonus = min(source_count / 10, 2.0)
        return max(1, min(10, base + round(source_bonus)))

    def boost_on_retopic(self, current_score: int, times_retopic: int) -> int:
        boost = min(times_retopic, 3)
        return max(1, min(10, current_score + boost))

    def decay(
        self,
        current_score: int,
        days_since_access: int,
        max_days: int = 90,
        delta: int = -1,
    ) -> int:
        if days_since_access < max_days:
            return current_score
        return max(1, current_score + delta)

    def should_include_in_context(self, memory: Memory, threshold: int | None = None) -> bool:
        return memory.importance_score >= (threshold or self.CONTEXT_THRESHOLD)

    def _days_since(self, timestamp: str) -> int:
        try:
            accessed = datetime.fromisoformat(timestamp)
            return (datetime.now(timezone.utc) - accessed).days
        except (ValueError, TypeError):
            return 0
