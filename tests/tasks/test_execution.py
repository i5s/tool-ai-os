import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.tasks.models import TaskStatus
from toll.tasks.service import TaskService
from toll.agents.service import AgentService
from toll.agents.adapter_factory import AdapterFactory
from toll.shared_memory.service import SharedMemoryService


@pytest.fixture
def cm(tmp_path):
    db = tmp_path / "test.db"
    mgr = ConnectionManager(str(db))
    mgr.execute("PRAGMA journal_mode=WAL;")
    flags = FeatureFlags(cm=mgr)
    flags.enable("agent_runtime_bridge")
    flags.enable("agent_runtime")
    flags.enable("shared_memory")
    flags.enable("task_dispatcher")
    yield mgr
    mgr.close()


@pytest.fixture
def client(cm):
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_agents(cm):
    svc = AgentService(cm)
    return svc.list_agents(limit=10)


class TestAgentRuntimeBridge:
    def test_execute_task_success(self, client, cm, seeded_agents):
        hermes = next((a for a in seeded_agents if a.name == "Hermes"), None)
        assert hermes is not None

        task_resp = client.post("/api/tasks", json={
            "title": "Echo hello",
            "description": "Return the word hello",
            "created_by": "test",
        })
        assert task_resp.status_code == 200
        task_id = task_resp.json()["id"]

        assign_resp = client.post(f"/api/tasks/{task_id}/assign", json={
            "agent_id": hermes.id,
            "actor": "test",
        })
        assert assign_resp.status_code == 200

        exec_resp = client.post(f"/api/tasks/{task_id}/execute", json={})
        assert exec_resp.status_code == 200
        body = exec_resp.json()
        assert body["execution_result"]["status"] == "success"
        assert "hello" in body["execution_result"]["output"].lower() or "OK" in body["execution_result"]["output"]
        assert body["execution_result"]["duration_ms"] >= 0

    def test_execute_task_missing_agent(self, client, cm):
        task_resp = client.post("/api/tasks", json={
            "title": "Orphan task",
            "created_by": "test",
        })
        assert task_resp.status_code == 200
        task_id = task_resp.json()["id"]

        exec_resp = client.post(f"/api/tasks/{task_id}/execute", json={})
        assert exec_resp.status_code == 422

    def test_execute_task_wrong_status(self, client, cm, seeded_agents):
        hermes = next((a for a in seeded_agents if a.name == "Hermes"), None)
        assert hermes is not None

        task_resp = client.post("/api/tasks", json={
            "title": "Already completed",
            "created_by": "test",
        })
        assert task_resp.status_code == 200
        task_id = task_resp.json()["id"]

        client.post(f"/api/tasks/{task_id}/assign", json={"agent_id": hermes.id})
        client.post(f"/api/tasks/{task_id}/complete")

        exec_resp = client.post(f"/api/tasks/{task_id}/execute", json={})
        assert exec_resp.status_code == 422

    def test_execute_creates_memory_block(self, client, cm, seeded_agents):
        hermes = next((a for a in seeded_agents if a.name == "Hermes"), None)
        assert hermes is not None

        task_resp = client.post("/api/tasks", json={
            "title": "Memo task",
            "created_by": "test",
        })
        task_id = task_resp.json()["id"]
        client.post(f"/api/tasks/{task_id}/assign", json={"agent_id": hermes.id})
        exec_resp = client.post(f"/api/tasks/{task_id}/execute", json={})
        assert exec_resp.status_code == 200

        mem_resp = client.get("/api/memory?scope=project&scope_id=" + task_id)
        assert mem_resp.status_code == 200
        blocks = mem_resp.json()
        assert len(blocks) >= 1
        titles = [b["title"] for b in blocks]
        assert "Task completed: Memo task" in titles

    def test_execute_feature_flag_disabled(self, tmp_path):
        db = tmp_path / "disabled.db"
        cm = ConnectionManager(str(db))
        cm.execute("PRAGMA journal_mode=WAL;")
        FeatureFlags(cm=cm)

        app.dependency_overrides[get_connection_manager] = lambda: cm
        with TestClient(app) as c:
            task_resp = c.post("/api/tasks", json={"title": "Blocked"})
            assert task_resp.status_code == 404
        app.dependency_overrides.clear()
        cm.close()
