from __future__ import annotations

import logging

from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from .execution_profile import ExecutionProfile, ExecutionProfileRepository
from .profiles import seed_profiles
from .repository import PromptProfile, PromptProfileRepository

logger = logging.getLogger(__name__)


class PromptProfileService:
    def __init__(self, cm: ConnectionManager, flags: FeatureFlags):
        self.cm = cm
        self.flags = flags
        self.repo = PromptProfileRepository(cm)

    def ensure_seeded(self):
        if self.flags.is_enabled("prompt_intelligence_seed", default=True):
            seed_profiles(self.repo)

    def create(self, params: dict) -> dict:
        name = params.get("name", "")
        if not name:
            return {"success": False, "error": "Profile name required"}
        profile = PromptProfile(
            id=params.get("id", ""),
            name=name,
            media_types=params.get("media_types", ["image"]),
            template=params.get("template", ""),
            default_params=params.get("default_params", {}),
            compatible_models=params.get("compatible_models", []),
            weight_criteria=params.get("weight_criteria", {}),
            tags=params.get("tags", []),
        )
        created = self.repo.create(profile)
        return {"success": True, "profile": self._to_dict(created)}

    def get(self, profile_id: str) -> dict:
        profile = self.repo.get(profile_id)
        if not profile:
            return {"success": False, "error": "Profile not found"}
        return {"success": True, "profile": self._to_dict(profile)}

    def list(self, media_type: str | None = None, tag: str | None = None) -> dict:
        profiles = self.repo.list(media_type=media_type, tag=tag)
        return {
            "success": True,
            "total": len(profiles),
            "profiles": [self._to_dict(p) for p in profiles],
        }

    def update(self, profile_id: str, params: dict) -> dict:
        allowed = {"name", "media_types", "template", "default_params",
                    "compatible_models", "weight_criteria", "tags", "enabled"}
        updates = {k: v for k, v in params.items() if k in allowed}
        profile = self.repo.update(profile_id, updates)
        if not profile:
            return {"success": False, "error": "Profile not found"}
        return {"success": True, "profile": self._to_dict(profile)}

    def delete(self, profile_id: str) -> dict:
        if not self.repo.delete(profile_id):
            return {"success": False, "error": "Profile not found"}
        return {"success": True}

    def get_version_history(self, profile_id: str) -> dict:
        versions = self.repo.get_version_history(profile_id)
        return {"success": True, "versions": versions}

    @staticmethod
    def _to_dict(p: PromptProfile) -> dict:
        return {
            "id": p.id,
            "name": p.name,
            "media_types": p.media_types,
            "template": p.template,
            "default_params": p.default_params,
            "compatible_models": p.compatible_models,
            "weight_criteria": p.weight_criteria,
            "tags": p.tags,
            "version": p.version,
            "enabled": p.enabled,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }


class ExecutionProfileService:
    def __init__(self):
        self.repo = ExecutionProfileRepository()

    def list(self) -> dict:
        return {
            "success": True,
            "profiles": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "sub_profiles": p.sub_profiles,
                    "default_media_type": p.default_media_type,
                    "icon": p.icon,
                    "tags": p.tags,
                }
                for p in self.repo.list()
            ],
        }

    def get(self, profile_id: str) -> dict:
        p = self.repo.get(profile_id)
        if not p:
            return {"success": False, "error": "Execution profile not found"}
        return {
            "success": True,
            "profile": {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "sub_profiles": p.sub_profiles,
                "default_media_type": p.default_media_type,
                "icon": p.icon,
                "tags": p.tags,
            },
        }
