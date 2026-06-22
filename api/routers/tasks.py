from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import json

from toll.tasks.models import Task, TaskStatus, TaskPriority, TaskEventType
from toll.tasks.service import TaskService
from toll.tasks.repository import TaskRepository
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = TaskPriority.MEDIUM.value
    created_by: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None


def _get_service(cm: ConnectionManager) -> TaskService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("task_dispatcher", default=False):
        raise HTTPException(status_code=404, detail="Task dispatcher is disabled")
    return TaskService(cm=cm)


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "created_by": task.created_by,
        "assigned_agent_id": task.assigned_agent_id,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "completed_at": task.completed_at,
    }


def _event_to_dict(ev) -> dict:
    payload = None
    if ev.payload:
        try:
            payload = json.loads(ev.payload)
        except Exception:
            payload = ev.payload
    return {
        "id": ev.id,
        "task_id": ev.task_id,
        "event_type": ev.event_type,
        "actor": ev.actor,
        "payload": payload,
        "created_at": ev.created_at,
    }


@router.get("/tasks")
def list_tasks(
    status: Optional[str] = None,
    assigned_agent_id: Optional[str] = None,
    limit: int = 100,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    tasks = service.list_tasks(status=status, assigned_agent_id=assigned_agent_id, limit=limit)
    return [_task_to_dict(t) for t in tasks]


@router.post("/tasks")
def create_task(
    req: CreateTaskRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    task = service.create_task(
        title=req.title, description=req.description,
        priority=req.priority, created_by=req.created_by
    )
    return _task_to_dict(task)


@router.get("/tasks/{task_id}")
def get_task(
    task_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.put("/tasks/{task_id}")
def update_task(
    task_id: str,
    req: UpdateTaskRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    updates = req.model_dump(exclude_none=True)
    task = service.update_task(task_id, **updates)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    repo = TaskRepository(cm)
    ok = repo.delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.post("/tasks/{task_id}/assign")
def assign_task(
    task_id: str,
    body: dict,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    agent_id = body.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=422, detail="agent_id is required")
    task = service.assign_task(task_id, agent_id, actor=body.get("actor"))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.post("/tasks/{task_id}/start")
def start_task(
    task_id: str,
    body: Optional[dict] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    task = service.start_task(task_id, actor=body.get("actor") if body else None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: str,
    body: Optional[dict] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    task = service.complete_task(task_id, actor=body.get("actor") if body else None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.post("/tasks/{task_id}/fail")
def fail_task(
    task_id: str,
    body: Optional[dict] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    task = service.fail_task(
        task_id,
        actor=body.get("actor") if body else None,
        error=(body or {}).get("error"),
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_dict(task)


@router.get("/tasks/{task_id}/events")
def get_task_events(
    task_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    events = service.repo.list_events(task_id)
    return [_event_to_dict(e) for e in events]
