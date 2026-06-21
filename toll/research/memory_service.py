from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from ..core.connection_manager import ConnectionManager
from ..memory.graph import Memory, MemoryGraph
from ..model.artifact import Artifact
from ..ports.research_source import ResearchSource
from .importance import ImportanceScorer

logger = logging.getLogger(__name__)

_TOPIC_PREFIX = "research:topic:"
_SOURCE_PREFIX = "research:source:"
_PROJECT_PREFIX = "research:project:"


def _normalize_topic(topic: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\u0600-\u06FF\s-]", "", topic).strip().lower()[:100]


def _source_key(source: ResearchSource) -> str:
    if source.doi:
        return f"{_SOURCE_PREFIX}{hashlib.sha256(source.doi.lower().encode()).hexdigest()[:16]}"
    if source.url:
        norm = re.sub(r"^https?://", "", source.url.strip().rstrip("/")).lower()
        return f"{_SOURCE_PREFIX}{hashlib.sha256(norm.encode()).hexdigest()[:16]}"
    title_hash = hashlib.sha256((source.title or "").strip().lower().encode()).hexdigest()[:16]
    return f"{_SOURCE_PREFIX}{title_hash}"


def _extract_topic_keywords(topic: str) -> list[str]:
    words = re.split(r"[\s,;:،.]+", _normalize_topic(topic))
    return [w for w in words if len(w) > 2][:10]


class ResearchMemoryService:
    def __init__(
        self,
        cm: ConnectionManager,
        memory_graph: MemoryGraph | None = None,
    ):
        self.cm = cm
        self.memory = memory_graph or MemoryGraph(cm=cm)
        self.scorer = ImportanceScorer()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def index_research(
        self,
        artifact: Artifact,
        sources: list[ResearchSource],
        workspace_type: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, int]:
        counts: dict[str, int] = {"global": 0, "knowledge": 0, "project": 0}
        topic = artifact.title
        content = artifact.content
        synopsis = content.get("synopsis", "") if isinstance(content, dict) else ""
        key_findings = content.get("key_findings", []) if isinstance(content, dict) else []

        norm_topic = _normalize_topic(topic)
        keywords = _extract_topic_keywords(topic)

        global_finding_score = self.scorer.compute_from_findings(key_findings, len(sources))

        try:
            self.memory.store(
                type="global",
                key=f"{_TOPIC_PREFIX}{norm_topic}",
                value={
                    "summary": synopsis,
                    "findings": key_findings,
                    "source_count": len(sources),
                    "artifact_id": artifact.id,
                    "keywords": keywords,
                    "indexed_at": self._now(),
                },
                importance_score=global_finding_score,
                source="research",
            )
            counts["global"] = 1
        except Exception as e:
            logger.warning("Failed to store global research memory: %s", e)

        for source in sources:
            try:
                self._index_source(source, artifact.id)
                counts["knowledge"] += 1
            except Exception as e:
                logger.warning("Failed to index source '%s': %s", source.title, e)

        if workspace_type and workspace_id:
            try:
                self.memory.store(
                    type=workspace_type,
                    entity_id=workspace_id,
                    key=f"{_PROJECT_PREFIX}{workspace_id}:{norm_topic}",
                    value={
                        "summary": synopsis,
                        "source_count": len(sources),
                        "artifact_id": artifact.id,
                        "indexed_at": self._now(),
                    },
                    importance_score=global_finding_score,
                    source="research",
                )
                counts["project"] = 1
            except Exception as e:
                logger.warning("Failed to store project research memory: %s", e)

        return counts

    def index_source(
        self,
        source: ResearchSource,
        artifact_id: str | None = None,
    ) -> Memory | None:
        return self._index_source(source, artifact_id)

    def _index_source(
        self,
        source: ResearchSource,
        artifact_id: str | None = None,
    ) -> Memory | None:
        key = _source_key(source)
        importance = self.scorer.compute(source)
        value = {
            "title": source.title,
            "authors": source.authors,
            "year": source.year,
            "doi": source.doi,
            "url": source.url,
            "abstract": source.abstract or "",
            "journal": source.journal,
            "source_type": source.source_type,
            "relevance_score": source.relevance_score,
            "confidence_score": source.confidence_score,
            "citation_count": source.citation_count,
            "artifact_id": artifact_id,
            "indexed_at": self._now(),
        }

        memory = self.memory.store(
            type="knowledge",
            entity_id=source.id or None,
            key=key,
            value=value,
            importance_score=importance,
            source=source.provider or "research",
        )

        self._store_meta(
            memory_id=memory.id,
            artifact_id=artifact_id,
            source_id=source.id or None,
            topic=_normalize_topic(source.title),
            keywords=_extract_topic_keywords(source.title),
        )

        return memory

    def _store_meta(
        self,
        memory_id: str,
        artifact_id: str | None,
        source_id: str | None,
        topic: str,
        keywords: list[str],
    ):
        now = self._now()
        self.cm.execute(
            """INSERT OR REPLACE INTO research_memory_meta
               (memory_id, artifact_id, source_id, topic, keywords, times_accessed, times_retopic_hit, created_at)
               VALUES (?, ?, ?, ?, ?, 0, 0, ?)""",
            (memory_id, artifact_id, source_id, topic, json.dumps(keywords, ensure_ascii=False), now),
        )
        self.cm.commit()

    def _update_meta(self, memory_id: str, **kwargs):
        sets = []
        params = []
        for key, value in kwargs.items():
            sets.append(f"{key} = ?")
            params.append(value)
        if not sets:
            return
        params.append(memory_id)
        self.cm.execute(
            f"UPDATE research_memory_meta SET {', '.join(sets)} WHERE memory_id = ?",
            params,
        )
        self.cm.commit()

    def get_relevant_memories(
        self,
        message: str,
        limit: int = 5,
        min_importance: int = 4,
    ) -> list[Memory]:
        keywords = _extract_topic_keywords(message)
        if not keywords:
            return []

        all_memories: list[Memory] = []
        seen_ids: set[str] = set()

        for keyword in keywords:
            rows = self.cm.connection.execute(
                """SELECT m.* FROM memories m
                   INNER JOIN research_memory_meta rm ON rm.memory_id = m.id
                   WHERE rm.keywords LIKE ? AND m.importance_score >= ?
                   ORDER BY m.importance_score DESC, m.last_accessed_at DESC
                   LIMIT ?""",
                (f"%{keyword}%", min_importance, limit),
            ).fetchall()
            for row in rows:
                mem = self.memory._row_to_memory(row) if hasattr(self.memory, '_row_to_memory') else self._row_to_memory(row)
                if mem.id not in seen_ids:
                    seen_ids.add(mem.id)
                    all_memories.append(mem)

            if len(all_memories) >= limit:
                break

        return all_memories[:limit]

    def _row_to_memory(self, row) -> Memory:
        return Memory(
            id=row["id"],
            type=row["type"],
            entity_id=row["entity_id"],
            key=row["key"],
            value=row["value"],
            importance_score=row["importance_score"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_accessed_at=row["last_accessed_at"],
        )

    def get_knowledge_vault(
        self,
        topic: str | None = None,
        limit: int = 50,
    ) -> list[Memory]:
        if topic:
            norm = _normalize_topic(topic)
            rows = self.cm.connection.execute(
                """SELECT m.* FROM memories m
                   INNER JOIN research_memory_meta rm ON rm.memory_id = m.id
                   WHERE m.type = 'knowledge' AND (rm.topic LIKE ? OR rm.keywords LIKE ?)
                   ORDER BY m.importance_score DESC, m.last_accessed_at DESC
                   LIMIT ?""",
                (f"%{norm}%", f"%{norm}%", limit),
            ).fetchall()
        else:
            rows = self.cm.connection.execute(
                """SELECT m.* FROM memories m
                   INNER JOIN research_memory_meta rm ON rm.memory_id = m.id
                   WHERE m.type = 'knowledge'
                   ORDER BY m.importance_score DESC, m.last_accessed_at DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def boost_on_retopic(
        self,
        topic: str,
        delta: int = 1,
    ) -> int:
        norm_topic = _normalize_topic(topic)
        keyword = _extract_topic_keywords(topic)
        if not keyword:
            return 0

        memory_rows = self.cm.connection.execute(
            """SELECT rm.memory_id FROM research_memory_meta rm
               WHERE rm.topic LIKE ? OR rm.keywords LIKE ?""",
            (f"%{norm_topic}%", f"%{keyword[0]}%"),
        ).fetchall()

        now = self._now()
        count = 0
        for row in memory_rows:
            mem = self.memory.get_by_id(row["memory_id"])
            if not mem:
                continue
            self.memory.adjust_importance(mem.id, delta)
            self._update_meta(
                mem.id,
                times_retopic_hit=(
                    self.cm.connection.execute(
                        "SELECT times_retopic_hit FROM research_memory_meta WHERE memory_id = ?",
                        (mem.id,),
                    ).fetchone()["times_retopic_hit"]
                    + 1
                ),
                last_boosted_at=now,
            )
            count += 1
        return count

    def decay_stale_memories(
        self,
        max_days: int = 90,
        delta: int = -1,
    ) -> int:
        cutoff = datetime.now(timezone.utc).isoformat()
        rows = self.cm.connection.execute(
            """SELECT m.* FROM memories m
               INNER JOIN research_memory_meta rm ON rm.memory_id = m.id
               WHERE m.last_accessed_at < ?""",
            (cutoff,),
        ).fetchall()

        count = 0
        now = datetime.now(timezone.utc)
        for row in rows:
            mem = self._row_to_memory(row)
            try:
                last = mem.last_accessed_at
                if last.endswith("Z"):
                    last = last[:-1] + "+00:00"
                accessed = datetime.fromisoformat(last)
                if accessed.tzinfo is None:
                    accessed = accessed.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
            days_since = (now - accessed).days
            if days_since >= max_days:
                new_score = self.scorer.decay(mem.importance_score, days_since, max_days, delta)
                if new_score != mem.importance_score:
                    self.cm.execute(
                        "UPDATE memories SET importance_score = ?, updated_at = ? WHERE id = ?",
                        (new_score, self._now(), mem.id),
                    )
                    self.cm.commit()
                    count += 1
        return count

    def touch_memory(self, memory_id: str):
        self.memory.touch(memory_id)
        self._update_meta(
            memory_id,
            times_accessed=(
                self.cm.connection.execute(
                    "SELECT times_accessed FROM research_memory_meta WHERE memory_id = ?",
                    (memory_id,),
                ).fetchone()["times_accessed"]
                + 1
            ),
        )
