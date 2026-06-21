from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from ..core.connection_manager import ConnectionManager
from ..ports.research_source import ResearchSource


@dataclass
class DedupDecision:
    source_a_id: str
    source_b_id: str
    strategy: str
    similarity_score: float
    merged_into: str
    created_at: str = ""


class DedupEngine:
    def __init__(self, cm: ConnectionManager | None = None):
        self.cm = cm

    def dedup(
        self, sources: list[ResearchSource]
    ) -> list[ResearchSource]:
        return self.deduplicate(sources)

    def deduplicate(
        self, sources: list[ResearchSource]
    ) -> list[ResearchSource]:
        if len(sources) <= 1:
            return sources

        decisions: list[DedupDecision] = []
        merged_ids: set[int] = set()
        result: list[ResearchSource] = []
        id_map: list[int] = list(range(len(sources)))

        def resolve(i: int) -> int:
            while id_map[i] != i:
                i = id_map[i]
            return i

        def merge(i: int, j: int):
            ri, rj = resolve(i), resolve(j)
            if ri != rj:
                id_map[rj] = ri

        strategies: list[tuple[str, Callable[[int, int, list[ResearchSource]], float]]] = [
            ("doi", self._doi_similarity),
            ("url", self._url_similarity),
            ("title", self._title_similarity),
            ("author_year", self._author_year_similarity),
        ]

        for strategy_name, sim_fn in strategies:
            for i in range(len(sources)):
                if i in merged_ids:
                    continue
                for j in range(i + 1, len(sources)):
                    if j in merged_ids:
                        continue
                    if resolve(i) == resolve(j):
                        continue
                    score = sim_fn(i, j, sources)
                    if score >= self._threshold(strategy_name):
                        merge(i, j)
                        merged_ids.add(j)
                        decisions.append(
                            DedupDecision(
                                source_a_id=str(i),
                                source_b_id=str(j),
                                strategy=strategy_name,
                                similarity_score=score,
                                merged_into=str(i),
                            )
                        )

        seen_roots: set[int] = set()
        for i in range(len(sources)):
            root = resolve(i)
            if root not in seen_roots:
                seen_roots.add(root)
                result.append(sources[i])

        if self.cm:
            self._log_decisions(decisions)

        return result

    def _threshold(self, strategy: str) -> float:
        thresholds = {
            "doi": 1.0,
            "url": 1.0,
            "title": 0.85,
            "author_year": 0.95,
            "hash": 1.0,
        }
        return thresholds.get(strategy, 0.8)

    def _doi_similarity(self, i: int, j: int, sources: list[ResearchSource]) -> float:
        a, b = sources[i], sources[j]
        if a.doi and b.doi and a.doi.lower() == b.doi.lower():
            return 1.0
        return 0.0

    def _url_similarity(self, i: int, j: int, sources: list[ResearchSource]) -> float:
        a, b = sources[i], sources[j]
        if a.url and b.url:
            norm_a = self._normalize_url(a.url)
            norm_b = self._normalize_url(b.url)
            if norm_a and norm_b and norm_a == norm_b:
                return 1.0
        return 0.0

    def _title_similarity(self, i: int, j: int, sources: list[ResearchSource]) -> float:
        a, b = sources[i], sources[j]
        if not a.title or not b.title:
            return 0.0
        return self._levenshtein_ratio(a.title.lower(), b.title.lower())

    def _author_year_similarity(self, i: int, j: int, sources: list[ResearchSource]) -> float:
        a, b = sources[i], sources[j]
        if a.year and b.year and a.year != b.year:
            return 0.0
        if not a.authors or not b.authors:
            return 0.0
        a_norm = sorted(
            self._normalize_author(author) for author in a.authors
        )
        b_norm = sorted(
            self._normalize_author(author) for author in b.authors
        )
        if a_norm == b_norm:
            return 1.0
        return 0.0

    def _hash_similarity(
        self, text_a: str, text_b: str
    ) -> float:
        if not text_a or not text_b:
            return 0.0
        hash_a = hashlib.sha256(text_a[:1024].encode()).hexdigest()
        hash_b = hashlib.sha256(text_b[:1024].encode()).hexdigest()
        return 1.0 if hash_a == hash_b else 0.0

    def _normalize_url(self, url: str) -> str | None:
        url = url.strip().rstrip("/")
        url = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
        url = re.sub(r"^www\.", "", url, flags=re.IGNORECASE)
        return url.lower() if url else None

    def _normalize_author(self, author: str) -> str:
        name = re.sub(r"[^\w\s]", "", author).strip().lower()
        parts = name.split()
        return " ".join(sorted(set(parts)))

    def _levenshtein_ratio(self, a: str, b: str) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + cost,
                )
        dist = dp[m][n]
        return 1.0 - (dist / max(m, n))

    def _log_decisions(self, decisions: list[DedupDecision]):
        if not self.cm:
            return
        now = datetime.now(timezone.utc).isoformat()
        for d in decisions:
            d.created_at = now
            self.cm.execute(
                """INSERT OR IGNORE INTO research_dedup_log
                   (id, source_a_id, source_b_id, strategy, similarity_score, merged_into, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid4()),
                    d.source_a_id,
                    d.source_b_id,
                    d.strategy,
                    d.similarity_score,
                    d.merged_into,
                    now,
                ),
            )
        if self.cm:
            self.cm.commit()
