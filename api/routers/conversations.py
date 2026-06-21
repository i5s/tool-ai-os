from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.core.conversations import ConversationStore
from toll.core.connection_manager import ConnectionManager
from api.dependencies import get_connection_manager

router = APIRouter()


class ConversationCreate(BaseModel):
    title: str = "محادثة جديدة"
    workspace_type: Optional[str] = None
    workspace_id: Optional[str] = None


class TitleUpdate(BaseModel):
    title: str


@router.get("/conversations")
def list_conversations(
    workspace_type: Optional[str] = None,
    workspace_id: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    store = ConversationStore(cm=cm)
    return {"conversations": store.list(workspace_type, workspace_id)}


@router.post("/conversations")
def create_conversation(
    req: ConversationCreate,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    store = ConversationStore(cm=cm)
    conv = store.create(req.title, req.workspace_type, req.workspace_id)
    return conv


@router.get("/conversations/{id}")
def get_conversation(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    store = ConversationStore(cm=cm)
    conv = store.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.put("/conversations/{id}/title")
def update_conversation_title(
    id: str,
    req: TitleUpdate,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    store = ConversationStore(cm=cm)
    store.update_title(id, req.title)
    return {"status": "updated"}


@router.delete("/conversations/{id}")
def delete_conversation(
    id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    store = ConversationStore(cm=cm)
    if not store.delete(id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}
