from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import (
    RuntimeJob,
    RuntimeAssignment,
    RuntimeResult,
    RuntimeMemory,
    JobStatus,
)


class RuntimeRepository:
    def __init__(self, cm):
        self.cm = cm

    def create_job(self, job: RuntimeJob) -> RuntimeJob:
        if not job.id:
            job.id = str(uuid.uuid4())
        if not job.created_at:
            job.created_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """
            INSERT INTO runtime_jobs (id, task_id, council_session_id, status, plan_text, merged_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.id,
                job.task_id,
                job.council_session_id,
                job.status,
                job.plan_text,
                job.merged_result,
                job.created_at,
            ),
        )
        self.cm.commit()
        return job

    def get_job(self, job_id: str) -> Optional[RuntimeJob]:
        row = self.cm.execute("SELECT * FROM runtime_jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        return RuntimeJob(
            id=row["id"],
            task_id=row["task_id"],
            council_session_id=row["council_session_id"],
            status=row["status"],
            plan_text=row["plan_text"],
            merged_result=row["merged_result"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )

    def list_jobs(self, task_id: Optional[str] = None, status: Optional[str] = None) -> list[RuntimeJob]:
        query = "SELECT * FROM runtime_jobs WHERE 1=1"
        params = []
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        rows = self.cm.execute(query, params).fetchall()
        return [
            RuntimeJob(
                id=r["id"],
                task_id=r["task_id"],
                council_session_id=r["council_session_id"],
                status=r["status"],
                plan_text=r["plan_text"],
                merged_result=r["merged_result"],
                created_at=r["created_at"],
                completed_at=r["completed_at"],
            )
            for r in rows
        ]

    def update_job_status(self, job_id: str, status: str, completed_at: Optional[str] = None):
        now = datetime.now(timezone.utc).isoformat() if completed_at else None
        self.cm.execute(
            "UPDATE runtime_jobs SET status = ?, completed_at = ? WHERE id = ?",
            (status, completed_at or now, job_id),
        )
        self.cm.commit()

    def create_assignment(self, assignment: RuntimeAssignment) -> RuntimeAssignment:
        if not assignment.id:
            assignment.id = str(uuid.uuid4())
        if not assignment.created_at:
            assignment.created_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """
            INSERT INTO runtime_assignments (id, runtime_job_id, task_fragment, assigned_agent_id, status, execution_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assignment.id,
                assignment.runtime_job_id,
                assignment.task_fragment,
                assignment.assigned_agent_id,
                assignment.status,
                assignment.execution_id,
                assignment.created_at,
            ),
        )
        self.cm.commit()
        return assignment

    def get_assignment(self, assignment_id: str) -> Optional[RuntimeAssignment]:
        row = self.cm.execute("SELECT * FROM runtime_assignments WHERE id = ?", (assignment_id,)).fetchone()
        if not row:
            return None
        return RuntimeAssignment(
            id=row["id"],
            runtime_job_id=row["runtime_job_id"],
            task_fragment=row["task_fragment"],
            assigned_agent_id=row["assigned_agent_id"],
            status=row["status"],
            execution_id=row["execution_id"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )

    def list_assignments(self, job_id: str) -> list[RuntimeAssignment]:
        rows = self.cm.execute("SELECT * FROM runtime_assignments WHERE runtime_job_id = ? ORDER BY created_at", (job_id,)).fetchall()
        return [
            RuntimeAssignment(
                id=r["id"],
                runtime_job_id=r["runtime_job_id"],
                task_fragment=r["task_fragment"],
                assigned_agent_id=r["assigned_agent_id"],
                status=r["status"],
                execution_id=r["execution_id"],
                created_at=r["created_at"],
                completed_at=r["completed_at"],
            )
            for r in rows
        ]

    def update_assignment(self, assignment_id: str, **kwargs):
        sets = []
        params = []
        for key in ["status", "execution_id", "completed_at"]:
            if key in kwargs:
                sets.append(f"{key} = ?")
                params.append(kwargs[key])
        if sets:
            params.append(assignment_id)
            self.cm.execute(f"UPDATE runtime_assignments SET {', '.join(sets)} WHERE id = ?", params)
            self.cm.commit()

    def create_result(self, result: RuntimeResult) -> RuntimeResult:
        if not result.id:
            result.id = str(uuid.uuid4())
        if not result.created_at:
            result.created_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """
            INSERT INTO runtime_results (id, runtime_assignment_id, agent_id, result, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (result.id, result.runtime_assignment_id, result.agent_id, result.result, result.metadata, result.created_at),
        )
        self.cm.commit()
        return result

    def get_results_for_job(self, job_id: str) -> list[RuntimeResult]:
        rows = self.cm.execute(
            """
            SELECT rr.* FROM runtime_results rr
            JOIN runtime_assignments ra ON ra.id = rr.runtime_assignment_id
            WHERE ra.runtime_job_id = ?
            """,
            (job_id,),
        ).fetchall()
        return [
            RuntimeResult(
                id=r["id"],
                runtime_assignment_id=r["runtime_assignment_id"],
                agent_id=r["agent_id"],
                result=r["result"],
                metadata=r["metadata"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def create_memory(self, memory: RuntimeMemory):
        if not memory.id:
            memory.id = str(uuid.uuid4())
        if not memory.created_at:
            memory.created_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            "INSERT INTO runtime_memory (id, runtime_job_id, memory_type, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (memory.id, memory.runtime_job_id, memory.memory_type, memory.content, memory.created_at),
        )
        self.cm.commit()

    def get_memories_for_job(self, job_id: str) -> list[RuntimeMemory]:
        rows = self.cm.execute("SELECT * FROM runtime_memory WHERE runtime_job_id = ? ORDER BY created_at", (job_id,)).fetchall()
        return [
            RuntimeMemory(
                id=r["id"],
                runtime_job_id=r["runtime_job_id"],
                memory_type=r["memory_type"],
                content=r["content"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
