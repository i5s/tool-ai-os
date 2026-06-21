from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.application.artifact_service import ArtifactService
from toll.application.notebook_service import NotebookService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


class CreateNotebookRequest(BaseModel):
    title: str
    description: str = ""
    workspace_type: Optional[str] = None
    workspace_id: Optional[str] = None


class UpdateNotebookRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class UploadSourceRequest(BaseModel):
    content: str
    file_name: str
    title: str = ""


class CreateNotesRequest(BaseModel):
    source_ids: Optional[list[str]] = None


class QueryRequest(BaseModel):
    question: str


class CreateSnapshotRequest(BaseModel):
    label: str = ""


class AudioOverviewRequest(BaseModel):
    source_ids: Optional[list[str]] = None


def _get_notebook_service(cm: ConnectionManager) -> NotebookService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("notebooklm_enabled"):
        raise HTTPException(status_code=403, detail="NotebookLM features are disabled")
    artifact_service = ArtifactService(cm)
    return NotebookService(artifact_service, cm, flags)


@router.post("/notebooks")
def create_notebook(
    req: CreateNotebookRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    nb = svc.create_notebook(
        title=req.title,
        description=req.description,
        workspace_type=req.workspace_type,
        workspace_id=req.workspace_id,
    )
    return {
        "id": nb.id,
        "title": nb.title,
        "description": nb.description,
        "source_count": nb.source_count,
        "note_count": nb.note_count,
        "created_at": nb.created_at,
        "updated_at": nb.updated_at,
    }


@router.get("/notebooks")
def list_notebooks(
    workspace_type: Optional[str] = None,
    workspace_id: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    notebooks = svc.list_notebooks(
        workspace_type=workspace_type,
        workspace_id=workspace_id,
    )
    return {
        "notebooks": [
            {
                "id": nb.id,
                "title": nb.title,
                "description": nb.description,
                "source_count": nb.source_count,
                "note_count": nb.note_count,
                "created_at": nb.created_at,
                "updated_at": nb.updated_at,
            }
            for nb in notebooks
        ]
    }


@router.get("/notebooks/{notebook_id}")
def get_notebook(
    notebook_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    nb = svc.get_notebook(notebook_id)
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return {
        "id": nb.id,
        "title": nb.title,
        "description": nb.description,
        "workspace_type": nb.workspace_type,
        "workspace_id": nb.workspace_id,
        "source_count": nb.source_count,
        "note_count": nb.note_count,
        "created_at": nb.created_at,
        "updated_at": nb.updated_at,
    }


@router.put("/notebooks/{notebook_id}")
def update_notebook(
    notebook_id: str,
    req: UpdateNotebookRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    nb = svc.update_notebook(
        notebook_id=notebook_id,
        title=req.title,
        description=req.description,
    )
    if not nb:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return {"success": True, "notebook": {"id": nb.id, "title": nb.title, "description": nb.description}}


@router.delete("/notebooks/{notebook_id}")
def delete_notebook(
    notebook_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    if not svc.get_notebook(notebook_id):
        raise HTTPException(status_code=404, detail="Notebook not found")
    svc.delete_notebook(notebook_id)
    return {"success": True}


@router.post("/notebooks/{notebook_id}/sources")
def upload_source(
    notebook_id: str,
    req: UploadSourceRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    source = svc.upload_source(
        notebook_id=notebook_id,
        content=req.content,
        file_name=req.file_name,
        title=req.title,
    )
    if not source:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return {
        "id": source.id,
        "title": source.title,
        "file_name": source.file_name,
        "char_count": source.char_count,
        "created_at": source.created_at,
    }


@router.get("/notebooks/{notebook_id}/sources")
def list_sources(
    notebook_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    if not svc.get_notebook(notebook_id):
        raise HTTPException(status_code=404, detail="Notebook not found")
    sources = svc.list_sources(notebook_id)
    return {
        "sources": [
            {
                "id": s.id,
                "title": s.title,
                "file_name": s.file_name,
                "char_count": s.char_count,
                "created_at": s.created_at,
            }
            for s in sources
        ]
    }


@router.delete("/notebooks/{notebook_id}/sources/{source_id}")
def delete_source(
    notebook_id: str,
    source_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    if not svc.get_notebook(notebook_id):
        raise HTTPException(status_code=404, detail="Notebook not found")
    deleted = svc.delete_source(notebook_id, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"success": True}


@router.post("/notebooks/{notebook_id}/notes")
def create_notes(
    notebook_id: str,
    req: CreateNotesRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    notes = svc.create_notes(notebook_id, source_ids=req.source_ids)
    return {
        "notes": [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "source_ids": n.source_ids,
                "created_at": n.created_at,
            }
            for n in notes
        ]
    }


@router.get("/notebooks/{notebook_id}/notes")
def list_notes(
    notebook_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    if not svc.get_notebook(notebook_id):
        raise HTTPException(status_code=404, detail="Notebook not found")
    notes = svc.list_notes(notebook_id)
    return {
        "notes": [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "source_ids": n.source_ids,
                "created_at": n.created_at,
            }
            for n in notes
        ]
    }


@router.delete("/notebooks/{notebook_id}/notes/{note_id}")
def delete_note(
    notebook_id: str,
    note_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    deleted = svc.delete_note(notebook_id, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True}


@router.post("/notebooks/{notebook_id}/query")
def query_notebook(
    notebook_id: str,
    req: QueryRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    svc = _get_notebook_service(cm)
    answer = svc.query(notebook_id, req.question)
    return {"answer": answer}


@router.post("/notebooks/{notebook_id}/snapshots")
def create_snapshot(
    notebook_id: str,
    req: CreateSnapshotRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    snapshot = svc.create_snapshot(notebook_id, label=req.label)
    if not snapshot:
        raise HTTPException(status_code=400, detail="Snapshots are disabled or notebook not found")
    return {
        "id": snapshot.id,
        "label": snapshot.label,
        "source_count": snapshot.source_count,
        "note_count": snapshot.note_count,
        "created_at": snapshot.created_at,
    }


@router.get("/notebooks/{notebook_id}/snapshots")
def list_snapshots(
    notebook_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    if not svc.get_notebook(notebook_id):
        raise HTTPException(status_code=404, detail="Notebook not found")
    snapshots = svc.list_snapshots(notebook_id)
    return {
        "snapshots": [
            {
                "id": s.id,
                "label": s.label,
                "source_count": s.source_count,
                "note_count": s.note_count,
                "created_at": s.created_at,
            }
            for s in snapshots
        ]
    }


@router.get("/notebooks/{notebook_id}/snapshots/{snapshot_id}")
def get_snapshot(
    notebook_id: str,
    snapshot_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    snapshot = svc.get_snapshot(notebook_id, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {
        "id": snapshot.id,
        "label": snapshot.label,
        "snapshot_data": snapshot.snapshot_data,
        "source_count": snapshot.source_count,
        "note_count": snapshot.note_count,
        "created_at": snapshot.created_at,
    }


@router.delete("/notebooks/{notebook_id}/snapshots/{snapshot_id}")
def delete_snapshot(
    notebook_id: str,
    snapshot_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    deleted = svc.delete_snapshot(notebook_id, snapshot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"success": True}


@router.post("/notebooks/{notebook_id}/audio")
def generate_audio_overview(
    notebook_id: str,
    req: AudioOverviewRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = _get_notebook_service(cm)
    if not svc.flags.is_enabled("notebooklm_audio_overview"):
        raise HTTPException(status_code=403, detail="Audio overview is not enabled")
    result = svc.generate_audio_overview(notebook_id, source_ids=req.source_ids)
    if "error" in result:
        raise HTTPException(status_code=501, detail=result["error"])
    return result
