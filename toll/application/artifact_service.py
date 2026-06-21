from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..core.config import ARTIFACTS_PATH, ARCHIVE_PATH
from ..core.connection_manager import ConnectionManager
from ..model.artifact import Artifact, ArtifactRepository, ArtifactStatus, ArtifactType


class ArtifactService:
    def __init__(self, cm: ConnectionManager):
        self.repo = ArtifactRepository(cm)

    def create(self, artifact: Artifact, rendered_html: str | None = None) -> Artifact:
        artifact = self.repo.create(artifact)
        if rendered_html:
            self._write_files(artifact, rendered_html)
        return artifact

    def update(self, artifact: Artifact, rendered_html: str | None = None) -> Artifact:
        artifact = self.repo.update(artifact)
        if rendered_html:
            self._write_files(artifact, rendered_html)
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        return self.repo.get(artifact_id)

    def list(
        self,
        type: ArtifactType | None = None,
        status: ArtifactStatus | None = None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[Artifact]:
        return self.repo.list(type, status, workflow_id, limit)

    def delete(self, artifact_id: str) -> bool:
        return self.repo.delete(artifact_id)

    def get_rendered_path(self, artifact_id: str) -> Path | None:
        art = self.repo.get(artifact_id)
        if not art or not art.rendered_path:
            return None
        p = Path(art.rendered_path)
        if p.exists():
            return p
        return None

    def get_preview_html(self, artifact_id: str) -> str | None:
        art = self.repo.get(artifact_id)
        if not art:
            return None
        preview_path = ARTIFACTS_PATH / art.id / "preview.html"
        if preview_path.exists():
            return preview_path.read_text(encoding="utf-8")
        return None

    def get_preview_json(self, artifact_id: str) -> dict | None:
        art = self.repo.get(artifact_id)
        if not art:
            return None
        preview_path = ARTIFACTS_PATH / art.id / "preview.json"
        if preview_path.exists():
            return json.loads(preview_path.read_text(encoding="utf-8"))
        return None

    def _write_files(self, artifact: Artifact, rendered_html: str):
        artifact_dir = ARTIFACTS_PATH / artifact.id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        index_path = artifact_dir / "index.html"
        index_path.write_text(rendered_html, encoding="utf-8")
        artifact.rendered_path = str(index_path)

        content_path = artifact_dir / "content.json"
        content_path.write_text(
            json.dumps(artifact.content, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        metadata_path = artifact_dir / "metadata.json"
        metadata_path.write_text(
            json.dumps(self._metadata_dict(artifact), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        self.repo.update(artifact)

    def write_preview(self, artifact: Artifact, preview_html: str, preview_json: dict):
        artifact_dir = ARTIFACTS_PATH / artifact.id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        html_path = artifact_dir / "preview.html"
        html_path.write_text(preview_html, encoding="utf-8")

        json_path = artifact_dir / "preview.json"
        json_path.write_text(
            json.dumps(preview_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        artifact.preview_url = f"/data/artifacts/{artifact.id}/preview.html"
        self.repo.update(artifact)

    def _metadata_dict(self, artifact: Artifact) -> dict:
        return {
            "id": artifact.id,
            "type": artifact.type.value,
            "status": artifact.status.value,
            "title": artifact.title,
            "version": artifact.version,
            "parent_artifact_id": artifact.parent_artifact_id,
            "workflow_id": artifact.workflow_id,
            "provider": artifact.provider,
            "model": artifact.model,
            "intent": artifact.intent,
            "workspace_type": artifact.workspace_type,
            "workspace_id": artifact.workspace_id,
            "tags": artifact.tags,
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "expires_at": artifact.expires_at,
        }

    def archive(self, artifact: Artifact):
        import tarfile

        artifact_dir = ARTIFACTS_PATH / artifact.id
        if not artifact_dir.exists():
            return

        ARCHIVE_PATH.mkdir(parents=True, exist_ok=True)
        archive_path = ARCHIVE_PATH / f"{artifact.id}.tar.gz"
        with tarfile.open(str(archive_path), "w:gz") as tar:
            tar.add(str(artifact_dir), arcname=artifact.id)

        import shutil
        shutil.rmtree(str(artifact_dir))

        artifact.status = ArtifactStatus.ARCHIVED
        artifact.rendered_path = None
        artifact.preview_url = None
        self.repo.update(artifact)
