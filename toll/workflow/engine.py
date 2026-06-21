"""Workflow Engine.

Executes Plans produced by the Planner. Handles approval checkpoints,
persistence, and state transitions.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from ..core.connection_manager import ConnectionManager


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "workflow_completed"
    FAILED = "workflow_failed"


@dataclass
class Workflow:
    id: str
    plan: dict
    status: WorkflowStatus
    created_at: str
    updated_at: str
    result: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class WorkflowEngine:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm
        self._handlers: dict[str, Callable] = {}

    def register_handler(self, intent: str, handler: Callable):
        self._handlers[intent] = handler

    def create(self, plan: dict, metadata: dict | None = None) -> Workflow:
        wf_id = str(uuid.uuid4())
        now = self._now()
        plan_copy = dict(plan)

        status = WorkflowStatus.PENDING
        if plan_copy.get("can_auto_execute"):
            status = WorkflowStatus.APPROVED

        workflow = Workflow(
            id=wf_id,
            plan=plan_copy,
            status=status,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._persist(workflow)
        return workflow

    def create_and_run(self, plan: dict, metadata: dict | None = None) -> Workflow:
        """Create a workflow and immediately run it if auto-executable."""
        workflow = self.create(plan, metadata)
        if workflow.status == WorkflowStatus.APPROVED:
            workflow = self.run(workflow.id)
        return workflow

    def approve(self, workflow_id: str) -> Workflow:
        workflow = self.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        if workflow.status != WorkflowStatus.PENDING:
            raise ValueError(f"Cannot approve workflow in status {workflow.status}")

        workflow.status = WorkflowStatus.APPROVED
        workflow.updated_at = self._now()
        self._persist(workflow)
        return workflow

    def reject(self, workflow_id: str, reason: str = "") -> Workflow:
        workflow = self.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        if workflow.status != WorkflowStatus.PENDING:
            raise ValueError(f"Cannot reject workflow in status {workflow.status}")

        workflow.status = WorkflowStatus.REJECTED
        workflow.error = reason or "Rejected by user"
        workflow.updated_at = self._now()
        self._persist(workflow)
        return workflow

    def run(self, workflow_id: str) -> Workflow:
        workflow = self.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        if workflow.status not in (WorkflowStatus.APPROVED, WorkflowStatus.RUNNING):
            raise ValueError(f"Cannot run workflow in status {workflow.status}")

        workflow.status = WorkflowStatus.RUNNING
        workflow.updated_at = self._now()
        self._persist(workflow)

        intent = workflow.plan.get("intent", "chat")
        handler = self._handlers.get(intent)

        try:
            if handler:
                result = handler(workflow.plan, workflow.metadata)
            else:
                result = {"note": f"No handler registered for intent '{intent}'"}

            workflow.result = result
            workflow.status = WorkflowStatus.COMPLETED
        except Exception as e:
            workflow.error = str(e)
            workflow.status = WorkflowStatus.FAILED

        workflow.updated_at = self._now()
        self._persist(workflow)
        return workflow

    def get(self, workflow_id: str) -> Workflow | None:
        row = self.cm.connection.execute(
            "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_workflow(row)

    def list(self, status: WorkflowStatus | None = None, limit: int = 100) -> list[Workflow]:
        if status:
            rows = self.cm.connection.execute(
                "SELECT * FROM workflows WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                (status.value, limit),
            ).fetchall()
        else:
            rows = self.cm.connection.execute(
                "SELECT * FROM workflows ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_workflow(row) for row in rows]

    def recover(self) -> list[Workflow]:
        """Mark running workflows as failed after unexpected shutdown.

        Called at server startup. Approved and pending workflows are left
        for normal processing.
        """
        recovered: list[Workflow] = []
        now = self._now()
        rows = self.cm.connection.execute(
            "SELECT * FROM workflows WHERE status = ?", (WorkflowStatus.RUNNING.value,)
        ).fetchall()
        for row in rows:
            wf = self._row_to_workflow(row)
            wf.status = WorkflowStatus.FAILED
            wf.error = "Server restart interrupted execution"
            wf.updated_at = now
            self._persist(wf)
            recovered.append(wf)
        return recovered

    def _persist(self, workflow: Workflow):
        self.cm.execute(
            """
            INSERT INTO workflows (id, plan, status, result, error, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                plan = excluded.plan,
                status = excluded.status,
                result = excluded.result,
                error = excluded.error,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at
            """,
            (
                workflow.id,
                json.dumps(workflow.plan, ensure_ascii=False),
                workflow.status.value,
                json.dumps(workflow.result, ensure_ascii=False) if workflow.result is not None else None,
                workflow.error,
                json.dumps(workflow.metadata, ensure_ascii=False),
                workflow.created_at,
                workflow.updated_at,
            ),
        )
        self.cm.commit()

    def _row_to_workflow(self, row) -> Workflow:
        return Workflow(
            id=row["id"],
            plan=json.loads(row["plan"]),
            status=WorkflowStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
