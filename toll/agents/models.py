from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal


class AgentRole(str, Enum):
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    CUSTOM = "custom"


class AgentRank(str, Enum):
    LEADER = "leader"
    DEPUTY = "deputy"
    ADVISOR = "advisor"
    WORKER = "worker"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"


@dataclass
class Agent:
    id: str = ""
    name: str = ""
    role: str = AgentRole.CUSTOM.value
    rank: str = AgentRank.WORKER.value
    status: str = AgentStatus.ACTIVE.value
    provider: str = ""
    model: str = ""
    cost_tier: str = "standard"
    reputation_score: float = 0.0
    quality_score: float = 0.0
    speed_score: float = 0.0
    created_at: str = ""
    updated_at: str = ""
