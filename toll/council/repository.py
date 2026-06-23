from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from ..core.connection_manager import ConnectionManager
from .models import (
    CouncilSession,
    CouncilMember,
    CouncilVote,
    CouncilDecision,
    CouncilSessionStatus,
    CouncilStrategy,
    CouncilVoteValue,
    CouncilMemberRole,
)


class CouncilRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    # Council sessions --------------------------------------------------
    def create_session(self, task_id: Optional[str], strategy: str) -> CouncilSession:
        session = CouncilSession(
            id=f"council-{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            status=CouncilSessionStatus.OPEN.value,
            strategy=strategy,
        )
        self.cm.execute(
            """INSERT INTO council_sessions (id, task_id, status, strategy, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (session.id, session.task_id, session.status, session.strategy, session.created_at),
        )
        self.cm.commit()
        return session

    def get_session(self, session_id: str) -> Optional[CouncilSession]:
        row = self.cm.execute("SELECT * FROM council_sessions WHERE id = ?", (session_id,)).fetchone()
        return self._row_to_session(row) if row else None

    def list_sessions(self, task_id: Optional[str] = None, status: Optional[str] = None) -> list[CouncilSession]:
        query = "SELECT * FROM council_sessions"
        conditions = []
        params: list[object] = []
        if task_id is not None:
            conditions.append("task_id = ?")
            params.append(task_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"
        rows = self.cm.execute(query, params).fetchall()
        return [self._row_to_session(r) for r in rows]

    def update_session_status(self, session_id: str, status: str, completed_at: Optional[str] = None) -> Optional[CouncilSession]:
        self.cm.execute(
            """UPDATE council_sessions
            SET status = ?, completed_at = ?
            WHERE id = ?""",
            (status, completed_at, session_id),
        )
        self.cm.commit()
        return self.get_session(session_id)

    # Council members ----------------------------------------------------
    def add_member(self, session_id: str, agent_id: str, role: Optional[str] = None) -> CouncilMember:
        member = CouncilMember(
            id=f"council-member-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            agent_id=agent_id,
            role=role or CouncilMemberRole.REVIEWER.value,
        )
        self.cm.execute(
            """INSERT INTO council_members (id, session_id, agent_id, role)
            VALUES (?, ?, ?, ?)""",
            (member.id, member.session_id, member.agent_id, member.role),
        )
        self.cm.commit()
        return member

    def list_members(self, session_id: str) -> list[dict]:
        rows = self.cm.execute(
            """SELECT council_members.*, agents.name as agent_name
            FROM council_members
            LEFT JOIN agents ON agents.id = council_members.agent_id
            WHERE council_members.session_id = ?""",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def member_exists(self, session_id: str, agent_id: str) -> bool:
        row = self.cm.execute(
            "SELECT 1 FROM council_members WHERE session_id = ? AND agent_id = ?",
            (session_id, agent_id),
        ).fetchone()
        return row is not None

    # Council votes ------------------------------------------------------
    def record_vote(self, session_id: str, agent_id: str, vote: str, confidence: float) -> CouncilVote:
        # upsert
        existing = self.cm.execute(
            "SELECT * FROM council_votes WHERE session_id = ? AND agent_id = ?",
            (session_id, agent_id),
        ).fetchone()
        now = datetime.now(timezone.utc).isoformat()
        if existing:
            self.cm.execute(
                """UPDATE council_votes
                SET vote = ?, confidence = ?, created_at = ?
                WHERE session_id = ? AND agent_id = ?""",
                (vote, confidence, now, session_id, agent_id),
            )
            self.cm.commit()
            return CouncilVote(
                id=existing["id"],
                session_id=session_id,
                agent_id=agent_id,
                vote=vote,
                confidence=confidence,
                created_at=now,
            )
        vote_obj = CouncilVote(
            id=f"vote-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            agent_id=agent_id,
            vote=vote,
            confidence=confidence,
        )
        self.cm.execute(
            """INSERT INTO council_votes (id, session_id, agent_id, vote, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (vote_obj.id, vote_obj.session_id, vote_obj.agent_id, vote_obj.vote, vote_obj.confidence, vote_obj.created_at),
        )
        self.cm.commit()
        return vote_obj

    def list_votes(self, session_id: str) -> list[dict]:
        rows = self.cm.execute(
            """SELECT council_votes.*, agents.name as agent_name
            FROM council_votes
            LEFT JOIN agents ON agents.id = council_votes.agent_id
            WHERE council_votes.session_id = ?""",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # Council decisions --------------------------------------------------
    def create_decision(self, session_id: str, decision_summary: str, rationale: Optional[str] = None, winning_agent_id: Optional[str] = None) -> CouncilDecision:
        decision = CouncilDecision(
            id=f"decision-{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            winning_agent_id=winning_agent_id,
            decision_summary=decision_summary,
            rationale=rationale,
        )
        self.cm.execute(
            """INSERT INTO council_decisions
            (id, session_id, winning_agent_id, decision_summary, rationale, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                decision.id,
                decision.session_id,
                decision.winning_agent_id,
                decision.decision_summary,
                decision.rationale,
                decision.created_at,
            ),
        )
        self.cm.commit()
        return decision

    def get_decision(self, session_id: str) -> Optional[dict]:
        row = self.cm.execute(
            """SELECT council_decisions.*, agents.name as winning_agent_name
            FROM council_decisions
            LEFT JOIN agents ON agents.id = council_decisions.winning_agent_id
            WHERE council_decisions.session_id = ?""",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None

    # Helpers ------------------------------------------------------------
    @staticmethod
    def _row_to_session(row) -> CouncilSession:
        return CouncilSession(
            id=row["id"],
            task_id=row["task_id"] if "task_id" in row.keys() else None,
            status=row["status"],
            strategy=row["strategy"],
            created_at=row["created_at"] if "created_at" in row.keys() else "",
            completed_at=row["completed_at"] if "completed_at" in row.keys() else None,
        )
