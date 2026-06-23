from __future__ import annotations

from typing import Optional

from .models import AgentReputation


class ReputationRepository:
    def __init__(self, cm):
        self.cm = cm

    def get(self, agent_id: str) -> Optional[AgentReputation]:
        row = self.cm.execute(
            "SELECT * FROM agent_reputation WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        if not row:
            return None
        return AgentReputation(
            agent_id=row["agent_id"],
            reputation_score=row["reputation_score"],
            quality_score=row["quality_score"],
            speed_score=row["speed_score"],
            reliability_score=row["reliability_score"],
            learning_score=row["learning_score"],
            council_score=row["council_score"],
            recommended_rank=row["recommended_rank"],
            updated_at=row["updated_at"],
        )

    def upsert(self, rep: AgentReputation):
        self.cm.execute(
            """
            INSERT OR REPLACE INTO agent_reputation (
                agent_id, reputation_score, quality_score, speed_score,
                reliability_score, learning_score, council_score,
                recommended_rank, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            """,
            (
                rep.agent_id,
                rep.reputation_score,
                rep.quality_score,
                rep.speed_score,
                rep.reliability_score,
                rep.learning_score,
                rep.council_score,
                rep.recommended_rank,
            ),
        )
        self.cm.commit()

    def get_leaderboard(self, limit: int = 10) -> list[AgentReputation]:
        rows = self.cm.execute(
            "SELECT * FROM agent_reputation ORDER BY reputation_score DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            AgentReputation(
                agent_id=r["agent_id"],
                reputation_score=r["reputation_score"],
                quality_score=r["quality_score"],
                speed_score=r["speed_score"],
                reliability_score=r["reliability_score"],
                learning_score=r["learning_score"],
                council_score=r["council_score"],
                recommended_rank=r["recommended_rank"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]
