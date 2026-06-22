import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.shared_memory.service import SharedMemoryService
from toll.shared_memory.models import MemoryBlockType, MemoryScope


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "toll_shared_memory_test.db"


@pytest.fixture
def cm(temp_db_path):
    mgr = ConnectionManager(db_path=temp_db_path)
    yield mgr
    mgr.close()


@pytest.fixture
def service(cm):
    return SharedMemoryService(cm=cm)


@pytest.fixture
def client(cm):
    flags = FeatureFlags(cm=cm)
    flags.enable("shared_memory")
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def _seed_block(service: SharedMemoryService) -> dict:
    block = service.create_memory(
        type=MemoryBlockType.FACT.value,
        scope=MemoryScope.GLOBAL.value,
        title="Seed fact",
        content="hello",
        created_by="system",
    )
    return {"id": block.id, "title": block.title}


class TestSharedMemoryCRUD:
    def test_create_block(self, client, service):
        payload = {
            "type": MemoryBlockType.FACT.value,
            "scope": MemoryScope.GLOBAL.value,
            "title": "Test fact",
            "content": "content",
        }
        resp = client.post("/api/memory", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test fact"
        assert data["type"] == MemoryBlockType.FACT.value
        assert "id" in data

    def test_get_block(self, client, service):
        info = _seed_block(service)
        resp = client.get(f"/api/memory/{info['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == info["id"]

    def test_get_missing_returns_404(self, client):
        resp = client.get("/api/memory/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_list_blocks(self, client, service):
        _seed_block(service)
        _seed_block(service)
        resp = client.get("/api/memory")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_update_block(self, client, service):
        info = _seed_block(service)
        resp = client.put(f"/api/memory/{info['id']}", json={"title": "Updated"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    def test_delete_block(self, client, service):
        info = _seed_block(service)
        resp = client.delete(f"/api/memory/{info['id']}")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_delete_missing_returns_404(self, client):
        resp = client.delete("/api/memory/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestSharedMemorySearch:
    def test_search_returns_matches(self, client, service):
        service.create_memory(
            type=MemoryBlockType.FACT.value,
            scope=MemoryScope.GLOBAL.value,
            title="Python tip",
            content="use list comprehensions",
        )
        service.create_memory(
            type=MemoryBlockType.FACT.value,
            scope=MemoryScope.GLOBAL.value,
            title="Rust tip",
            content="ownership rules",
        )
        resp = client.post("/api/memory/search?q=python")
        assert resp.status_code == 200
        titles = [b["title"] for b in resp.json()]
        assert "Python tip" in titles
        assert "Rust tip" not in titles

    def test_search_empty_returns_empty(self, client, service):
        resp = client.post("/api/memory/search?q=zzzzzzz")
        assert resp.status_code == 200
        assert resp.json() == []


class TestSharedMemoryScopeFilter:
    def test_scope_filter(self, client, service):
        service.create_memory(
            type=MemoryBlockType.FACT.value,
            scope=MemoryScope.PROJECT.value,
            title="Project fact",
            scope_id="proj-1",
        )
        service.create_memory(
            type=MemoryBlockType.FACT.value,
            scope=MemoryScope.GLOBAL.value,
            title="Global fact",
        )
        resp = client.get("/api/memory?scope=project")
        assert resp.status_code == 200
        titles = [b["title"] for b in resp.json()]
        assert "Project fact" in titles
        assert "Global fact" not in titles


class TestFeatureFlag:
    def test_disabled_returns_404(self, cm):
        flags = FeatureFlags(cm=cm)
        flags.disable("shared_memory")
        app.dependency_overrides[get_connection_manager] = lambda: cm
        try:
            with TestClient(app) as c:
                resp = c.get("/api/memory")
                assert resp.status_code == 404
                assert "disabled" in resp.json()["detail"]
        finally:
            app.dependency_overrides = {}

    def test_enabled_allows_access(self, cm):
        flags = FeatureFlags(cm=cm)
        flags.enable("shared_memory")
        app.dependency_overrides[get_connection_manager] = lambda: cm
        try:
            with TestClient(app) as c:
                resp = c.get("/api/memory")
                assert resp.status_code == 200
        finally:
            app.dependency_overrides = {}
