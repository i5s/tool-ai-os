from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from toll.shared_memory.models import MemoryBlock, MemoryScope, MemoryBlockType
from toll.shared_memory.service import SharedMemoryService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


def _get_service(cm: ConnectionManager) -> SharedMemoryService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("shared_memory", default=False):
        raise HTTPException(status_code=404, detail="Shared memory is disabled")
    return SharedMemoryService(cm=cm)


class CreateMemoryRequest(BaseModel):
    type: str
    scope: str
    title: str
    content: Optional[str] = None
    scope_id: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[dict] = None


class UpdateMemoryRequest(BaseModel):
    type: Optional[str] = None
    scope: Optional[str] = None
    scope_id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[dict] = None


class LinkMemoryRequest(BaseModel):
    target_id: str
    relation: str = "related_to"


def _block_to_dict(block: MemoryBlock) -> dict:
    return {
        "id": block.id,
        "type": block.type,
        "scope": block.scope,
        "scope_id": block.scope_id,
        "title": block.title,
        "content": block.content,
        "created_by": block.created_by,
        "metadata": block.metadata,
        "created_at": block.created_at,
        "updated_at": block.updated_at,
    }


@router.get("/memory")
def list_memory(
    type: Optional[str] = None,
    scope: Optional[str] = None,
    scope_id: Optional[str] = None,
    created_by: Optional[str] = None,
    title: Optional[str] = None,
    limit: int = 100,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    blocks = service.list_memory(
        block_type=type,
        scope=scope,
        scope_id=scope_id,
        created_by=created_by,
        title_contains=title,
        limit=limit,
    )
    return [_block_to_dict(b) for b in blocks]


@router.post("/memory")
def create_memory(
    req: CreateMemoryRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    block = service.create_memory(
        type=req.type,
        scope=req.scope,
        title=req.title,
        content=req.content,
        scope_id=req.scope_id,
        created_by=req.created_by,
        metadata=req.metadata,
    )
    return _block_to_dict(block)


@router.get("/memory/{block_id}")
def get_memory(
    block_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    block = service.get_memory(block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Memory block not found")
    return _block_to_dict(block)


@router.put("/memory/{block_id}")
def update_memory(
    block_id: str,
    req: UpdateMemoryRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    data = req.model_dump(exclude_none=True)
    block = service.update_memory(block_id, **data)
    if block is None:
        raise HTTPException(status_code=404, detail="Memory block not found")
    return _block_to_dict(block)


@router.delete("/memory/{block_id}")
def delete_memory(
    block_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    ok = service.delete_memory(block_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory block not found")
    return {"ok": True}


@router.post("/memory/search")
def search_memory(
    q: str,
    limit: int = 50,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    blocks = service.search_memory(query=q, limit=limit)
    return [_block_to_dict(b) for b in blocks]
