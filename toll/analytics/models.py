from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AgentMetrics:
    agent_id: str
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    average_duration_ms: float = 0.0
    council_participation_count: int = 0
    learning_entries_created: int = 0
