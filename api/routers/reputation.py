from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from toll.reputation.models import AgentReputation
from toll.reputation.service import ReputationService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


def _require_flag(cm: ConnectionManager):
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("agent_reputation"):
        raise HTTPException(status_code=404, detail="Not found")
    return flags


def _to_dict(m: AgentReputation) -> dict:
    return {
        "agent_id": m.agent_id,
        "reputation_score": m.reputation_score,
        "quality_score": m.quality_score,
        "speed_score": m.speed_score,
        "reliability_score": m.reliability_score,
        "learning_score": m.learning_score,
        "council_score": m.council_score,
        "recommended_rank": m.recommended_rank,
        "updated_at": m.updated_at,
    }


@router.get("/reputation")
def list_reputations(cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = ReputationService(cm)
    rows = cm.execute("SELECT agent_id FROM agents ORDER BY id").fetchall()
    result = []
    for r in rows:
        rep = svc.refresh_agent_reputation(r["agent_id"])
        result.append(_to_dict(rep))
    result.sort(key=lambda x: x["reputation_score"], reverse=True)
    return result


@router.get("/reputation/leaderboard")
def get_leaderboard(limit: int = 10, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = ReputationService(cm)
    return [_to_dict(m) for m in svc.get_leaderboard(limit=limit)]


@router.get("/reputation/{agent_id}")
def get_reputation(agent_id: str, cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = ReputationService(cm)
    rep = svc.refresh_agent_reputation(agent_id)
    return _to_dict(rep)


@router.post("/reputation/recalculate_all")
def recalculate_all(cm: ConnectionManager = Depends(get_connection_manager)):
    _require_flag(cm)
    svc = ReputationService(cm)
    rows = cm.execute("SELECT agent_id FROM agents ORDER BY id").fetchall()
    result = []
    for r in rows:
        rep = svc.refresh_agent_reputation(r["agent_id"])
        result.append(_to_dict(rep))
    result.sort(key=lambda x: x["reputation_score"], reverse=True)
    return result

