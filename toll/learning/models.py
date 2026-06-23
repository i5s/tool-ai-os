from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class LearningSourceType(str, Enum):
    EXECUTION = "execution"
    COUNCIL = "council"
    TASK = "task"


class LearningFeedbackType(str, Enum):
    USEFUL = "useful"
    IGNORED = "ignored"
    INCORRECT = "incorrect"


@dataclass
class LearningEntry:
    id: str
    source_type: str
    source_id: str
    agent_id: str
    title: str
    lesson: str
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class LearningFeedback:
    id: str
    learning_entry_id: str
    feedback_type: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
