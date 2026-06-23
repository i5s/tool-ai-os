from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import json

from toll.executions.service import ExecutionService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


def _get_execution_service(cm: ConnectionManager) -> ExecutionService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("agent_execution_history", default=False):
        raise HTTPException(status_code=404, detail="Agent execution history is disabled")
    return ExecutionService(cm=cm)


def _execution_to_dict(ex) -> dict:
    meta = None
    if ex.execution_metadata:
        try:
            meta = json.loads(ex.execution_metadata)
        except Exception:
            meta = ex.execution_metadata
    return {
        "id": ex.id,
        "task_id": ex.task_id,
        "agent_id": ex.agent_id,
        "status": ex.status,
        "started_at": ex.started_at,
        "completed_at": ex.completed_at,
        "duration_ms": ex.duration_ms,
        "stdout": ex.stdout,
        "stderr": ex.stderr,
        "execution_metadata": meta,
        "created_at": ex.created_at,
    }


@router.get("/executions")
def list_executions(
    task_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_execution_service(cm)
    executions = service.list_executions(task_id=task_id, agent_id=agent_id, status=status, limit=limit)
    return [_execution_to_dict(e) for e in executions]


@router.get("/executions/{execution_id}")
def get_execution(
    execution_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_execution_service(cm)
    ex = service.get_execution(execution_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return _execution_to_dict(ex)


@router.get("/agents/{agent_id}/executions")
def list_agent_executions(
    agent_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_execution_service(cm)
    executions = service.list_executions(agent_id=agent_id, status=status, limit=limit)
    return [_execution_to_dict(e) for e in executions]


@router.get("/tasks/{task_id}/executions")
def list_task_executions(
    task_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_execution_service(cm)
    executions = service.list_executions(task_id=task_id, status=status, limit=limit)
    return [_execution_to_dict(e) for e in executions]
