from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags


def _setup_cm(tmp_path):
    cm = ConnectionManager(db_path=tmp_path / "test.db")
    app.dependency_overrides[get_connection_manager] = lambda: cm
    flags = FeatureFlags(cm=cm)
    flags.enable("benchmark_lab")
    return cm


def test_list_suites_empty(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/benchmark/suites")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["suites"] == []
    app.dependency_overrides.clear()
    cm.close()


def test_create_suite(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.post("/api/benchmark/suites", json={
        "name": "Test Suite",
        "prompts": ["a cat", "a dog"],
        "media_type": "image",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["prompts"] == 2
    app.dependency_overrides.clear()
    cm.close()


def test_get_suite_not_found(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/benchmark/suites/nonexistent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    app.dependency_overrides.clear()
    cm.close()


def test_list_runs_empty(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/benchmark/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["runs"] == []
    app.dependency_overrides.clear()
    cm.close()


def test_model_scores(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/benchmark/models/r:test/scores")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["run_count"] == 0
    app.dependency_overrides.clear()
    cm.close()
