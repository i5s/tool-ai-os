from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags


def _setup_cm(tmp_path):
    cm = ConnectionManager(db_path=tmp_path / "test.db")
    app.dependency_overrides[get_connection_manager] = lambda: cm
    flags = FeatureFlags(cm=cm)
    flags.enable("prompt_intelligence")
    return cm


def test_list_execution_profiles(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/prompt/execution-profiles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["profiles"]) == 6
    app.dependency_overrides.clear()
    cm.close()


def test_get_execution_profile(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/prompt/execution-profiles/marketing")
    assert resp.status_code == 200
    assert resp.json()["profile"]["name"] == "Marketing Profile"
    app.dependency_overrides.clear()
    cm.close()


def test_list_profiles_empty(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/prompt/profiles")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    app.dependency_overrides.clear()
    cm.close()


def test_create_profile(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.post("/api/prompt/profiles", json={
        "name": "Test Profile",
        "media_types": ["image"],
        "template": "Show {subject}",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["profile"]["name"] == "Test Profile"
    app.dependency_overrides.clear()
    cm.close()


def test_create_profile_no_name(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.post("/api/prompt/profiles", json={"name": ""})
    assert resp.status_code == 200
    assert resp.json()["success"] is False
    app.dependency_overrides.clear()
    cm.close()


def test_resolve_prompt(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.post("/api/prompt/resolve", json={
        "user_input": "اعلان حليب فاخر",
        "media_type": "image",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "prompt" in data
    assert len(data["prompt"]) > 0
    app.dependency_overrides.clear()
    cm.close()


def test_resolve_with_execution_profile(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.post("/api/prompt/resolve", json={
        "user_input": "new product",
        "media_type": "image",
        "execution_profile_id": "marketing",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["execution_profile_id"] == "marketing"
    app.dependency_overrides.clear()
    cm.close()


def test_resolve_disabled_flag(tmp_path):
    cm = ConnectionManager(db_path=tmp_path / "test.db")
    app.dependency_overrides[get_connection_manager] = lambda: cm
    client = TestClient(app)
    resp = client.post("/api/prompt/resolve", json={
        "user_input": "test",
        "media_type": "image",
    })
    assert resp.status_code == 403
    app.dependency_overrides.clear()
    cm.close()


def test_get_profile_not_found(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    resp = client.get("/api/prompt/profiles/nonexistent")
    assert resp.status_code == 404
    app.dependency_overrides.clear()
    cm.close()


def test_delete_profile(tmp_path):
    cm = _setup_cm(tmp_path)
    client = TestClient(app)
    client.post("/api/prompt/profiles", json={
        "id": "api:del", "name": "Delete me",
    })
    resp = client.delete("/api/prompt/profiles/api:del")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    app.dependency_overrides.clear()
    cm.close()
