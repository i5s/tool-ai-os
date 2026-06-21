import pytest
from pathlib import Path
from toll.application.artifact_service import ArtifactService
from toll.model.artifact import Artifact, ArtifactType, ArtifactStatus


def test_create_and_get(cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"
    cfg.ARCHIVE_PATH = cfg.ARTIFACTS_PATH / "archive"

    svc = ArtifactService(cm)
    art = Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.DRAFT, title="Test Report")
    art = svc.create(art, "<html><body><h1>Test</h1></body></html>")
    assert art.id != ""
    assert art.rendered_path is not None

    fetched = svc.get(art.id)
    assert fetched.title == "Test Report"
    assert fetched.type == ArtifactType.REPORT


def test_list_artifacts(cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"

    svc = ArtifactService(cm)
    svc.create(Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="R1"))
    svc.create(Artifact(id="", type=ArtifactType.CAROUSEL, status=ArtifactStatus.DRAFT, title="C1"))

    all_arts = svc.list()
    assert len(all_arts) == 2

    reports = svc.list(type=ArtifactType.REPORT)
    assert len(reports) == 1
    assert reports[0].title == "R1"


def test_delete(cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"

    svc = ArtifactService(cm)
    art = svc.create(Artifact(id="", type=ArtifactType.GENERIC, status=ArtifactStatus.DRAFT, title="Temp"))
    assert svc.delete(art.id) is True
    fetched = svc.get(art.id)
    assert fetched.status == ArtifactStatus.DELETED


def test_render_html_persisted(cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"

    svc = ArtifactService(cm)
    art = svc.create(
        Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.DRAFT, title="Rendered"),
        "<html>Hello</html>",
    )
    path = svc.get_rendered_path(art.id)
    assert path is not None
    assert path.read_text(encoding="utf-8") == "<html>Hello</html>"


def test_preview_html_and_json(cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"

    svc = ArtifactService(cm)
    art = Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.DRAFT, title="Preview Test",
                   content={"sections": [{"heading": "Intro", "body": "Hello"}]})
    art = svc.create(art, "<html>Full</html>")
    svc.write_preview(art, "<html>Preview</html>", {"id": art.id, "title": "Preview Test"})

    html = svc.get_preview_html(art.id)
    assert html == "<html>Preview</html>"

    data = svc.get_preview_json(art.id)
    assert data["id"] == art.id
    assert data["title"] == "Preview Test"


def test_archive_artifact(cm, tmp_path):
    import toll.core.config as cfg
    from unittest.mock import patch

    test_artifacts = tmp_path / "artifacts"
    test_archive = test_artifacts / "archive"

    with patch("toll.application.artifact_service.ARTIFACTS_PATH", test_artifacts):
        with patch("toll.application.artifact_service.ARCHIVE_PATH", test_archive):
            svc = ArtifactService(cm)
            art = Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="Archivable")
            art = svc.create(art, "<html>Data</html>")

            svc.archive(art)
            archived = svc.get(art.id)
            assert archived.status == ArtifactStatus.ARCHIVED
            assert archived.rendered_path is None

            archive_file = test_archive / f"{art.id}.tar.gz"
            assert archive_file.exists()
