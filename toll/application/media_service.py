from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from ..core.connection_manager import ConnectionManager
from ..core.feature_flags import FeatureFlags
from ..core.provider_selector import ProviderSelector
from ..core.registry import ProviderRegistry
from ..model.artifact import Artifact, ArtifactRepository, ArtifactStatus, ArtifactType
from ..model_registry.service import ModelRegistryService
from ..ports.media import MediaRequest, MediaResult
from ..ports.media_storage import MediaStorage

logger = logging.getLogger(__name__)


class MediaService:
    def __init__(
        self,
        cm: ConnectionManager,
        registry: ProviderRegistry,
        selector: ProviderSelector,
        flags: FeatureFlags,
        storage: MediaStorage | None = None,
        model_registry: ModelRegistryService | None = None,
        prompt_intelligence: Any = None,
    ):
        self.cm = cm
        self.registry = registry
        self.selector = selector
        self.flags = flags
        self.storage = storage
        self.model_registry = model_registry
        self.prompt_intelligence = prompt_intelligence

    def generate(self, params: dict) -> dict:
        media_type = params.get("media_type", "image")
        if media_type == "video" and not self.flags.is_enabled("media_video", default=False):
            return {"success": False, "error": "Video generation is disabled"}
        if not self.flags.is_enabled("media_generation", default=True):
            return {"success": False, "error": "Media generation is disabled"}

        prompt = params.get("prompt", "")
        if not prompt:
            return {"success": False, "error": "No prompt provided"}

        if self.prompt_intelligence and self.flags.is_enabled("prompt_intelligence", default=False):
            pkg = self.prompt_intelligence.resolve(
                prompt, media_type=media_type,
                model_id=params.get("provider_model_id") or params.get("provider"),
            )
            prompt = pkg.prompt
            params["prompt"] = prompt

        provider_name, resolved_model_id = self._resolve_provider(params, media_type)
        if not provider_name:
            return {"success": False, "error": "No media provider available"}

        media_port = self.registry.all_media().get(provider_name)
        if not media_port or not media_port.is_available():
            return {"success": False, "error": f"Media provider '{provider_name}' not available"}

        request = MediaRequest(
            prompt=prompt,
            media_type=media_type,
            provider_model_id=resolved_model_id or "",
            provider=provider_name,
            size=params.get("size"),
            seed=params.get("seed"),
            negative_prompt=params.get("negative_prompt"),
            duration=params.get("duration"),
            style=params.get("style"),
        )

        result = media_port.generate(request)
        if not result.success:
            return {"success": False, "error": result.error}

        media_path = self._persist(result)
        artifact = self._store_artifact(params, result, provider_name, prompt,
                                        resolved_model_id, media_path)

        return {
            "success": True,
            "artifact_id": artifact.id,
            "media_url": result.url or media_path,
            "media_path": media_path,
            "media_type": result.media_type,
            "content_type": result.content_type,
            "file_size_bytes": result.file_size_bytes,
        }

    def _resolve_provider(self, params: dict, media_type: str) -> tuple[str | None, str | None]:
        provider_model_id = params.get("provider_model_id")
        provider_name = params.get("provider")

        if provider_model_id and not provider_name:
            if self.model_registry:
                model = self.model_registry.get(provider_model_id)
                if model:
                    return model.provider, model.id
            return None, None

        if provider_name:
            return provider_name, provider_model_id

        if self.model_registry:
            best = self.model_registry.find_best(media_type=media_type)
            if best:
                return best.provider, best.id

        available = self.registry.available_media()
        if available:
            return available[0], None

        return None, None

    def _persist(self, result: MediaResult) -> str | None:
        if not self.storage:
            return result.url or None
        if not result.media_data:
            return result.url or None
        ext = self._ext_for_content_type(result.content_type)
        filename = f"{uuid.uuid4().hex}{ext}"
        return self.storage.save(result.media_type, result.media_data, filename)

    def _ext_for_content_type(self, content_type: str) -> str:
        mapping = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
        }
        return mapping.get(content_type, ".bin")

    def _store_artifact(
        self, params: dict, result: MediaResult, provider: str, prompt: str,
        resolved_model_id: str | None, media_path: str | None,
    ) -> Artifact:
        artifact_type = ArtifactType.IMAGE_GEN if result.media_type == "image" else ArtifactType.VIDEO
        now = __import__("datetime").datetime.utcnow().isoformat() + "Z"

        artifact = Artifact(
            id=params.get("id", str(uuid.uuid4())),
            type=artifact_type,
            title=params.get("title", f"Generated {result.media_type}"),
            status=ArtifactStatus.COMPLETED,
            version=1,
            model=resolved_model_id or result.provider_model_id,
            provider=provider,
            content={
                "media_url": result.url,
                "media_path": media_path,
                "prompt": prompt,
                "model": resolved_model_id or "",
                "provider": provider,
                "seed": result.seed,
                "file_size_bytes": result.file_size_bytes,
                "content_type": result.content_type,
                "duration_seconds": params.get("duration"),
            },
            workspace_type=params.get("workspace_type", "chat"),
            workspace_id=params.get("workspace_id", ""),
            tags=params.get("tags", [artifact_type.value]),
            intent=params.get("intent", "media_generate"),
            created_at=now,
            updated_at=now,
        )

        repo = ArtifactRepository(self.cm)
        return repo.create(artifact)
