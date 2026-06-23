from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone

from .models import AgentExecution


class ExecutionRepository:
    def __init__(self, cm):
        self.cm = cm

    def create_execution(self, execution: AgentExecution) -> AgentExecution:
        self.cm.execute(
            """INSERT INTO agent_executions
            (id, task_id, agent_id, status, started_at, execution_metadata)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                execution.id,
                execution.task_id,
                execution.agent_id,
                execution.status,
                execution.started_at,
                execution.execution_metadata,
            ),
        )
        self.cm.commit()
        return execution

    def complete_execution(self, execution_id: str, status: str, duration_ms: int,
                           stdout: str, stderr: str, metadata: Optional[str] = None) -> Optional[AgentExecution]:
        completed_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """UPDATE agent_executions
            SET status = ?, completed_at = ?, duration_ms = ?, stdout = ?, stderr = ?, execution_metadata = ?
            WHERE id = ?""",
            (status, completed_at, duration_ms, stdout, stderr, metadata, execution_id),
        )
        self.cm.commit()
        if self.cm.connection.total_changes == 0:
            return None
        return self.get_execution(execution_id)

    def fail_execution(self, execution_id: str, duration_ms: int, stderr: str,
                       metadata: Optional[str] = None) -> Optional[AgentExecution]:
        return self.complete_execution(execution_id, "failed", duration_ms, "", stderr, metadata)

    def get_execution(self, execution_id: str) -> Optional[AgentExecution]:
        row = self.cm.execute("SELECT * FROM agent_executions WHERE id = ?", (execution_id,)).fetchone()
        return self._row_to_execution(row) if row else None

    def list_executions(self, task_id: Optional[str] = None, agent_id: Optional[str] = None,
                        status: Optional[str] = None, limit: int = 100) -> list[AgentExecution]:
        query = "SELECT * FROM agent_executions"
        conditions = []
        params = []
        if task_id is not None:
            conditions.append("task_id = ?")
            params.append(task_id)
        if agent_id is not None:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        rows = self.cm.execute(query, params).fetchall()
        return [self._row_to_execution(r) for r in rows]

    @staticmethod
    def _row_to_execution(row) -> AgentExecution:
        def safe_int(val):
            try:
                return int(val)
            except Exception:
                return None
        return AgentExecution(
            id=row["id"],
            task_id=row["task_id"],
            agent_id=row["agent_id"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"] if "completed_at" in row.keys() else None,
            duration_ms=safe_int(row["duration_ms"]) if "duration_ms" in row.keys() and row["duration_ms"] is not None else None,
            stdout=row["stdout"] if "stdout" in row.keys() else None,
            stderr=row["stderr"] if "stderr" in row.keys() else None,
            execution_metadata=row["execution_metadata"] if "execution_metadata" in row.keys() else None,
            created_at=row["created_at"],
        )
