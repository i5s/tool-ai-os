import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.feature_flags import FeatureFlags


def _enable_notebooks(cm):
    cm.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        ("feature_notebooklm_enabled", "true"),
    )
    cm.commit()


def _disable_notebooks(cm):
    cm.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        ("feature_notebooklm_enabled", "false"),
    )
    cm.commit()


@pytest.fixture
def client(cm):
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def test_create_notebook(client, cm):
    _enable_notebooks(cm)
    resp = client.post("/api/notebooks", json={"title": "دفتر API"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "دفتر API"
    assert "id" in data


def test_list_notebooks_empty(client, cm):
    _enable_notebooks(cm)
    resp = client.get("/api/notebooks")
    assert resp.status_code == 200
    assert resp.json()["notebooks"] == []


def test_list_notebooks_after_create(client, cm):
    _enable_notebooks(cm)
    client.post("/api/notebooks", json={"title": "دفتر 1"})
    client.post("/api/notebooks", json={"title": "دفتر 2"})
    resp = client.get("/api/notebooks")
    assert len(resp.json()["notebooks"]) == 2


def test_get_notebook(client, cm):
    _enable_notebooks(cm)
    created = client.post("/api/notebooks", json={"title": "دفتر وحيد"}).json()
    resp = client.get(f"/api/notebooks/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "دفتر وحيد"


def test_get_notebook_404(client, cm):
    _enable_notebooks(cm)
    resp = client.get("/api/notebooks/غير_موجود")
    assert resp.status_code == 404


def test_update_notebook(client, cm):
    _enable_notebooks(cm)
    created = client.post("/api/notebooks", json={"title": "قبل"}).json()
    resp = client.put(f"/api/notebooks/{created['id']}", json={"title": "بعد"})
    assert resp.status_code == 200
    assert resp.json()["notebook"]["title"] == "بعد"


def test_delete_notebook(client, cm):
    _enable_notebooks(cm)
    created = client.post("/api/notebooks", json={"title": "سيتم حذفه"}).json()
    resp = client.delete(f"/api/notebooks/{created['id']}")
    assert resp.status_code == 200
    get_resp = client.get(f"/api/notebooks/{created['id']}")
    assert get_resp.status_code == 404


def test_upload_source(client, cm):
    _enable_notebooks(cm)
    nb = client.post("/api/notebooks", json={"title": "مصدر اختبار"}).json()
    resp = client.post(
        f"/api/notebooks/{nb['id']}/sources",
        json={"content": "محتوى المصدر", "file_name": "test.txt"},
    )
    assert resp.status_code == 200
    assert resp.json()["file_name"] == "test.txt"


def test_list_sources_404_for_missing_notebook(client, cm):
    _enable_notebooks(cm)
    resp = client.get("/api/notebooks/غير_موجود/sources")
    assert resp.status_code == 404


def test_delete_source_404(client, cm):
    _enable_notebooks(cm)
    nb = client.post("/api/notebooks", json={"title": "حذف"}).json()
    resp = client.delete(f"/api/notebooks/{nb['id']}/sources/غير_موجود")
    assert resp.status_code == 404


def test_list_notes_404_for_missing_notebook(client, cm):
    _enable_notebooks(cm)
    resp = client.get("/api/notebooks/غير_موجود/notes")
    assert resp.status_code == 404


def test_delete_note_404(client, cm):
    _enable_notebooks(cm)
    nb = client.post("/api/notebooks", json={"title": "حذف ملاحظة"}).json()
    resp = client.delete(f"/api/notebooks/{nb['id']}/notes/غير_موجود")
    assert resp.status_code == 404


def test_create_snapshot(client, cm):
    _enable_notebooks(cm)
    nb = client.post("/api/notebooks", json={"title": "لقطة اختبار"}).json()
    resp = client.post(f"/api/notebooks/{nb['id']}/snapshots", json={"label": "لقطة 1"})
    assert resp.status_code == 200
    assert resp.json()["label"] == "لقطة 1"


def test_list_snapshots_404_for_missing_notebook(client, cm):
    _enable_notebooks(cm)
    resp = client.get("/api/notebooks/غير_موجود/snapshots")
    assert resp.status_code == 404


def test_delete_snapshot_404(client, cm):
    _enable_notebooks(cm)
    nb = client.post("/api/notebooks", json={"title": "حذف لقطة"}).json()
    resp = client.delete(f"/api/notebooks/{nb['id']}/snapshots/غير_موجود")
    assert resp.status_code == 404


def test_disabled_notebook_returns_403(client, cm):
    _disable_notebooks(cm)
    resp = client.post("/api/notebooks", json={"title": "محظور"})
    assert resp.status_code == 403


def test_query_requires_question(client, cm):
    _enable_notebooks(cm)
    nb = client.post("/api/notebooks", json={"title": "استعلام"}).json()
    resp = client.post(
        f"/api/notebooks/{nb['id']}/query",
        json={"question": "   "},
    )
    assert resp.status_code == 400
