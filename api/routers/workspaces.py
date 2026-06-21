from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

from toll.workspace.manager import WorkspaceManager

router = APIRouter()


class WorkspaceCreate(BaseModel):
    type: str
    name: str
    metadata: Optional[dict] = None


class SemesterCreate(BaseModel):
    name: str
    metadata: Optional[dict] = None


class ActiveWorkspaceSet(BaseModel):
    brand_id: Optional[str] = None
    university_id: Optional[str] = None
    project_id: Optional[str] = None
    semester_id: Optional[str] = None


@router.get("/workspaces")
def list_workspaces(type: Optional[str] = None):
    manager = WorkspaceManager()
    return {"workspaces": manager.list_workspaces(type=type)}


@router.post("/workspaces")
def create_workspace(req: WorkspaceCreate):
    manager = WorkspaceManager()
    try:
        workspace = manager.create_workspace(req.type, req.name, req.metadata)
        return workspace
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspaces/{id}")
def get_workspace(id: str):
    manager = WorkspaceManager()
    workspace = manager.get_workspace(id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.post("/workspaces/{id}/semesters")
def create_semester(id: str, req: SemesterCreate):
    manager = WorkspaceManager()
    try:
        semester = manager.create_semester(id, req.name, req.metadata)
        return semester
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspaces/{id}/semesters")
def list_semesters(id: str):
    manager = WorkspaceManager()
    return {"semesters": manager.list_semesters(id)}


@router.get("/workspaces/active")
def get_active_workspace():
    manager = WorkspaceManager()
    return {
        "state": manager.get_active().to_dict(),
        "summary": manager.get_active_summary(),
    }


@router.post("/workspaces/active")
def set_active_workspace(req: ActiveWorkspaceSet):
    manager = WorkspaceManager()
    state = manager.set_active(
        brand_id=req.brand_id,
        university_id=req.university_id,
        project_id=req.project_id,
        semester_id=req.semester_id,
    )
    return {
        "state": state.to_dict(),
        "summary": manager.get_active_summary(),
    }


@router.delete("/workspaces/active")
def clear_active_workspace():
    manager = WorkspaceManager()
    manager.clear_active()
    return {"state": WorkspaceManager().get_active().to_dict()}
