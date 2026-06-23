from __future__ import annotations

from typing import Optional

from .models import AgentReputation
from .repository import ReputationRepository


class ReputationService:
    def __init__(self, cm):
        self.cm = cm
        self.repo = ReputationRepository(cm)

    def calculate_agent_reputation(self, agent_id: str) -> AgentReputation:
        # Quality: based on execution success rate
        exec_row = self.cm.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as successful
            FROM agent_executions
            WHERE agent_id = ?
            """,
            (agent_id,),
        ).fetchone()
        total_ex = exec_row["total"] if exec_row and exec_row["total"] else 0
        successful_ex = exec_row["successful"] if exec_row and exec_row["successful"] else 0
        quality_score = (successful_ex / total_ex) if total_ex > 0 else 0.0

        # Speed: based on average duration (normalized to 0..1) — 0ms = 1.0, 10000ms = 0.0
        duration_row = self.cm.execute(
            "SELECT AVG(duration_ms) as avg_duration FROM agent_executions WHERE agent_id = ? AND duration_ms IS NOT NULL",
            (agent_id,),
        ).fetchone()
        avg_duration = duration_row["avg_duration"] if duration_row and duration_row["avg_duration"] else 0.0
        speed_score = max(0.0, min(1.0, 1.0 - (avg_duration / 10000.0))) if avg_duration > 0 else 0.0

        # Reliability: weighted mix of quality (60%) and speed (40%)
        reliability_score = (quality_score * 0.6) + (speed_score * 0.4)

        # Learning score: useful/(useful+ignored+incorrect)
        learning_row = self.cm.execute(
            """
            SELECT
                SUM(CASE WHEN lf.feedback_type='useful' THEN 1 ELSE 0 END) as useful,
                SUM(CASE WHEN lf.feedback_type='ignored' THEN 1 ELSE 0 END) as ignored,
                SUM(CASE WHEN lf.feedback_type='incorrect' THEN 1 ELSE 0 END) as incorrect
            FROM learning_entries le
            LEFT JOIN learning_feedback lf ON lf.learning_entry_id = le.id
            WHERE le.agent_id = ?
            """,
            (agent_id,),
        ).fetchone()
        useful = learning_row["useful"] if learning_row and learning_row["useful"] else 0
        ignored = learning_row["ignored"] if learning_row and learning_row["ignored"] else 0
        incorrect = learning_row["incorrect"] if learning_row and learning_row["incorrect"] else 0
        learning_total = useful + ignored + incorrect
        learning_score = (useful / learning_total) if learning_total > 0 else 0.0

        # Council score: participation count + win rate
        member_row = self.cm.execute(
            "SELECT COUNT(DISTINCT session_id) as sessions FROM council_members WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        participation = member_row["sessions"] if member_row and member_row["sessions"] else 0

        win_row = self.cm.execute(
            """
            SELECT COUNT(*) as wins
            FROM council_decisions cd
            JOIN council_sessions cs ON cs.id = cd.session_id
            WHERE cd.winning_agent_id = ? AND cs.status = 'finalized'
            """,
            (agent_id,),
        ).fetchone()
        wins = win_row["wins"] if win_row and win_row["wins"] else 0
        council_score = min(1.0, (participation * 0.05) + (wins * 0.1))

        # Reputation: weighted combination
        reputation_score = (
            (quality_score * 0.30) +
            (speed_score * 0.15) +
            (reliability_score * 0.25) +
            (learning_score * 0.15) +
            (council_score * 0.15)
        )
        reputation_score = round(reputation_score, 4)

        # Recommended rank
        if reputation_score >= 0.9:
            recommended_rank = "leader"
        elif reputation_score >= 0.7:
            recommended_rank = "deputy"
        elif reputation_score >= 0.4:
            recommended_rank = "advisor"
        else:
            recommended_rank = "worker"

        return AgentReputation(
            agent_id=agent_id,
            reputation_score=reputation_score,
            quality_score=round(quality_score, 4),
            speed_score=round(speed_score, 4),
            reliability_score=round(reliability_score, 4),
            learning_score=round(learning_score, 4),
            council_score=round(council_score, 4),
            recommended_rank=recommended_rank,
        )

    def refresh_agent_reputation(self, agent_id: str) -> AgentReputation:
        rep = self.calculate_agent_reputation(agent_id)
        self.repo.upsert(rep)
        return rep

    def get_agent_reputation(self, agent_id: str) -> Optional[AgentReputation]:
        return self.repo.get(agent_id)

    def get_leaderboard(self, limit: int = 10) -> list[AgentReputation]:
        return self.repo.get_leaderboard(limit=limit)
