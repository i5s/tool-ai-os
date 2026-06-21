from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..core.connection_manager import ConnectionManager


@dataclass
class PromptProfile:
    id: str
    name: str
    media_types: list[str] = field(default_factory=lambda: ["image"])
    template: str = ""
    default_params: dict = field(default_factory=dict)
    compatible_models: list[str] = field(default_factory=list)
    weight_criteria: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    version: int = 1
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""


class PromptProfileRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def create(self, profile: PromptProfile) -> PromptProfile:
        now = datetime.now(timezone.utc).isoformat()
        profile.id = profile.id or str(uuid.uuid4())
        profile.created_at = now
        profile.updated_at = now
        self._upsert(profile)
        return profile

    def get(self, profile_id: str) -> PromptProfile | None:
        row = self.cm.connection.execute(
            "SELECT * FROM prompt_profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        return self._row_to_profile(row) if row else None

    def list(self, media_type: str | None = None, tag: str | None = None) -> list[PromptProfile]:
        parts = ["SELECT * FROM prompt_profiles WHERE 1=1"]
        params: list[Any] = []
        if media_type:
            parts.append("AND media_types LIKE ?")
            params.append(f"%{media_type}%")
        if tag:
            parts.append("AND tags LIKE ?")
            params.append(f"%{tag}%")
        parts.append("ORDER BY name ASC")
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_profile(r) for r in rows]

    def update(self, profile_id: str, updates: dict) -> PromptProfile | None:
        existing = self.get(profile_id)
        if not existing:
            return None
        for key, val in updates.items():
            if hasattr(existing, key):
                setattr(existing, key, val)
        existing.updated_at = datetime.now(timezone.utc).isoformat()
        existing.version += 1
        self._upsert(existing)
        self._save_version(existing)
        return existing

    def delete(self, profile_id: str) -> bool:
        self.cm.execute("DELETE FROM prompt_profile_versions WHERE profile_id = ?", (profile_id,))
        self.cm.execute("DELETE FROM prompt_profiles WHERE id = ?", (profile_id,))
        self.cm.commit()
        return True

    def _upsert(self, profile: PromptProfile):
        self.cm.execute(
            """INSERT INTO prompt_profiles
               (id, name, media_types, template, default_params, compatible_models,
                weight_criteria, tags, version, enabled, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                name = excluded.name, media_types = excluded.media_types,
                template = excluded.template, default_params = excluded.default_params,
                compatible_models = excluded.compatible_models,
                weight_criteria = excluded.weight_criteria, tags = excluded.tags,
                version = excluded.version, enabled = excluded.enabled,
                updated_at = excluded.updated_at""",
            (
                profile.id, profile.name,
                json.dumps(profile.media_types, ensure_ascii=False),
                profile.template,
                json.dumps(profile.default_params, ensure_ascii=False),
                json.dumps(profile.compatible_models, ensure_ascii=False),
                json.dumps(profile.weight_criteria, ensure_ascii=False),
                json.dumps(profile.tags, ensure_ascii=False),
                profile.version, profile.enabled,
                profile.created_at, profile.updated_at,
            ),
        )
        self.cm.commit()

    def _save_version(self, profile: PromptProfile):
        self.cm.execute(
            """INSERT INTO prompt_profile_versions
               (profile_id, version, template, default_params, changed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                profile.id, profile.version, profile.template,
                json.dumps(profile.default_params, ensure_ascii=False),
                profile.updated_at,
            ),
        )
        self.cm.commit()

    def get_version_history(self, profile_id: str) -> list[dict]:
        rows = self.cm.connection.execute(
            "SELECT version, template, default_params, changed_at"
            " FROM prompt_profile_versions WHERE profile_id = ?"
            " ORDER BY version DESC", (profile_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _row_to_profile(row) -> PromptProfile:
        return PromptProfile(
            id=row["id"],
            name=row["name"],
            media_types=json.loads(row["media_types"]) if isinstance(row["media_types"], str) else row["media_types"],
            template=row["template"],
            default_params=json.loads(row["default_params"]) if isinstance(row["default_params"], str) else row["default_params"],
            compatible_models=json.loads(row["compatible_models"]) if isinstance(row["compatible_models"], str) else row["compatible_models"],
            weight_criteria=json.loads(row["weight_criteria"]) if isinstance(row["weight_criteria"], str) else row["weight_criteria"],
            tags=json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"],
            version=row["version"],
            enabled=row["enabled"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
