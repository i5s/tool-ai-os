from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from ..core.connection_manager import ConnectionManager
from .models import Agent, AgentRole, AgentRank, AgentStatus


class AgentRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def create(self, agent: Agent) -> Agent:
        now = datetime.now(timezone.utc).isoformat()
        agent.id = agent.id or str(uuid.uuid4())
        agent.created_at = now
        agent.updated_at = now
        self.cm.execute(
            """
            INSERT INTO agents (id, name, role, rank, status, provider, model,
                                cost_tier, reputation_score, quality_score, speed_score,
                                created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent.id,
                agent.name,
                agent.role,
                agent.rank,
                agent.status,
                agent.provider,
                agent.model,
                agent.cost_tier,
                agent.reputation_score,
                agent.quality_score,
                agent.speed_score,
                agent.created_at,
                agent.updated_at,
            ),
        )
        self.cm.commit()
        return agent

    def get(self, agent_id: str) -> Optional[Agent]:
        row = self.cm.connection.execute(
            "SELECT * FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_agent(row)

    def list(
        self,
        role: Optional[str] = None,
        rank: Optional[str] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        name_contains: Optional[str] = None,
        limit: int = 100,
    ) -> list[Agent]:
        parts = ["SELECT * FROM agents WHERE 1=1"]
        params: list[object] = []
        if role:
            parts.append("AND role = ?")
            params.append(role)
        if rank:
            parts.append("AND rank = ?")
            params.append(rank)
        if status:
            parts.append("AND status = ?")
            params.append(status)
        if provider:
            parts.append("AND provider = ?")
            params.append(provider)
        if name_contains:
            parts.append("AND name LIKE ?")
            params.append(f"%{name_contains}%")
        parts.append("ORDER BY created_at DESC LIMIT ?")
        params.append(limit)
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_agent(r) for r in rows]

    def update(self, agent: Agent) -> Optional[Agent]:
        agent.updated_at = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """
            UPDATE agents
            SET name = ?, role = ?, rank = ?, status = ?, provider = ?, model = ?,
                cost_tier = ?, reputation_score = ?, quality_score = ?, speed_score = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                agent.name,
                agent.role,
                agent.rank,
                agent.status,
                agent.provider,
                agent.model,
                agent.cost_tier,
                agent.reputation_score,
                agent.quality_score,
                agent.speed_score,
                agent.updated_at,
                agent.id,
            ),
        )
        self.cm.commit()
        return agent if self.cm.connection.total_changes > 0 else None

    def delete(self, agent_id: str) -> bool:
        cursor = self.cm.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        self.cm.commit()
        return cursor.rowcount > 0

    def promote(self, agent_id: str) -> Optional[Agent]:
        agent = self.get(agent_id)
        if agent is None:
            return None
        order = [AgentRank.WORKER.value, AgentRank.ADVISOR.value, AgentRank.DEPUTY.value, AgentRank.LEADER.value]
        try:
            idx = order.index(agent.rank)
            if idx >= len(order) - 1:
                return agent
            agent.rank = order[idx + 1]
        except ValueError:
            return agent
        return self.update(agent)

    def demote(self, agent_id: str) -> Optional[Agent]:
        agent = self.get(agent_id)
        if agent is None:
            return None
        order = [AgentRank.WORKER.value, AgentRank.ADVISOR.value, AgentRank.DEPUTY.value, AgentRank.LEADER.value]
        try:
            idx = order.index(agent.rank)
            if idx <= 0:
                return agent
            agent.rank = order[idx - 1]
        except ValueError:
            return agent
        return self.update(agent)

    def seed_if_empty(self) -> None:
        existing = self.cm.execute("SELECT COUNT(*) as cnt FROM agents").fetchone()
        if existing and existing["cnt"] > 0:
            return
        now = datetime.now(timezone.utc).isoformat()
        seeds = [
            ("Hermes", AgentRole.ARCHITECT.value, AgentRank.LEADER.value, "Standard", "Hermes", "hermes-runtime", 1.0),
            ("OpenCode", AgentRole.DEVELOPER.value, AgentRank.DEPUTY.value, "Standard", "OpenCode", "opencode-runtime", 1.0),
            ("Open Design", AgentRole.DESIGNER.value, AgentRank.ADVISOR.value, "Standard", "Open Design", "opendesign-runtime", 1.0),
            ("Ollama", AgentRole.RESEARCHER.value, AgentRank.ADVISOR.value, "Local", "Ollama", "ollama-runtime", 1.0),
        ]
        for name, role, rank, provider, model, cost_tier, reputation in seeds:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=name,
                role=role,
                rank=rank,
                status=AgentStatus.ACTIVE.value,
                provider=provider,
                model=model,
                cost_tier=cost_tier,
                reputation_score=reputation,
                quality_score=0.8,
                speed_score=0.7,
                created_at=now,
                updated_at=now,
            )
            self.create(agent)

    @staticmethod
    def _row_to_agent(row) -> Agent:
        return Agent(
            id=row["id"],
            name=row["name"],
            role=row["role"],
            rank=row["rank"],
            status=row["status"],
            provider=row["provider"],
            model=row["model"],
            cost_tier=row["cost_tier"] if "cost_tier" in row.keys() else "standard",
            reputation_score=row["reputation_score"] if "reputation_score" in row.keys() else 0.0,
            quality_score=row["quality_score"] if "quality_score" in row.keys() else 0.0,
            speed_score=row["speed_score"] if "speed_score" in row.keys() else 0.0,
            created_at=row["created_at"] if "created_at" in row.keys() else "",
            updated_at=row["updated_at"] if "updated_at" in row.keys() else "",
        )
