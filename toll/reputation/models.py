from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentReputation:
    agent_id: str
    reputation_score: float = 0.0
    quality_score: float = 0.0
    speed_score: float = 0.0
    reliability_score: float = 0.0
    learning_score: float = 0.0
    council_score: float = 0.0
    recommended_rank: str = "worker"
    updated_at: str = ""
