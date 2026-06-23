from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional


class CouncilSessionStatus(str, Enum):
    OPEN = "open"
    VOTING = "voting"
    COMPLETED = "completed"
    FAILED = "failed"


class CouncilStrategy(str, Enum):
    MAJORITY = "majority"
    CONSENSUS = "consensus"


class CouncilVoteValue(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class CouncilMemberRole(str, Enum):
    PROPOSER = "proposer"
    REVIEWER = "reviewer"
    ARBITRATOR = "arbitrator"


@dataclass
class CouncilSession:
    id: str
    task_id: Optional[str] = None
    status: str = CouncilSessionStatus.OPEN.value
    strategy: str = CouncilStrategy.MAJORITY.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


@dataclass
class CouncilMember:
    id: str
    session_id: str
    agent_id: str
    role: str = CouncilMemberRole.REVIEWER.value


@dataclass
class CouncilVote:
    id: str
    session_id: str
    agent_id: str
    vote: str
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CouncilDecision:
    id: str
    session_id: str
    winning_agent_id: Optional[str] = None
    decision_summary: str = ""
    rationale: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
