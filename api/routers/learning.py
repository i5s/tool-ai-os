from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.learning.service import LearningService
from api.dependencies import get_connection_manager

router = APIRouter()


class LearningCreateRequest(BaseModel):
    source_type: str
    source_id: str
    agent_id: str
    title: str
    lesson: str
    confidence: float = 1.0


class FeedbackRequest(BaseModel):
    feedback_type: str


def _require_flag(cm: ConnectionManager):
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("learning_loop"):
        raise HTTPException(status_code=404, detail="Not found")
    return flags


@router.get("/learning")
def list_learning(
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    _require_flag(cm)
    service = LearningService(cm)
    return service.list_learning(source_type=source_type, source_id=source_id)


@router.post("/learning")
def create_learning(req: LearningCreateRequest, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    try:
        entry = LearningService(cm).create_learning(
            source_type=req.source_type,
            source_id=req.source_id,
            agent_id=req.agent_id,
            title=req.title,
            lesson=req.lesson,
            confidence=req.confidence,
        )
        return _entry_to_dict(entry)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/learning/{entry_id}")
def get_learning(entry_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    row = LearningService(cm).get_learning(entry_id)
    if not row:
        raise HTTPException(status_code=404, detail="Learning entry not found")
    return row


@router.post("/learning/{entry_id}/useful")
def mark_useful(entry_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    try:
        return LearningService(cm).mark_useful(entry_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Learning entry not found")


@router.post("/learning/{entry_id}/ignored")
def mark_ignored(entry_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    try:
        return LearningService(cm).mark_ignored(entry_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Learning entry not found")


@router.post("/learning/{entry_id}/incorrect")
def mark_incorrect(entry_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    try:
        return LearningService(cm).mark_incorrect(entry_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Learning entry not found")


def _entry_to_dict(entry) -> dict:
    return {
        "id": entry.id,
        "source_type": entry.source_type,
        "source_id": entry.source_id,
        "agent_id": entry.agent_id,
        "title": entry.title,
        "lesson": entry.lesson,
        "confidence": entry.confidence,
        "created_at": entry.created_at,
    }
