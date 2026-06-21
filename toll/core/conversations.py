"""Server-side conversation system.

Conversations are separate from memories.
Many conversations may generate a small number of memories.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, List

from ..core.storage import Storage


class ConversationStore:
    def __init__(self, storage: Storage | None = None):
        self.db = storage or Storage()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create(
        self,
        title: str = "محادثة جديدة",
        workspace_type: str | None = None,
        workspace_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        conv_id = str(uuid.uuid4())
        now = self._now()
        self.db.conn.execute(
            """
            INSERT INTO conversations (id, title, workspace_type, workspace_id, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conv_id,
                title,
                workspace_type,
                workspace_id,
                json.dumps(metadata or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        self.db.conn.commit()
        return self.get(conv_id)

    def get(self, id: str) -> dict | None:
        row = self.db.conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "workspace_type": row["workspace_type"],
            "workspace_id": row["workspace_id"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "messages": self.list_messages(row["id"]),
        }

    def list(
        self,
        workspace_type: str | None = None,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> List[dict]:
        if workspace_type and workspace_id:
            rows = self.db.conn.execute(
                """
                SELECT * FROM conversations
                WHERE workspace_type = ? AND workspace_id = ?
                ORDER BY updated_at DESC LIMIT ?
                """,
                (workspace_type, workspace_id, limit),
            ).fetchall()
        else:
            rows = self.db.conn.execute(
                """
                SELECT * FROM conversations
                ORDER BY updated_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self.get(row["id"]) for row in rows]

    def update_title(self, id: str, title: str):
        self.db.conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, self._now(), id),
        )
        self.db.conn.commit()

    def delete(self, id: str) -> bool:
        cursor = self.db.conn.execute(
            "DELETE FROM conversations WHERE id = ?", (id,)
        )
        self.db.conn.commit()
        return cursor.rowcount > 0

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        if role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {role}")

        self.db.conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content,
                json.dumps(metadata or {}, ensure_ascii=False),
                self._now(),
            ),
        )
        self.db.conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (self._now(), conversation_id),
        )
        self.db.conn.commit()
        return self.get(conversation_id)

    def list_messages(self, conversation_id: str) -> List[dict]:
        rows = self.db.conn.execute(
            """
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"],
            }
            for row in rows
        ]
