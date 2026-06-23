from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from toll.runtime.models import RuntimeJob, RuntimeAssignment, RuntimeResult
from toll.runtime.service import RuntimeService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


def _require_flag(cm: ConnectionManager):
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("multi_agent_runtime"):
        raise HTTPException(status_code=404, detail="Not found")
    return flags


def _job_to_dict(j: RuntimeJob) -> dict:
    return {
        "id": j.id,
        "task_id": j.task_id,
        "council_session_id": j.council_session_id,
        "status": j.status,
        "plan_text": j.plan_text,
        "merged_result": j.merged_result,
        "created_at": j.created_at,
        "completed_at": j.completed_at,
    }


def _assignment_to_dict(a: RuntimeAssignment) -> dict:
    return {
        "id": a.id,
        "runtime_job_id": a.runtime_job_id,
        "task_fragment": a.task_fragment,
        "assigned_agent_id": a.assigned_agent_id,
        "status": a.status,
        "execution_id": a.execution_id,
        "created_at": a.created_at,
        "completed_at": a.completed_at,
    }


def _result_to_dict(r: RuntimeResult) -> dict:
    return {
        "id": r.id,
        "runtime_assignment_id": r.runtime_assignment_id,
        "agent_id": r.agent_id,
        "result": r.result,
        "metadata": r.metadata,
        "created_at": r.created_at,
    }


@router.get("/runtime/jobs")
def list_jobs(task_id: Optional[str] = None, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = RuntimeService(cm)
    jobs = svc.repo.list_jobs(task_id=task_id)
    return [_job_to_dict(j) for j in jobs]


@router.post("/runtime/jobs")
def create_job(payload: dict, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = RuntimeService(cm)
    job = svc.create_runtime_job(
        task_id=payload.get("task_id", ""),
        council_session_id=payload.get("council_session_id"),
        plan_text=payload.get("plan_text"),
    )
    return _job_to_dict(job)


@router.get("/runtime/jobs/{job_id}")
def get_job(job_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    job = RuntimeService(cm).repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_dict(job)


@router.post("/runtime/jobs/{job_id}/assign")
def assign_job(job_id: str, payload: dict, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = RuntimeService(cm)
    job = svc.repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    fragments = payload.get("fragments", [])
    if not fragments:
        raise HTTPException(status_code=400, detail="fragments required")
    assignments = svc.assign_agents(job_id, fragments)
    return [_assignment_to_dict(a) for a in assignments]


@router.post("/runtime/jobs/{job_id}/execute")
def execute_job(job_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = RuntimeService(cm)
    job = svc.repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    assignments = svc.execute_assignments(job_id)
    merged = svc.merge_results(job_id)
    svc.finalize_job(job_id, merged)
    refreshed = svc.repo.get_job(job_id)
    if not refreshed:
        raise HTTPException(status_code=500, detail="Failed to refresh job")
    return {
        "job": _job_to_dict(refreshed),
        "assignments": [_assignment_to_dict(a) for a in assignments],
        "results": [_result_to_dict(r) for r in svc.repo.get_results_for_job(job_id)],
    }


@router.get("/runtime/jobs/{job_id}/results")
def get_results(job_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    job = RuntimeService(cm).repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    svc = RuntimeService(cm)
    return [_result_to_dict(r) for r in svc.repo.get_results_for_job(job_id)]
