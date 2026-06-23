from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RuntimeJob:
    id: str = ""
    task_id: str = ""
    council_session_id: Optional[str] = None
    status: str = JobStatus.PENDING.value
    plan_text: Optional[str] = None
    merged_result: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class RuntimeAssignment:
    id: str = ""
    runtime_job_id: str = ""
    task_fragment: str = ""
    assigned_agent_id: str = ""
    status: str = JobStatus.PENDING.value
    execution_id: Optional[str] = None
    created_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class RuntimeResult:
    id: str = ""
    runtime_assignment_id: str = ""
    agent_id: str = ""
    result: str = ""
    metadata: Optional[str] = None
    created_at: str = ""


@dataclass
class RuntimeMemory:
    id: str = ""
    runtime_job_id: str = ""
    memory_type: str = ""
    content: str = ""
    created_at: str = ""
