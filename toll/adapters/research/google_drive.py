from __future__ import annotations

import json
import logging
from pathlib import Path

from ...core.config import DATA
from ...core.feature_flags import FeatureFlags
from ...model.artifact import Artifact

logger = logging.getLogger(__name__)


class GoogleDriveAdapter:
    name = "google_drive"

    def __init__(self, flags: FeatureFlags):
        self.flags = flags

    def backup_artifact(self, artifact: Artifact) -> str | None:
        if not self.flags.is_enabled("google_drive_backup"):
            logger.info("google_drive_backup feature flag is disabled")
            return None

        artifact_dir = DATA / "artifacts" / artifact.id
        if not artifact_dir.exists():
            logger.warning(
                "Artifact directory not found: %s", artifact_dir
            )
            return None

        backup_dir = DATA / "drive_backup" / artifact.id
        backup_dir.mkdir(parents=True, exist_ok=True)

        for fname in ["index.html", "preview.html", "preview.json"]:
            src = artifact_dir / fname
            if src.exists():
                dst = backup_dir / fname
                dst.write_bytes(src.read_bytes())
                logger.info("Backed up %s to %s", fname, dst)

        meta_path = backup_dir / "metadata.json"
        meta_path.write_text(
            json.dumps(
                {
                    "id": artifact.id,
                    "type": artifact.type.value,
                    "title": artifact.title,
                    "version": artifact.version,
                    "provider": artifact.provider,
                    "intent": artifact.intent,
                    "workspace_type": artifact.workspace_type,
                    "workspace_id": artifact.workspace_id,
                    "tags": artifact.tags,
                    "created_at": artifact.created_at,
                    "updated_at": artifact.updated_at,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        logger.info(
            "Artifact %s backed up to %s", artifact.id, backup_dir
        )
        return str(backup_dir)

    def is_available(self) -> bool:
        return True
