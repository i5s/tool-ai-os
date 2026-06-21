from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from toll.core.conversations import ConversationStore

router = APIRouter()


class ConversationCreate(BaseModel):
    title: Optional[str] = "محادثة جديدة"
    workspace_type: Optional[str] = None
    workspace_id: Optional[str] = None
    metadata: Optional[dict] = None


class MessageCreate(BaseModel):
    role: str
    content: str
    metadata: Optional[dict] = None


class TitleUpdate(BaseModel):
    title: str


@router.get("/conversations")
def list_conversations(
    workspace_type: Optional[str] = None,
    workspace_id: Optional[str] = None,
    limit: int = 100,
):
    store = ConversationStore()
    return {"conversations": store.list(workspace_type, workspace_id, limit)}


@router.post("/conversations")
def create_conversation(req: ConversationCreate):
    store = ConversationStore()
    conv = store.create(
        title=req.title,
        workspace_type=req.workspace_type,
        workspace_id=req.workspace_id,
        metadata=req.metadata,
    )
    return {"conversation_id": conv["id"], **conv}


@router.get("/conversations/{id}")
def get_conversation(id: str):
    store = ConversationStore()
    conv = store.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.put("/conversations/{id}/title")
def update_title(id: str, req: TitleUpdate):
    store = ConversationStore()
    conv = store.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    store.update_title(id, req.title)
    return store.get(id)


@router.delete("/conversations/{id}")
def delete_conversation(id: str):
    store = ConversationStore()
    conv = store.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    store.delete(id)
    return {"deleted": True}


@router.get("/conversations/{id}/messages")
def list_messages(id: str):
    store = ConversationStore()
    conv = store.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": store.list_messages(id)}


@router.post("/conversations/{id}/messages")
def add_message(id: str, req: MessageCreate):
    store = ConversationStore()
    conv = store.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return store.add_message(id, req.role, req.content, req.metadata)
