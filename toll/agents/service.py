from __future__ import annotations

from typing import Optional

from .models import Agent, AgentRank, AgentRole, AgentStatus
from .repository import AgentRepository
from ..core.connection_manager import ConnectionManager


class AgentService:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm
        self.repo = AgentRepository(cm)
        self.repo.seed_if_empty()

    def create_agent(
        self,
        name: str,
        role: str = AgentRole.CUSTOM.value,
        rank: str = AgentRank.WORKER.value,
        status: str = AgentStatus.ACTIVE.value,
        provider: str = "",
        model: str = "",
        cost_tier: str = "standard",
        reputation_score: float = 0.0,
        quality_score: float = 0.0,
        speed_score: float = 0.0,
    ) -> Agent:
        return self.repo.create(
            Agent(
                name=name,
                role=role,
                rank=rank,
                status=status,
                provider=provider,
                model=model,
                cost_tier=cost_tier,
                reputation_score=reputation_score,
                quality_score=quality_score,
                speed_score=speed_score,
            )
        )

    def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        rank: Optional[str] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        cost_tier: Optional[str] = None,
        reputation_score: Optional[float] = None,
        quality_score: Optional[float] = None,
        speed_score: Optional[float] = None,
    ) -> Optional[Agent]:
        agent = self.repo.get(agent_id)
        if agent is None:
            return None
        if name is not None:
            agent.name = name
        if role is not None:
            agent.role = role
        if rank is not None:
            agent.rank = rank
        if status is not None:
            agent.status = status
        if provider is not None:
            agent.provider = provider
        if model is not None:
            agent.model = model
        if cost_tier is not None:
            agent.cost_tier = cost_tier
        if reputation_score is not None:
            agent.reputation_score = reputation_score
        if quality_score is not None:
            agent.quality_score = quality_score
        if speed_score is not None:
            agent.speed_score = speed_score
        return self.repo.update(agent)

    def delete_agent(self, agent_id: str) -> bool:
        return self.repo.delete(agent_id)

    def list_agents(
        self,
        role: Optional[str] = None,
        rank: Optional[str] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        name_contains: Optional[str] = None,
        limit: int = 100,
    ) -> list[Agent]:
        return self.repo.list(role, rank, status, provider, name_contains, limit)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.repo.get(agent_id)

    def promote_agent(self, agent_id: str) -> Optional[Agent]:
        return self.repo.promote(agent_id)

    def demote_agent(self, agent_id: str) -> Optional[Agent]:
        return self.repo.demote(agent_id)
