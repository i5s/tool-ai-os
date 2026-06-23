from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from .repository import CouncilRepository
from .models import (
    CouncilSession,
    CouncilMember,
    CouncilVote,
    CouncilSessionStatus,
    CouncilStrategy,
    CouncilVoteValue,
    CouncilMemberRole,
)


class CouncilService:
    def __init__(self, cm):
        self.cm = cm
        self.repo = CouncilRepository(cm)

    def create_session(self, task_id: Optional[str], strategy: str, member_ids: Optional[list[str]] = None) -> CouncilSession:
        session = self.repo.create_session(task_id=task_id, strategy=strategy)
        if member_ids:
            for raw in member_ids:
                resolved = self._resolve_agent_id(raw)
                self.repo.add_member(session.id, resolved, role="reviewer")
        return session

    def add_member(self, session_id: str, agent_identifier: str, role: Optional[str] = None) -> CouncilMember:
        agent_id = self._resolve_agent_id(agent_identifier)
        if self.repo.member_exists(session_id, agent_id):
            raise ValueError("Agent is already a member of this session")
        return self.repo.add_member(session_id, agent_id, role=role)

    def submit_vote(self, session_id: str, agent_id: str, vote: str, confidence: float = 1.0) -> CouncilVote:
        session = self.repo.get_session(session_id)
        if session is None:
            raise ValueError("Council session not found")
        if session.status not in (CouncilSessionStatus.OPEN.value, CouncilSessionStatus.VOTING.value):
            raise ValueError(f"Cannot vote on session in status {session.status}")
        if vote not in (CouncilVoteValue.APPROVE.value, CouncilVoteValue.REJECT.value, CouncilVoteValue.ABSTAIN.value):
            raise ValueError("Vote must be one of: approve, reject, abstain")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        agent_id = self._resolve_agent_id(agent_id)
        if session.status == CouncilSessionStatus.OPEN.value:
            self.repo.update_session_status(session_id, CouncilSessionStatus.VOTING.value)
        return self.repo.record_vote(session_id, agent_id, vote, confidence)

    def finalize_session(self, session_id: str, forced_winner: Optional[str] = None) -> dict:
        session = self.repo.get_session(session_id)
        if session is None:
            raise ValueError("Council session not found")
        if session.status in (CouncilSessionStatus.COMPLETED.value, CouncilSessionStatus.FAILED.value):
            raise ValueError("Session is already finalized")
        votes = self.repo.list_votes(session_id)
        if not votes:
            raise ValueError("No votes recorded")
        completed_session = self.repo.update_session_status(
            session_id, CouncilSessionStatus.COMPLETED.value, datetime.now().isoformat()
        )
        decision = self._compute_decision(
            completed_session,
            votes,
            self.repo.list_members(session_id),
            forced_winner,
        )
        winning_id = decision["winning_agent_id"]
        if winning_id is not None and len(winning_id) != 36:  # not a UUID, look up by name
            row = self.cm.execute("SELECT id FROM agents WHERE name = ?", (winning_id,)).fetchone()
            if row:
                winning_id = row["id"]
        self.repo.create_decision(
            session_id=completed_session.id,
            decision_summary=decision["summary"],
            rationale=decision["rationale"],
            winning_agent_id=winning_id,
        )
        return {
            "session": self._session_to_dict(completed_session),
            "decision": decision,
        }

    def get_session(self, session_id: str) -> Optional[dict]:
        session = self.repo.get_session(session_id)
        if session is None:
            return None
        members = self.repo.list_members(session_id)
        votes = self.repo.list_votes(session_id)
        decision = self.repo.get_decision(session_id)
        return {
            "session": self._session_to_dict(session),
            "members": members,
            "votes": votes,
            "decision": decision,
        }

    def list_sessions(self, task_id: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        sessions = self.repo.list_sessions(task_id=task_id, status=status)
        return [self._session_to_dict(s) for s in sessions]

    # Internal helpers ---------------------------------------------------
    def _resolve_agent_id(self, identifier: str) -> str:
        # Try exact match as ID first
        row = self.cm.execute("SELECT id, name FROM agents WHERE id = ?", (identifier,)).fetchone()
        if row:
            return row["id"]
        # Fallback to name lookup
        row = self.cm.execute("SELECT id, name FROM agents WHERE name = ?", (identifier,)).fetchone()
        if row:
            return row["id"]
        raise ValueError(f"Agent {identifier} not found")

    def _allowed_agents(self) -> list[str]:
        return ["Hermes", "OpenCode", "Ollama"]

    def _session_to_dict(self, s: CouncilSession) -> dict:
        return {
            "id": s.id,
            "task_id": s.task_id,
            "status": s.status,
            "strategy": s.strategy,
            "created_at": s.created_at,
            "completed_at": s.completed_at,
        }

    def _compute_decision(self, session, votes, members, forced_winner: Optional[str] = None) -> dict:
        strategy = session.strategy
        if forced_winner:
            return {
                "winning_agent_id": forced_winner,
                "summary": f"Decision set to {forced_winner}",
                "rationale": "Manual override during finalization",
            }
        tally: dict[str, int] = {}
        for v in votes:
            key = v.get("agent_name") or v["agent_id"]
            if v["vote"] == CouncilVoteValue.APPROVE.value:
                tally[key] = tally.get(key, 0) + 1
            elif v["vote"] == CouncilVoteValue.REJECT.value:
                tally[key] = tally.get(key, 0) - 1
        if strategy == CouncilStrategy.MAJORITY.value:
            if not tally:
                return {
                    "winning_agent_id": None,
                    "summary": "No decisive votes",
                    "rationale": "No approve or reject votes recorded",
                }
            winner = max(tally, key=tally.get)
            return {
                "winning_agent_id": winner,
                "summary": f"Selected {winner} by majority vote",
                "rationale": f"Tallies: {tally}",
            }
        if strategy == CouncilStrategy.CONSENSUS.value:
            approves = sum(1 for v in votes if v["vote"] == CouncilVoteValue.APPROVE.value)
            rejects = sum(1 for v in votes if v["vote"] == CouncilVoteValue.REJECT.value)
            abstains = sum(1 for v in votes if v["vote"] == CouncilVoteValue.ABSTAIN.value)
            if rejects == 0 and approves > 0:
                winner = votes[0]["agent_name"] or votes[0]["agent_id"]
                return {
                    "winning_agent_id": winner,
                    "summary": "Consensus reached — unanimous approval",
                    "rationale": f"approves={approves}, abstains={abstains}, rejects={rejects}",
                }
            return {
                "winning_agent_id": None,
                "summary": "Consensus not reached",
                "rationale": f"approves={approves}, abstains={abstains}, rejects={rejects}",
            }
        raise ValueError(f"Unknown strategy: {strategy}")
