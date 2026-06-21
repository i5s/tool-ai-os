from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional

from toll.core.connection_manager import ConnectionManager
from toll.model.artifact import ArtifactType, ArtifactStatus, Artifact
from toll.application.artifact_service import ArtifactService
from api.dependencies import get_connection_manager

router = APIRouter()


class ArtifactResponse(BaseModel):
    id: str
    type: str
    status: str
    title: str
    version: int
    workflow_id: Optional[str] = None
    conversation_id: Optional[str] = None
    preview_url: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    intent: Optional[str] = None
    tags: list[str] = []
    created_at: str
    updated_at: str


def _to_response(artifact: Artifact) -> dict:
    return {
        "id": artifact.id,
        "type": artifact.type.value,
        "status": artifact.status.value,
        "title": artifact.title,
        "version": artifact.version,
        "workflow_id": artifact.workflow_id,
        "conversation_id": artifact.conversation_id,
        "preview_url": artifact.preview_url,
        "provider": artifact.provider,
        "model": artifact.model,
        "intent": artifact.intent,
        "tags": artifact.tags,
        "created_at": artifact.created_at,
        "updated_at": artifact.updated_at,
    }


@router.get("/artifacts")
def list_artifacts(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    workflow_id: Optional[str] = Query(None),
    limit: int = Query(100),
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = ArtifactService(cm)
    art_type = ArtifactType(type) if type else None
    art_status = ArtifactStatus(status) if status else None
    artifacts = svc.list(art_type, art_status, workflow_id, limit)
    return {"artifacts": [_to_response(a) for a in artifacts]}


@router.get("/artifacts/{id}")
def get_artifact(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = ArtifactService(cm)
    artifact = svc.get(id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return _to_response(artifact)


@router.get("/artifacts/{id}/content")
def get_artifact_content(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = ArtifactService(cm)
    artifact = svc.get(id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.content


@router.get("/artifacts/{id}/render")
def get_artifact_render(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = ArtifactService(cm)
    path = svc.get_rendered_path(id)
    if not path:
        raise HTTPException(status_code=404, detail="Rendered file not found")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/artifacts/{id}/preview")
def get_artifact_preview(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = ArtifactService(cm)
    preview = svc.get_preview_html(id)
    if preview:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(preview)
    preview_json = svc.get_preview_json(id)
    if preview_json:
        return preview_json
    raise HTTPException(status_code=404, detail="Preview not found")


@router.delete("/artifacts/{id}")
def delete_artifact(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    svc = ArtifactService(cm)
    if not svc.delete(id):
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"status": "deleted"}
