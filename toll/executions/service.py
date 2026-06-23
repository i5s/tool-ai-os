from __future__ import annotations

import json
import time
from uuid import uuid4
from typing import Optional

from .models import AgentExecution
from .repository import ExecutionRepository


class ExecutionService:
    def __init__(self, cm):
        self.cm = cm
        self.repo = ExecutionRepository(cm)

    def start_execution(self, task_id: str, agent_id: str, metadata: Optional[dict] = None) -> AgentExecution:
        execution = AgentExecution(
            id=f"exec-{uuid4().hex[:8]}",
            task_id=task_id,
            agent_id=agent_id,
            status="running",
            execution_metadata=json.dumps(metadata) if metadata else None,
        )
        return self.repo.create_execution(execution)

    def complete_execution(self, execution_id: str, duration_ms: int,
                           stdout: str, stderr: str, metadata: Optional[dict] = None) -> Optional[AgentExecution]:
        meta_str = json.dumps(metadata) if metadata else None
        return self.repo.complete_execution(execution_id, "completed", duration_ms, stdout, stderr, meta_str)

    def fail_execution(self, execution_id: str, duration_ms: int, error: str,
                       metadata: Optional[dict] = None) -> Optional[AgentExecution]:
        meta_str = json.dumps(metadata) if metadata else None
        return self.repo.fail_execution(execution_id, duration_ms, error, meta_str)

    def get_execution(self, execution_id: str) -> Optional[AgentExecution]:
        return self.repo.get_execution(execution_id)

    def list_executions(self, task_id: Optional[str] = None, agent_id: Optional[str] = None,
                        status: Optional[str] = None, limit: int = 100) -> list[AgentExecution]:
        return self.repo.list_executions(task_id=task_id, agent_id=agent_id, status=status, limit=limit)
