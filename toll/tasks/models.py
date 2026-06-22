from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskEventType(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    COMMENTED = "commented"


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: Optional[str] = None
    status: str = TaskStatus.DRAFT.value
    priority: str = TaskPriority.MEDIUM.value
    created_by: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


@dataclass
class TaskEvent:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    event_type: str = TaskEventType.CREATED.value
    actor: Optional[str] = None
    payload: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
