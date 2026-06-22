from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from ..core.connection_manager import ConnectionManager
from .models import Task, TaskEvent, TaskStatus, TaskPriority, TaskEventType


class TaskRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def create_task(self, task: Task) -> Task:
        task.id = task.id or str(uuid.uuid4())
        task.created_at = datetime.now(timezone.utc).isoformat()
        task.updated_at = task.created_at
        self.cm.execute(
            "INSERT INTO tasks (id, title, description, status, priority,"
            " created_by, assigned_agent_id, created_at, updated_at, completed_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task.id,
                task.title,
                task.description,
                task.status,
                task.priority,
                task.created_by,
                task.assigned_agent_id,
                task.created_at,
                task.updated_at,
                task.completed_at,
            ),
        )
        self.cm.commit()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        row = self.cm.connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    def list_tasks(
        self,
        status: Optional[str] = None,
        assigned_agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Task]:
        parts = ["SELECT * FROM tasks WHERE 1=1"]
        params: list = []
        if status:
            parts.append("AND status = ?")
            params.append(status)
        if assigned_agent_id:
            parts.append("AND assigned_agent_id = ?")
            params.append(assigned_agent_id)
        parts.append("ORDER BY created_at DESC LIMIT ?")
        params.append(limit)
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def update_task(self, task_id: str, **fields) -> Optional[Task]:
        allowed = {"title", "description", "status", "priority", "assigned_agent_id", "completed_at"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if updates.get("status") in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
            updates["completed_at"] = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        if not updates:
            return self.get_task(task_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        params = list(updates.values()) + [task_id]
        self.cm.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", params)
        self.cm.commit()
        if self.cm.connection.total_changes == 0:
            return None
        return self.get_task(task_id)

    def delete_task(self, task_id: str) -> bool:
        cursor = self.cm.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.cm.commit()
        return cursor.rowcount > 0

    def add_event(self, event: TaskEvent) -> TaskEvent:
        event.id = event.id or str(uuid.uuid4())
        event.created_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            "INSERT INTO task_events (id, task_id, event_type, actor, payload, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (event.id, event.task_id, event.event_type, event.actor, event.payload, event.created_at),
        )
        self.cm.commit()
        return event

    def list_events(self, task_id: str) -> list[TaskEvent]:
        rows = self.cm.connection.execute(
            "SELECT * FROM task_events WHERE task_id = ? ORDER BY created_at ASC", (task_id,)
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    @staticmethod
    def _row_to_task(row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"] if "description" in row.keys() else None,
            status=row["status"],
            priority=row["priority"],
            created_by=row["created_by"] if "created_by" in row.keys() else None,
            assigned_agent_id=row["assigned_agent_id"] if "assigned_agent_id" in row.keys() else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            completed_at=row["completed_at"] if "completed_at" in row.keys() else None,
        )

    @staticmethod
    def _row_to_event(row) -> TaskEvent:
        return TaskEvent(
            id=row["id"],
            task_id=row["task_id"],
            event_type=row["event_type"],
            actor=row["actor"] if "actor" in row.keys() else None,
            payload=row["payload"] if "payload" in row.keys() else None,
            created_at=row["created_at"],
        )
