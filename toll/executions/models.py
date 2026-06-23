from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AgentExecution:
    id: str
    task_id: str
    agent_id: str
    status: str  # running | completed | failed
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_metadata: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
