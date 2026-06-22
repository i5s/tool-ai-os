from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from toll.agents.models import Agent, AgentRole, AgentRank, AgentStatus
from toll.agents.service import AgentService
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from api.dependencies import get_connection_manager

router = APIRouter()


class CreateAgentRequest(BaseModel):
    name: str
    role: str = AgentRole.CUSTOM.value
    rank: str = AgentRank.WORKER.value
    status: str = AgentStatus.ACTIVE.value
    provider: str = ""
    model: str = ""
    cost_tier: str = "standard"
    reputation_score: float = 0.0
    quality_score: float = 0.0
    speed_score: float = 0.0


class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    rank: Optional[str] = None
    status: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    cost_tier: Optional[str] = None
    reputation_score: Optional[float] = None
    quality_score: Optional[float] = None
    speed_score: Optional[float] = None


def _get_service(cm: ConnectionManager) -> AgentService:
    flags = FeatureFlags(cm=cm)
    if not flags.is_enabled("agent_runtime", default=False):
        raise HTTPException(status_code=404, detail="Agent runtime is disabled")
    return AgentService(cm=cm)


def _agent_to_dict(agent: Agent) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "rank": agent.rank,
        "status": agent.status,
        "provider": agent.provider,
        "model": agent.model,
        "cost_tier": agent.cost_tier,
        "reputation_score": agent.reputation_score,
        "quality_score": agent.quality_score,
        "speed_score": agent.speed_score,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
    }


@router.get("/agents")
def list_agents(
    role: Optional[str] = None,
    rank: Optional[str] = None,
    status: Optional[str] = None,
    provider: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    agents = service.list_agents(role, rank, status, provider, name, limit)
    return [_agent_to_dict(a) for a in agents]


@router.post("/agents")
def create_agent(
    req: CreateAgentRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    agent = service.create_agent(
        name=req.name,
        role=req.role,
        rank=req.rank,
        status=req.status,
        provider=req.provider,
        model=req.model,
        cost_tier=req.cost_tier,
        reputation_score=req.reputation_score,
        quality_score=req.quality_score,
        speed_score=req.speed_score,
    )
    return _agent_to_dict(agent)


@router.get("/agents/{agent_id}")
def get_agent(
    agent_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    agent = service.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.put("/agents/{agent_id}")
def update_agent(
    agent_id: str,
    req: UpdateAgentRequest,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    agent = service.update_agent(
        agent_id,
        name=req.name,
        role=req.role,
        rank=req.rank,
        status=req.status,
        provider=req.provider,
        model=req.model,
        cost_tier=req.cost_tier,
        reputation_score=req.reputation_score,
        quality_score=req.quality_score,
        speed_score=req.speed_score,
    )
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.delete("/agents/{agent_id}")
def delete_agent(
    agent_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    deleted = service.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"ok": True}


@router.post("/agents/{agent_id}/promote")
def promote_agent(
    agent_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    agent = service.promote_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)


@router.post("/agents/{agent_id}/demote")
def demote_agent(
    agent_id: str,
    cm: ConnectionManager = Depends(get_connection_manager),
):
    service = _get_service(cm)
    agent = service.demote_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_to_dict(agent)
