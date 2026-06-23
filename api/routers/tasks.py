from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import json

from toll.tasks.models import Task, TaskStatus, TaskPriority, TaskEventType
from toll.tasks.service import TaskService
from toll.tasks.repository import TaskRepository
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.agents.service import AgentService
from toll.agents.adapter_factory import AdapterFactory
from toll.shared_memory.service import SharedMemoryService
from toll.executions.service import ExecutionService
from toll.learning.service import LearningService
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


def _get_execution_service(cm: ConnectionManager) -> TaskService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("agent_runtime_bridge", default=False):
        raise HTTPException(status_code=404, detail="Agent runtime bridge is disabled")
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
        "result": task.result,
        "result_metadata": task.result_metadata,
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


@router.post("/tasks/{task_id}/execute")
def execute_task(
    task_id: str,
    body: Optional[dict] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_execution_service(cm)
    agent_service = AgentService(cm)
    memory_service = SharedMemoryService(cm)

    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in (TaskStatus.ASSIGNED.value, TaskStatus.RUNNING.value):
        raise HTTPException(status_code=422, detail="Task must be assigned or running before execution")

    agent_id = task.assigned_agent_id
    if not agent_id:
        raise HTTPException(status_code=422, detail="Task must be assigned to an agent")

    agent = agent_service.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Assigned agent not found")

    adapter = AdapterFactory.get_adapter(agent.name)
    context = None
    if body:
        context = body.get("context")

    execution_service = ExecutionService(cm)
    execution = execution_service.start_execution(
        task_id=task.id,
        agent_id=agent.id,
        metadata={"task_title": task.title, "task_description": task.description, "context": context},
    )

    result = adapter.execute(task_id=task.id, title=task.title, description=task.description, context=context)

    duration_ms = result.get("duration_ms") or 0
    stdout = result.get("output") or ""
    stderr = ""
    if result.get("status") == "failed":
        stderr = stdout
        stdout = ""

    execution_service.complete_execution(
        execution_id=execution.id,
        duration_ms=duration_ms,
        stdout=stdout,
        stderr=stderr,
        metadata=result.get("metadata"),
    )

    learning_flags = FeatureFlags(cm=cm)
    if learning_flags.is_enabled("learning_loop"):
        LearningService(cm).record_execution_learning(
            execution_id=execution.id,
            agent_id=agent.id,
            task_id=task.id,
            status=result.get("status", "completed"),
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
        )

    service.repo.update_task(task.id, result=stdout, result_metadata=json.dumps(result.get("metadata")))

    memory_block = memory_service.create_memory(
        type="fact",
        scope="project",
        title=f"Task completed: {task.title}",
        content=stdout,
        scope_id=task.id,
        created_by=agent_id,
        metadata={"duration_ms": duration_ms, "status": result.get("status")},
    )

    completed = service.complete_task(task.id, actor=agent.name)
    if completed is None:
        raise HTTPException(status_code=500, detail="Failed to mark task complete")

    return {
        **_task_to_dict(completed),
        "execution_result": result,
        "memory_block_id": memory_block.id,
        "execution_id": execution.id,
    }
