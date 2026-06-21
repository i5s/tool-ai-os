from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.workspace.manager import WorkspaceManager
from toll.core.connection_manager import ConnectionManager
from api.dependencies import get_connection_manager

router = APIRouter()


class WorkspaceCreate(BaseModel):
    type: str
    name: str


class SemesterCreate(BaseModel):
    university_id: str
    name: str


class SetActiveRequest(BaseModel):
    brand_id: Optional[str] = None
    university_id: Optional[str] = None
    project_id: Optional[str] = None
    semester_id: Optional[str] = None


@router.get("/workspaces")
def list_workspaces(
    type: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    manager = WorkspaceManager(cm=cm)
    return {"workspaces": manager.list_workspaces(type)}


@router.post("/workspaces")
def create_workspace(
    req: WorkspaceCreate,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    manager = WorkspaceManager(cm=cm)
    workspace = manager.create_workspace(req.type, req.name)
    return workspace


@router.delete("/workspaces/{id}")
def delete_workspace(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    # TODO: implement cascade delete in workspace manager
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/semesters")
def create_semester(
    req: SemesterCreate,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    manager = WorkspaceManager(cm=cm)
    semester = manager.create_semester(req.university_id, req.name)
    return semester


@router.get("/semesters/{university_id}")
def list_semesters(
    university_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    manager = WorkspaceManager(cm=cm)
    return {"semesters": manager.list_semesters(university_id)}


@router.get("/workspace/active")
def get_active(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    manager = WorkspaceManager(cm=cm)
    state = manager.get_active()
    summary = manager.get_active_summary()
    return {"state": state.to_dict(), "summary": summary}


@router.post("/workspace/active")
def set_active(
    req: SetActiveRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    manager = WorkspaceManager(cm=cm)
    manager.set_active(
        brand_id=req.brand_id,
        university_id=req.university_id,
        project_id=req.project_id,
        semester_id=req.semester_id,
    )
    state = manager.get_active()
    summary = manager.get_active_summary()
    return {"state": state.to_dict(), "summary": summary}


@router.delete("/workspace/active")
def clear_active(
    cm: ConnectionManager = Depends(get_connection_manager),
):
    manager = WorkspaceManager(cm=cm)
    manager.clear_active()
    return {"status": "cleared"}
