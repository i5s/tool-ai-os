import pytest
from toll.model.artifact import (
    Artifact, ArtifactRepository, ArtifactType, ArtifactStatus,
)


def test_artifact_defaults():
    art = Artifact(id="a1", type=ArtifactType.REPORT, status=ArtifactStatus.DRAFT, title="Test")
    assert art.version == 1
    assert art.parent_artifact_id is None
    assert art.tags == []
    assert art.metadata == {}


def test_artifact_types():
    assert ArtifactType.CAROUSEL.value == "carousel"
    assert ArtifactType.REPORT.value == "report"
    assert ArtifactType.PRESENTATION.value == "presentation"


def test_artifact_statuses():
    assert ArtifactStatus.DRAFT.value == "draft"
    assert ArtifactStatus.COMPLETED.value == "completed"
    assert ArtifactStatus.FAILED.value == "failed"
    assert ArtifactStatus.ARCHIVED.value == "archived"
    assert ArtifactStatus.DELETED.value == "deleted"


def test_create_and_get(cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.DRAFT, title="My Report"))
    assert art.id != ""
    assert art.created_at != ""

    fetched = repo.get(art.id)
    assert fetched is not None
    assert fetched.title == "My Report"
    assert fetched.type == ArtifactType.REPORT


def test_list_by_type(cm):
    repo = ArtifactRepository(cm)
    repo.create(Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.DRAFT, title="R1"))
    repo.create(Artifact(id="", type=ArtifactType.CAROUSEL, status=ArtifactStatus.DRAFT, title="C1"))
    repo.create(Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="R2"))

    reports = repo.list(type=ArtifactType.REPORT)
    assert len(reports) == 2

    completed = repo.list(status=ArtifactStatus.COMPLETED)
    assert len(completed) == 1
    assert completed[0].title == "R2"


def test_update(cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(id="", type=ArtifactType.CODE, status=ArtifactStatus.DRAFT, title="Code"))
    art.status = ArtifactStatus.COMPLETED
    art.rendered_path = "/path/to/file"
    repo.update(art)

    fetched = repo.get(art.id)
    assert fetched.status == ArtifactStatus.COMPLETED
    assert fetched.rendered_path == "/path/to/file"


def test_delete_soft(cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(id="", type=ArtifactType.GENERIC, status=ArtifactStatus.DRAFT, title="Temp"))
    assert repo.delete(art.id) is True
    fetched = repo.get(art.id)
    assert fetched.status == ArtifactStatus.DELETED


def test_delete_not_found(cm):
    repo = ArtifactRepository(cm)
    assert repo.delete("nonexistent") is False


def test_next_version(cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="V1"))
    child = repo.next_version(art.id)
    assert child is not None
    assert child.version == 2
    assert child.parent_artifact_id == art.id
    assert child.type == ArtifactType.REPORT


def test_metadata_roundtrip(cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(
        id="", type=ArtifactType.REPORT, status=ArtifactStatus.DRAFT, title="Meta",
        provider="opencode", model="qwen2.5", intent="report",
        workspace_type="brand", workspace_id="b1",
        tags=["arabic", "academic"],
        metadata={"tokens": 500},
    ))
    fetched = repo.get(art.id)
    assert fetched.provider == "opencode"
    assert fetched.model == "qwen2.5"
    assert fetched.intent == "report"
    assert fetched.workspace_type == "brand"
    assert fetched.workspace_id == "b1"
    assert fetched.tags == ["arabic", "academic"]
    assert fetched.metadata == {"tokens": 500}
