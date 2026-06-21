"""Memory Graph repository.

Stores and retrieves long-term memory across:
- Global Memory
- Brand Memory
- University Memory
- Project Memory
- Knowledge Vault (type='knowledge')
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..core.connection_manager import ConnectionManager


@dataclass
class Memory:
    id: str
    type: str
    entity_id: str | None
    key: str
    value: Any
    importance_score: int
    source: str
    created_at: str
    updated_at: str
    last_accessed_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "entity_id": self.entity_id,
            "key": self.key,
            "value": self.value,
            "importance_score": self.importance_score,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed_at": self.last_accessed_at,
        }


class MemoryGraph:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _parse_value(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def _serialize_value(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _row_to_memory(self, row) -> Memory:
        return Memory(
            id=row["id"],
            type=row["type"],
            entity_id=row["entity_id"],
            key=row["key"],
            value=self._parse_value(row["value"]),
            importance_score=row["importance_score"],
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_accessed_at=row["last_accessed_at"],
        )

    def store(
        self,
        type: str,
        key: str,
        value: Any,
        entity_id: str | None = None,
        importance_score: int = 5,
        source: str = "unknown",
    ) -> Memory:
        existing = self.get(type, key, entity_id)
        mem_id = existing.id if existing else str(uuid.uuid4())
        now = self._now()

        if existing:
            self.cm.execute(
                """
                UPDATE memories
                SET value = ?, importance_score = ?, source = ?, updated_at = ?, last_accessed_at = ?
                WHERE id = ?
                """,
                (
                    self._serialize_value(value),
                    importance_score,
                    source,
                    now,
                    now,
                    mem_id,
                ),
            )
        else:
            self.cm.execute(
                """
                INSERT INTO memories (id, type, entity_id, key, value, importance_score, source, created_at, updated_at, last_accessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mem_id,
                    type,
                    entity_id,
                    key,
                    self._serialize_value(value),
                    importance_score,
                    source,
                    now,
                    now,
                    now,
                ),
            )
        self.cm.commit()
        return self.get_by_id(mem_id)

    def get(self, type: str, key: str, entity_id: str | None = None) -> Memory | None:
        row = self.cm.connection.execute(
            "SELECT * FROM memories WHERE type = ? AND entity_id IS ? AND key = ?",
            (type, entity_id, key),
        ).fetchone()
        return self._row_to_memory(row) if row else None

    def get_by_id(self, id: str) -> Memory | None:
        row = self.cm.connection.execute(
            "SELECT * FROM memories WHERE id = ?", (id,)
        ).fetchone()
        return self._row_to_memory(row) if row else None

    def query(
        self,
        type: str | None = None,
        entity_id: str | None = None,
        key_prefix: str | None = None,
        limit: int = 100,
    ) -> list[Memory]:
        sql = "SELECT * FROM memories WHERE 1=1"
        params = []
        if type:
            sql += " AND type = ?"
            params.append(type)
        if entity_id is not None:
            sql += " AND entity_id IS ?"
            params.append(entity_id)
        if key_prefix:
            sql += " AND key LIKE ?"
            params.append(f"{key_prefix}%")
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        rows = self.cm.connection.execute(sql, params).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def retrieve(
        self,
        brand_id: str | None = None,
        university_id: str | None = None,
        project_id: str | None = None,
        limit: int = 20,
    ) -> list[Memory]:
        rows = self.cm.connection.execute(
            """
            SELECT * FROM memories
            WHERE type = 'global'
               OR (type = 'brand' AND entity_id = ?)
               OR (type = 'university' AND entity_id = ?)
               OR (type = 'project' AND entity_id = ?)
               OR (type = 'knowledge' AND (entity_id IS NULL OR entity_id IN (?, ?, ?)))
            """,
            (brand_id, university_id, project_id, brand_id, university_id, project_id),
        ).fetchall()

        memories = [self._row_to_memory(row) for row in rows]

        def score(mem: Memory) -> float:
            accessed = datetime.fromisoformat(mem.last_accessed_at)
            days_since = (datetime.now(timezone.utc) - accessed).days
            recency = max(0, 10 - days_since)
            return (mem.importance_score * 2) + recency

        memories.sort(key=score, reverse=True)
        return memories[:limit]

    def touch(self, id: str):
        self.cm.execute(
            "UPDATE memories SET last_accessed_at = ? WHERE id = ?",
            (self._now(), id),
        )
        self.cm.commit()

    def adjust_importance(self, id: str, delta: int):
        memory = self.get_by_id(id)
        if not memory:
            raise ValueError(f"Memory {id} not found")
        new_score = max(1, min(10, memory.importance_score + delta))
        self.cm.execute(
            "UPDATE memories SET importance_score = ?, updated_at = ? WHERE id = ?",
            (new_score, self._now(), id),
        )
        self.cm.commit()

    def learn_from_feedback(
        self,
        type: str,
        key: str,
        entity_id: str | None,
        approved: bool,
    ):
        memory = self.get(type, key, entity_id)
        if not memory:
            return
        delta = 1 if approved else -1
        self.adjust_importance(memory.id, delta)

    def delete(self, id: str) -> bool:
        cursor = self.cm.execute("DELETE FROM memories WHERE id = ?", (id,))
        self.cm.commit()
        return cursor.rowcount > 0
