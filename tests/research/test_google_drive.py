import json
from pathlib import Path
from unittest.mock import patch

from toll.adapters.research import google_drive as gd_module
from toll.adapters.research.google_drive import GoogleDriveAdapter
from toll.model.artifact import Artifact, ArtifactType, ArtifactStatus
from toll.core.feature_flags import FeatureFlags


def test_backup_disabled_feature_flag(cm, tmp_path):
    flags = FeatureFlags(cm=cm)
    adapter = GoogleDriveAdapter(flags)
    art = Artifact(
        id="test_001",
        type=ArtifactType.RESEARCH,
        status=ArtifactStatus.DRAFT,
        title="Test Backup",
    )
    result = adapter.backup_artifact(art)
    assert result is None


def test_backup_missing_artifact_dir(cm, tmp_path):
    flags = FeatureFlags(cm=cm)
    flags.enable("google_drive_backup")
    adapter = GoogleDriveAdapter(flags)
    art = Artifact(
        id="nonexistent",
        type=ArtifactType.RESEARCH,
        status=ArtifactStatus.DRAFT,
        title="Missing",
    )
    result = adapter.backup_artifact(art)
    assert result is None


def test_backup_creates_files(cm, tmp_path):
    artifact_dir = tmp_path / "artifacts" / "backup_test"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "index.html").write_text("<html>test</html>")
    (artifact_dir / "preview.html").write_text("<html>preview</html>")

    flags = FeatureFlags(cm=cm)
    flags.enable("google_drive_backup")
    adapter = GoogleDriveAdapter(flags)

    with patch.object(gd_module, "DATA", tmp_path):
        art = Artifact(
            id="backup_test",
            type=ArtifactType.RESEARCH,
            status=ArtifactStatus.DRAFT,
            title="Backup Test",
            version="1.0.0",
            provider="test",
            intent="research",
            workspace_type="semester",
            workspace_id="ws_001",
            tags=["test"],
            created_at="2026-06-21",
            updated_at="2026-06-21",
        )
        result = adapter.backup_artifact(art)
    assert result is not None
    backup_path = Path(result)
    assert (backup_path / "index.html").exists()
    assert (backup_path / "preview.html").exists()
    assert (backup_path / "metadata.json").exists()
    meta = json.loads((backup_path / "metadata.json").read_text())
    assert meta["id"] == "backup_test"
    assert meta["title"] == "Backup Test"
