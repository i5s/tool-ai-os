from __future__ import annotations

import logging

from ..model.artifact import Artifact
from .artifact_service import ArtifactService

logger = logging.getLogger(__name__)


class OpenDesignService:
    def __init__(self, artifact_service: ArtifactService):
        self.artifact_service = artifact_service

    def push(self, artifact_id: str) -> dict:
        artifact = self.artifact_service.get(artifact_id)
        if not artifact:
            return {"error": "Artifact not found"}

        preview_url = self._open_design_push(artifact)
        if preview_url:
            artifact.preview_url = preview_url
            self.artifact_service.update(artifact)
            return {"preview_url": preview_url}

        return {"error": "OpenDesign push failed"}

    def push_from_workflow(self, plan: dict, metadata: dict | None = None) -> dict:
        artifact_id = plan.get("artifact_id")
        if not artifact_id:
            return {"error": "No artifact_id in plan"}
        return self.push(artifact_id)

    def _open_design_push(self, artifact: Artifact) -> str | None:
        try:
            import subprocess
            result = subprocess.run(
                ["opendesign", "create", artifact.id, "--file", artifact.rendered_path or ""],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            logger.warning("OpenDesign push failed: %s", result.stderr)
            return None
        except FileNotFoundError:
            logger.info("OpenDesign CLI not installed; skipping push")
            return None
        except Exception as e:
            logger.warning("OpenDesign push error: %s", e)
            return None
