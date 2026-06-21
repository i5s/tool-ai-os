from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager


def _setup_cm(tmp_path):
    cm = ConnectionManager(db_path=tmp_path / "test.db")
    app.dependency_overrides[get_connection_manager] = lambda: cm
    return cm


def test_list_models_empty(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "total" in data
    app.dependency_overrides.clear()
    cm.close()


def test_register_and_get_model(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.post("/api/models", json={
        "provider": "replicate",
        "provider_model_id": "test-model",
        "name": "Test Model",
    })
    assert resp.status_code == 200
    model_id = resp.json()["id"]
    resp = client.get(f"/api/models/{model_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Model"
    app.dependency_overrides.clear()
    cm.close()


def test_list_providers(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    client.post("/api/models", json={
        "provider": "replicate",
        "provider_model_id": "a",
        "name": "A",
    })
    client.post("/api/models", json={
        "provider": "openai",
        "provider_model_id": "b",
        "name": "B",
    })
    resp = client.get("/api/models/providers")
    assert resp.status_code == 200
    providers = resp.json()["providers"]
    assert "replicate" in providers
    assert "openai" in providers
    app.dependency_overrides.clear()
    cm.close()


def test_disable_model(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.post("/api/models", json={
        "provider": "replicate",
        "provider_model_id": "del",
        "name": "Delete Me",
    })
    model_id = resp.json()["id"]
    resp = client.delete(f"/api/models/{model_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "disabled"
    app.dependency_overrides.clear()
    cm.close()


def test_get_model_not_found(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/models/nonexistent")
    assert resp.status_code == 404
    app.dependency_overrides.clear()
    cm.close()
