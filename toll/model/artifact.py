from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..core.connection_manager import ConnectionManager


class ArtifactType(str, Enum):
    CAROUSEL = "carousel"
    REPORT = "report"
    PRESENTATION = "presentation"
    CODE = "code"
    SEARCH_RESULT = "search_result"
    PROMPT = "prompt"
    SOCIAL_POST = "social_post"
    RESEARCH = "research"
    IMAGE = "image"
    IMAGE_GEN = "image_gen"
    VIDEO = "video"
    GENERIC = "generic"


class ArtifactStatus(str, Enum):
    DRAFT = "draft"
    COMPLETED = "artifact_completed"
    FAILED = "artifact_failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class Artifact:
    id: str
    type: ArtifactType
    status: ArtifactStatus
    title: str
    version: int = 1
    parent_artifact_id: str | None = None
    workflow_id: str | None = None
    conversation_id: str | None = None
    content: dict = field(default_factory=dict)
    rendered_path: str | None = None
    preview_url: str | None = None
    provider: str | None = None
    model: str | None = None
    intent: str | None = None
    workspace_type: str | None = None
    workspace_id: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    expires_at: str | None = None


class ArtifactRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def create(self, artifact: Artifact) -> Artifact:
        now = datetime.now(timezone.utc).isoformat()
        artifact.id = artifact.id or str(uuid.uuid4())
        artifact.created_at = now
        artifact.updated_at = now
        self._upsert(artifact)
        return artifact

    def update(self, artifact: Artifact) -> Artifact:
        artifact.updated_at = datetime.now(timezone.utc).isoformat()
        self._upsert(artifact)
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        row = self.cm.connection.execute(
            "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_artifact(row)

    def list(
        self,
        type: ArtifactType | None = None,
        status: ArtifactStatus | None = None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[Artifact]:
        parts = ["SELECT * FROM artifacts WHERE 1=1"]
        params: list[Any] = []
        if type:
            parts.append("AND type = ?")
            params.append(type.value)
        if status:
            parts.append("AND status = ?")
            params.append(status.value)
        if workflow_id:
            parts.append("AND workflow_id = ?")
            params.append(workflow_id)
        parts.append("ORDER BY updated_at DESC LIMIT ?")
        params.append(limit)
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_artifact(r) for r in rows]

    def delete(self, artifact_id: str) -> bool:
        art = self.get(artifact_id)
        if not art:
            return False
        art.status = ArtifactStatus.DELETED
        self.update(art)
        return True

    def next_version(self, artifact_id: str) -> Artifact | None:
        parent = self.get(artifact_id)
        if not parent:
            return None
        child = Artifact(
            id=str(uuid.uuid4()),
            type=parent.type,
            status=ArtifactStatus.DRAFT,
            title=parent.title,
            version=parent.version + 1,
            parent_artifact_id=parent.id,
            workflow_id=parent.workflow_id,
            conversation_id=parent.conversation_id,
            workspace_type=parent.workspace_type,
            workspace_id=parent.workspace_id,
            tags=list(parent.tags),
        )
        return child

    def _upsert(self, artifact: Artifact):
        self.cm.execute(
            """
            INSERT INTO artifacts (
                id, type, status, title, version, parent_artifact_id,
                workflow_id, conversation_id, content, rendered_path, preview_url,
                provider, model, intent, workspace_type, workspace_id, tags,
                metadata, created_at, updated_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                status = excluded.status,
                title = excluded.title,
                version = excluded.version,
                content = excluded.content,
                rendered_path = excluded.rendered_path,
                preview_url = excluded.preview_url,
                provider = excluded.provider,
                model = excluded.model,
                intent = excluded.intent,
                workspace_type = excluded.workspace_type,
                workspace_id = excluded.workspace_id,
                tags = excluded.tags,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at,
                expires_at = excluded.expires_at
            """,
            (
                artifact.id,
                artifact.type.value,
                artifact.status.value,
                artifact.title,
                artifact.version,
                artifact.parent_artifact_id,
                artifact.workflow_id,
                artifact.conversation_id,
                json.dumps(artifact.content, ensure_ascii=False),
                artifact.rendered_path,
                artifact.preview_url,
                artifact.provider,
                artifact.model,
                artifact.intent,
                artifact.workspace_type,
                artifact.workspace_id,
                json.dumps(artifact.tags, ensure_ascii=False),
                json.dumps(artifact.metadata, ensure_ascii=False),
                artifact.created_at,
                artifact.updated_at,
                artifact.expires_at,
            ),
        )
        self.cm.commit()

    def _row_to_artifact(self, row) -> Artifact:
        return Artifact(
            id=row["id"],
            type=ArtifactType(row["type"]),
            status=ArtifactStatus(row["status"]),
            title=row["title"],
            version=row["version"],
            parent_artifact_id=row["parent_artifact_id"],
            workflow_id=row["workflow_id"],
            conversation_id=row["conversation_id"],
            content=json.loads(row["content"]) if row["content"] else {},
            rendered_path=row["rendered_path"],
            preview_url=row["preview_url"],
            provider=row["provider"],
            model=row["model"],
            intent=row["intent"],
            workspace_type=row["workspace_type"],
            workspace_id=row["workspace_id"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            expires_at=row["expires_at"],
        )

    def expire_before(self, cutoff: str) -> list[Artifact]:
        rows = self.cm.connection.execute(
            "SELECT * FROM artifacts WHERE expires_at IS NOT NULL AND expires_at < ? AND status NOT IN ('archived', 'deleted')",
            (cutoff,),
        ).fetchall()
        return [self._row_to_artifact(r) for r in rows]
