from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional

from toll.planner.planner import Planner, PlannerMode
from toll.workflow.engine import WorkflowEngine, WorkflowStatus
from toll.core.feature_flags import FeatureFlags
from toll.core.connection_manager import ConnectionManager
from api.dependencies import get_connection_manager

router = APIRouter()


class PlanRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class ModeRequest(BaseModel):
    mode: str  # strict | balanced | fast


class ApproveRequest(BaseModel):
    reason: Optional[str] = None


def _get_planner(cm: ConnectionManager) -> Planner:
    flags = FeatureFlags(cm=cm)
    return Planner.from_flags(
        strict=flags.is_enabled("planner_strict_mode"),
        fast=flags.is_enabled("planner_fast_mode"),
    )


@router.post("/plan")
def create_plan(
    req: PlanRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    planner = _get_planner(cm)
    plan = planner.plan(req.message, req.context)
    return {
        "intent": plan.intent,
        "level": plan.level.value,
        "mode": plan.mode.value,
        "title": plan.title,
        "description": plan.description,
        "steps": plan.steps,
        "can_auto_execute": plan.can_auto_execute,
        "requires_approval": plan.requires_approval,
        "plan_only": plan.plan_only,
        "metadata": plan.metadata,
    }


@router.get("/plan/mode")
def get_planner_mode(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    planner = _get_planner(cm)
    return {"mode": planner.mode.value}


@router.post("/plan/mode")
def set_planner_mode(
    req: ModeRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    flags = FeatureFlags(cm=cm)
    if req.mode == "strict":
        flags.enable("planner_strict_mode")
        flags.disable("planner_fast_mode")
    elif req.mode == "fast":
        flags.disable("planner_strict_mode")
        flags.enable("planner_fast_mode")
    elif req.mode == "balanced":
        flags.disable("planner_strict_mode")
        flags.disable("planner_fast_mode")
    else:
        raise HTTPException(status_code=400, detail="Mode must be strict, balanced, or fast")
    return {"mode": req.mode}


@router.post("/workflows")
def create_workflow(
    req: PlanRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    planner = _get_planner(cm)
    plan = planner.plan(req.message, req.context)
    engine = WorkflowEngine(cm=cm)
    workflow = engine.create_and_run(plan.__dict__)
    return {
        "workflow_id": workflow.id,
        "status": workflow.status.value,
        "plan": workflow.plan,
        "result": workflow.result,
    }


@router.get("/workflows")
def list_workflows(
    status: Optional[str] = None,
    limit: int = 100,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    engine = WorkflowEngine(cm=cm)
    workflows = engine.list(
        status=WorkflowStatus(status) if status else None,
        limit=limit,
    )
    return {"workflows": [w.__dict__ for w in workflows]}


@router.get("/workflows/{id}")
def get_workflow(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    engine = WorkflowEngine(cm=cm)
    workflow = engine.get(id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.__dict__


@router.post("/workflows/{id}/approve")
def approve_workflow(
    id: str,
    req: ApproveRequest = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    engine = WorkflowEngine(cm=cm)
    try:
        workflow = engine.approve(id)
        return {"workflow_id": workflow.id, "status": workflow.status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{id}/reject")
def reject_workflow(
    id: str,
    req: ApproveRequest = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    engine = WorkflowEngine(cm=cm)
    try:
        reason = req.reason if req else ""
        workflow = engine.reject(id, reason)
        return {"workflow_id": workflow.id, "status": workflow.status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{id}/run")
def run_workflow(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    engine = WorkflowEngine(cm=cm)
    try:
        workflow = engine.run(id)
        return {
            "workflow_id": workflow.id,
            "status": workflow.status.value,
            "result": workflow.result,
            "error": workflow.error,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
