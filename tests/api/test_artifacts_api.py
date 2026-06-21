import pytest
from fastapi.testclient import TestClient
from api.main import app
from toll.core.connection_manager import ConnectionManager
from toll.core.storage import Storage
from toll.core.feature_flags import FeatureFlags
from toll.model.artifact import Artifact, ArtifactType, ArtifactStatus, ArtifactRepository


@pytest.fixture
def client(cm):
    app.dependency_overrides = {}
    app.state.cm = cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def test_list_artifacts_empty(client):
    resp = client.get("/api/artifacts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["artifacts"] == []


def test_create_and_list_artifacts(client, cm, tmp_path):
    import toll.core.config as cfg
    cfg.ARTIFACTS_PATH = tmp_path / "artifacts"
    svc = type("Fake", (object,), {})
    svc.cm = cm
    svc.settings = None
    svc.registries = {}

    app.state.cm = cm

    repo = ArtifactRepository(cm)
    repo.create(Artifact(id="a1", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="Test Report"))
    repo.create(Artifact(id="a2", type=ArtifactType.CAROUSEL, status=ArtifactStatus.DRAFT, title="Test Carousel"))

    resp = client.get("/api/artifacts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["artifacts"]) == 2


def test_get_artifact_not_found(client):
    resp = client.get("/api/artifacts/nonexistent")
    assert resp.status_code == 404


def test_get_artifact_found(client, cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(id="", type=ArtifactType.REPORT, status=ArtifactStatus.COMPLETED, title="Found Me",
                                content={"sections": []}))
    app.state.cm = cm

    resp = client.get(f"/api/artifacts/{art.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Found Me"


def test_delete_artifact(client, cm):
    repo = ArtifactRepository(cm)
    art = repo.create(Artifact(id="", type=ArtifactType.GENERIC, status=ArtifactStatus.DRAFT, title="Delete Me"))
    app.state.cm = cm

    resp = client.delete(f"/api/artifacts/{art.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "deleted"
