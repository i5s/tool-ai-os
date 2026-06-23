from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import json

from toll.council.service import CouncilService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.learning.service import LearningService
from api.dependencies import get_connection_manager

router = APIRouter()


class CreateCouncilSessionRequest(BaseModel):
    task_id: Optional[str] = None
    strategy: str = "majority"
    member_ids: Optional[List[str]] = None


class SubmitVoteRequest(BaseModel):
    agent_id: str
    vote: str
    confidence: float = 1.0


class FinalizeRequest(BaseModel):
    winning_agent_id: Optional[str] = None


def _get_service(cm: ConnectionManager) -> CouncilService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("agent_council", default=False):
        raise HTTPException(status_code=404, detail="Agent council is disabled")
    return CouncilService(cm=cm)


def _to_dict(obj) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dataclass_fields__"):
        return {f: getattr(obj, f) for f in obj.__dataclass_fields__}
    return dict(obj)


def _session_to_dict(s) -> dict:
    d = _to_dict(s)
    return {
        "id": d.get("id"),
        "task_id": d.get("task_id"),
        "status": d.get("status"),
        "strategy": d.get("strategy"),
        "created_at": d.get("created_at"),
        "completed_at": d.get("completed_at"),
    }


def _member_to_dict(m) -> dict:
    d = _to_dict(m)
    return {
        "id": d.get("id"),
        "session_id": d.get("session_id"),
        "agent_id": d.get("agent_id"),
        "role": d.get("role"),
        "agent_name": d.get("agent_name"),
    }


def _vote_to_dict(v) -> dict:
    d = _to_dict(v)
    return {
        "id": d.get("id"),
        "session_id": d.get("session_id"),
        "agent_id": d.get("agent_id"),
        "vote": d.get("vote"),
        "confidence": d.get("confidence"),
        "created_at": d.get("created_at"),
        "agent_name": d.get("agent_name"),
    }


def _decision_to_dict(d) -> dict:
    if d is None:
        return None
    d = _to_dict(d)
    return {
        "id": d.get("id"),
        "session_id": d.get("session_id"),
        "winning_agent_id": d.get("winning_agent_id"),
        "winning_agent_name": d.get("winning_agent_name"),
        "decision_summary": d.get("decision_summary"),
        "rationale": d.get("rationale"),
        "created_at": d.get("created_at"),
    }


@router.get("/council")
def list_sessions(
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    return service.list_sessions(task_id=task_id, status=status)


@router.post("/council")
def create_session(
    req: CreateCouncilSessionRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    try:
        session = service.create_session(
            task_id=req.task_id,
            strategy=req.strategy,
            member_ids=req.member_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _session_to_dict(session)


@router.get("/council/{session_id}")
def get_session(
    session_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    result = service.get_session(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Council session not found")
    return {
        "session": result["session"],
        "members": [_member_to_dict(m) for m in result["members"]],
        "votes": [_vote_to_dict(v) for v in result["votes"]],
        "decision": _decision_to_dict(result["decision"]),
    }


@router.post("/council/{session_id}/vote")
def submit_vote(
    session_id: str,
    req: SubmitVoteRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    try:
        vote = service.submit_vote(
            session_id=session_id,
            agent_id=req.agent_id,
            vote=req.vote,
            confidence=req.confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _vote_to_dict(vote)


@router.post("/council/{session_id}/finalize")
def finalize_session(
    session_id: str,
    req: FinalizeRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    try:
        result = service.finalize_session(session_id, forced_winner=req.winning_agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    learning_flags = FeatureFlags(cm=cm)
    if learning_flags.is_enabled("learning_loop"):
        c_session = result["session"]
        c_decision = result["decision"]
        agent_id = None
        if c_decision and c_decision.get("winning_agent_id"):
            agent_id = c_decision["winning_agent_id"]
        else:
            members = service.repo.list_members(session_id)
            if members:
                agent_id = members[0]["agent_id"]
        if agent_id:
            LearningService(cm).record_council_learning(
                session_id=session_id,
                agent_id=agent_id,
                strategy=c_session.get("strategy", "majority"),
                decision_summary=c_decision.get("decision_summary", "") if c_decision else "",
                rationale=c_decision.get("rationale", "") if c_decision else "",
                winning_agent_id=c_decision.get("winning_agent_id") if c_decision else None,
            )

    return result


@router.get("/council/{session_id}/decision")
def get_decision(
    session_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    session = service.repo.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Council session not found")
    decision = service.repo.get_decision(session_id)
    return {"session": _session_to_dict(session), "decision": _decision_to_dict(decision)}
