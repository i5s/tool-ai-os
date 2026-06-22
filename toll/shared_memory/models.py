from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class MemoryBlockType(str, Enum):
    FACT = "fact"
    DECISION = "decision"
    ARTIFACT_REF = "artifact_ref"
    ERROR = "error"
    HINT = "hint"
    CONSTRAINT = "constraint"


class MemoryScope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    WORKSPACE = "workspace"
    AGENT = "agent"


class MemoryLinkRelation(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REFERENCES = "references"
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"


@dataclass
class MemoryBlock:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = MemoryBlockType.FACT.value
    scope: str = MemoryScope.GLOBAL.value
    scope_id: Optional[str] = None
    title: str = ""
    content: Optional[str] = None
    created_by: Optional[str] = None
    metadata: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MemoryLink:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relation: str = MemoryLinkRelation.RELATED_TO.value
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
