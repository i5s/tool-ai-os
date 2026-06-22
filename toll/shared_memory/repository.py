from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from ..core.connection_manager import ConnectionManager
from .models import MemoryBlock, MemoryLink, MemoryBlockType, MemoryScope, MemoryLinkRelation


class SharedMemoryRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def create_block(self, block: MemoryBlock) -> MemoryBlock:
        block.id = block.id or str(uuid.uuid4())
        block.created_at = datetime.now(timezone.utc).isoformat()
        block.updated_at = block.created_at
        self.cm.execute(
            """
            INSERT INTO memory_blocks (id, type, scope, scope_id, title, content,
                                       created_by, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                block.id,
                block.type,
                block.scope,
                block.scope_id,
                block.title,
                block.content,
                block.created_by,
                block.metadata,
                block.created_at,
                block.updated_at,
            ),
        )
        self.cm.commit()
        return block

    def get_block(self, block_id: str) -> Optional[MemoryBlock]:
        row = self.cm.connection.execute(
            "SELECT * FROM memory_blocks WHERE id = ?", (block_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_block(row)

    def list_blocks(
        self,
        block_type: Optional[str] = None,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        created_by: Optional[str] = None,
        title_contains: Optional[str] = None,
        limit: int = 100,
    ) -> list[MemoryBlock]:
        parts = ["SELECT * FROM memory_blocks WHERE 1=1"]
        params: list[object] = []
        if block_type:
            parts.append("AND type = ?")
            params.append(block_type)
        if scope:
            parts.append("AND scope = ?")
            params.append(scope)
        if scope_id:
            parts.append("AND scope_id = ?")
            params.append(scope_id)
        if created_by:
            parts.append("AND created_by = ?")
            params.append(created_by)
        if title_contains:
            parts.append("AND title LIKE ?")
            params.append(f"%{title_contains}%")
        parts.append("ORDER BY created_at DESC LIMIT ?")
        params.append(limit)
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_block(r) for r in rows]

    def search_blocks(self, query: str, limit: int = 50) -> list[MemoryBlock]:
        q = f"%{query}%"
        rows = self.cm.connection.execute(
            """
            SELECT * FROM memory_blocks
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (q, q, limit),
        ).fetchall()
        return [self._row_to_block(r) for r in rows]

    def update_block(self, block_id: str, **fields) -> Optional[MemoryBlock]:
        allowed = {"type", "scope", "scope_id", "title", "content", "created_by", "metadata"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            block = self.get_block(block_id)
            return block
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        params = list(updates.values()) + [block_id]
        self.cm.execute(
            f"UPDATE memory_blocks SET {set_clause} WHERE id = ?", params
        )
        self.cm.commit()
        if self.cm.connection.total_changes == 0:
            return None
        return self.get_block(block_id)

    def delete_block(self, block_id: str) -> bool:
        cursor = self.cm.execute("DELETE FROM memory_blocks WHERE id = ?", (block_id,))
        self.cm.commit()
        return cursor.rowcount > 0

    def create_link(self, link: MemoryLink) -> MemoryLink:
        link.id = link.id or str(uuid.uuid4())
        link.created_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """
            INSERT INTO memory_links (id, source_id, target_id, relation, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (link.id, link.source_id, link.target_id, link.relation, link.created_at),
        )
        self.cm.commit()
        return link

    def get_link(self, link_id: str) -> Optional[MemoryLink]:
        row = self.cm.connection.execute(
            "SELECT * FROM memory_links WHERE id = ?", (link_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_link(row)

    def list_links(self, source_id: Optional[str] = None, target_id: Optional[str] = None) -> list[MemoryLink]:
        parts = ["SELECT * FROM memory_links WHERE 1=1"]
        params: list[object] = []
        if source_id:
            parts.append("AND source_id = ?")
            params.append(source_id)
        if target_id:
            parts.append("AND target_id = ?")
            params.append(target_id)
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_link(r) for r in rows]

    def delete_link(self, link_id: str) -> bool:
        cursor = self.cm.execute("DELETE FROM memory_links WHERE id = ?", (link_id,))
        self.cm.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_block(row) -> MemoryBlock:
        return MemoryBlock(
            id=row["id"],
            type=row["type"],
            scope=row["scope"],
            scope_id=row["scope_id"] if "scope_id" in row.keys() else None,
            title=row["title"],
            content=row["content"] if "content" in row.keys() else None,
            created_by=row["created_by"] if "created_by" in row.keys() else None,
            metadata=row["metadata"] if "metadata" in row.keys() else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_link(row) -> MemoryLink:
        return MemoryLink(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation=row["relation"],
            created_at=row["created_at"],
        )
