from __future__ import annotations

import json
import uuid

from ..core.feature_flags import FeatureFlags
from ..ports.model_registry import Model
from .repository import ModelRepository
from .seed import SEED_MODELS


class ModelRegistryService:
    def __init__(self, cm, flags: FeatureFlags | None = None):
        self.cm = cm
        self.flags = flags or FeatureFlags(cm=cm)
        self.repo = ModelRepository(cm)
        if self.flags.is_enabled("model_registry_seed"):
            self._seed()

    def _seed(self):
        existing = self.repo.list()
        if existing:
            return
        for data in SEED_MODELS:
            model = Model(**data)
            self.repo.create(model)

    def register(self, data: dict) -> Model:
        model_id = data.get("id") or f"{data['provider']}:{data['provider_model_id']}"
        existing = self.repo.get(model_id)
        if existing:
            raise ValueError(f"Model '{model_id}' already exists")
        model = Model(
            id=model_id,
            provider=data["provider"],
            provider_model_id=data["provider_model_id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version"),
            family=data.get("family"),
            media_types=data.get("media_types", ["image"]),
            capabilities=data.get("capabilities", {}),
            default_params=data.get("default_params", {}),
            status=data.get("status", "active"),
            cost_per_unit=data.get("cost_per_unit"),
            cost_unit=data.get("cost_unit"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
        return self.repo.create(model)

    def get(self, model_id: str) -> Model | None:
        return self.repo.get(model_id)

    def get_by_provider(self, provider: str, provider_model_id: str) -> Model | None:
        return self.repo.get_by_provider(provider, provider_model_id)

    def list(self, provider: str | None = None, media_type: str | None = None,
             status: str | None = None, family: str | None = None,
             tag: str | None = None) -> list[Model]:
        return self.repo.list(provider, media_type, status, family, tag)

    def update(self, model_id: str, data: dict) -> Model | None:
        return self.repo.update(model_id, data)

    def disable(self, model_id: str) -> bool:
        return self.repo.disable(model_id)

    def find_best(self, media_type: str, prefer_speed: bool = False,
                  prefer_quality: bool = False, prefer_cost: bool = False) -> Model | None:
        models = self.repo.list(media_type=media_type, status="active")
        if not models:
            return None
        return models[0]

    def list_providers(self) -> list[str]:
        return self.repo.list_providers()

    def register_handler(self, plan: dict, metadata: dict | None = None) -> dict:
        return {"model": self.register(plan)}

    def list_handler(self, plan: dict, metadata: dict | None = None) -> dict:
        models = self.repo.list(
            provider=plan.get("provider"),
            media_type=plan.get("media_type"),
            status=plan.get("status"),
            family=plan.get("family"),
            tag=plan.get("tag"),
        )
        return {
            "models": [m.__dict__ for m in models],
            "total": len(models),
        }
