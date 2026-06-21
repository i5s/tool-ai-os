"""Workspace Manager.

Manages active context for:
- Brand
- University
- Project

University workspaces support semester structures.
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..core.storage import Storage


@dataclass
class WorkspaceState:
    active_brand_id: str | None = None
    active_university_id: str | None = None
    active_project_id: str | None = None
    active_semester_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "active_brand_id": self.active_brand_id,
            "active_university_id": self.active_university_id,
            "active_project_id": self.active_project_id,
            "active_semester_id": self.active_semester_id,
        }


class WorkspaceManager:
    def __init__(self, storage: Storage | None = None, user_id: str = "default"):
        self.db = storage or Storage()
        self.user_id = user_id

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _parse_metadata(self, raw: str | None) -> dict:
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def create_workspace(self, type: str, name: str, metadata: dict | None = None) -> dict:
        if type not in ("brand", "university", "project"):
            raise ValueError(f"Invalid workspace type: {type}")

        ws_id = str(uuid.uuid4())
        now = self._now()
        self.db.conn.execute(
            "INSERT INTO workspaces (id, type, name, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (ws_id, type, name, json.dumps(metadata or {}, ensure_ascii=False), now, now),
        )
        self.db.conn.commit()
        return self.get_workspace(ws_id)

    def get_workspace(self, id: str) -> dict | None:
        row = self.db.conn.execute(
            "SELECT * FROM workspaces WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "type": row["type"],
            "name": row["name"],
            "metadata": self._parse_metadata(row["metadata"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_workspaces(self, type: str | None = None) -> list[dict]:
        if type:
            rows = self.db.conn.execute(
                "SELECT * FROM workspaces WHERE type = ? ORDER BY name",
                (type,),
            ).fetchall()
        else:
            rows = self.db.conn.execute(
                "SELECT * FROM workspaces ORDER BY type, name"
            ).fetchall()
        return [self.get_workspace(row["id"]) for row in rows]

    def create_semester(
        self, university_id: str, name: str, metadata: dict | None = None
    ) -> dict:
        university = self.get_workspace(university_id)
        if not university or university["type"] != "university":
            raise ValueError("Invalid university workspace")

        semester_id = str(uuid.uuid4())
        now = self._now()
        self.db.conn.execute(
            "INSERT INTO semesters (id, university_id, name, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                semester_id,
                university_id,
                name,
                json.dumps(metadata or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        self.db.conn.commit()
        return self.get_semester(semester_id)

    def get_semester(self, id: str) -> dict | None:
        row = self.db.conn.execute(
            "SELECT * FROM semesters WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "university_id": row["university_id"],
            "name": row["name"],
            "metadata": self._parse_metadata(row["metadata"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_semesters(self, university_id: str) -> list[dict]:
        rows = self.db.conn.execute(
            "SELECT * FROM semesters WHERE university_id = ? ORDER BY created_at DESC",
            (university_id,),
        ).fetchall()
        return [self.get_semester(row["id"]) for row in rows]

    def set_active(
        self,
        brand_id: str | None = None,
        university_id: str | None = None,
        project_id: str | None = None,
        semester_id: str | None = None,
    ):
        """Set active workspace components. None values leave existing state unchanged."""
        current = self.get_active()

        if brand_id is not None:
            current.active_brand_id = brand_id
        if university_id is not None:
            current.active_university_id = university_id
        if project_id is not None:
            current.active_project_id = project_id
        if semester_id is not None:
            current.active_semester_id = semester_id

        self.db.conn.execute(
            """
            INSERT INTO workspace_state (user_id, active_brand_id, active_university_id, active_project_id, active_semester_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                active_brand_id = excluded.active_brand_id,
                active_university_id = excluded.active_university_id,
                active_project_id = excluded.active_project_id,
                active_semester_id = excluded.active_semester_id,
                updated_at = excluded.updated_at
            """,
            (
                self.user_id,
                current.active_brand_id,
                current.active_university_id,
                current.active_project_id,
                current.active_semester_id,
                self._now(),
            ),
        )
        self.db.conn.commit()
        return current

    def get_active(self) -> WorkspaceState:
        row = self.db.conn.execute(
            "SELECT * FROM workspace_state WHERE user_id = ?", (self.user_id,)
        ).fetchone()
        if not row:
            return WorkspaceState()
        return WorkspaceState(
            active_brand_id=row["active_brand_id"],
            active_university_id=row["active_university_id"],
            active_project_id=row["active_project_id"],
            active_semester_id=row["active_semester_id"],
        )

    def clear_active(self):
        self.db.conn.execute(
            "DELETE FROM workspace_state WHERE user_id = ?",
            (self.user_id,),
        )
        self.db.conn.commit()

    def get_active_summary(self) -> dict:
        state = self.get_active()
        summary = {
            "brand": None,
            "university": None,
            "project": None,
            "semester": None,
        }
        if state.active_brand_id:
            summary["brand"] = self.get_workspace(state.active_brand_id)
        if state.active_university_id:
            summary["university"] = self.get_workspace(state.active_university_id)
        if state.active_project_id:
            summary["project"] = self.get_workspace(state.active_project_id)
        if state.active_semester_id:
            summary["semester"] = self.get_semester(state.active_semester_id)
        return summary
