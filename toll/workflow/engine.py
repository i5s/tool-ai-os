"""Workflow Engine.

Executes Plans produced by the Planner. Handles approval checkpoints,
persistence, and state transitions.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from ..core.storage import Storage


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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
    def __init__(self, storage: Storage | None = None):
        self.db = storage or Storage()
        self._handlers: dict[str, Callable] = {}

    def register_handler(self, intent: str, handler: Callable):
        """Register a handler function for a given intent."""
        self._handlers[intent] = handler

    def create(self, plan: dict, metadata: dict | None = None) -> Workflow:
        """Create a workflow from a plan."""
        wf_id = str(uuid.uuid4())
        now = self._now()
        plan_copy = dict(plan)

        # Auto-execute workflows skip pending
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

    def approve(self, workflow_id: str) -> Workflow:
        """Approve a pending workflow."""
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
        """Reject a pending workflow."""
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
        """Execute an approved workflow."""
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
        row = self.db.conn.execute(
            "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_workflow(row)

    def list(self, status: WorkflowStatus | None = None, limit: int = 100) -> list[Workflow]:
        if status:
            rows = self.db.conn.execute(
                "SELECT * FROM workflows WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                (status.value, limit),
            ).fetchall()
        else:
            rows = self.db.conn.execute(
                "SELECT * FROM workflows ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_workflow(row) for row in rows]

    def _persist(self, workflow: Workflow):
        import json

        self.db.conn.execute(
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
        self.db.conn.commit()

    def _row_to_workflow(self, row) -> Workflow:
        import json

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
