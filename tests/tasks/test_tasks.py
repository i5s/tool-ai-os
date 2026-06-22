import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.tasks.service import TaskService
from toll.tasks.models import TaskStatus, TaskPriority, TaskEventType
from toll.agents.service import AgentService
from toll.agents.models import AgentRole, AgentRank


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "toll_tasks_test.db"


@pytest.fixture
def cm(temp_db_path):
    mgr = ConnectionManager(db_path=temp_db_path)
    yield mgr
    mgr.close()


@pytest.fixture
def task_service(cm):
    return TaskService(cm=cm)


@pytest.fixture
def agent_service(cm):
    return AgentService(cm=cm)


@pytest.fixture
def task_client(cm):
    flags = FeatureFlags(cm=cm)
    flags.enable("task_dispatcher")
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def _seed_agent(agent_service: AgentService) -> dict:
    agent = agent_service.create_agent(
        name="Task Agent",
        role=AgentRole.DEVELOPER.value,
        rank=AgentRank.WORKER.value,
    )
    return {"id": agent.id, "name": agent.name}


class TestTaskCRUD:
    def test_create_task(self, task_client, task_service, agent_service):
        _seed_agent(agent_service)
        resp = task_client.post("/api/tasks", json={"title": "Build", "priority": TaskPriority.HIGH.value})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Build"
        assert data["status"] == TaskStatus.DRAFT.value
        assert "id" in data

    def test_get_task(self, task_client, task_service):
        task = task_service.create_task(title="Task X")
        resp = task_client.get(f"/api/tasks/{task.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == task.id

    def test_get_missing_task_returns_404(self, task_client):
        resp = task_client.get("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_list_tasks(self, task_client, task_service):
        task_service.create_task(title="T1")
        task_service.create_task(title="T2")
        resp = task_client.get("/api/tasks")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_delete_task(self, task_client, task_service):
        task = task_service.create_task(title="T1")
        resp = task_client.delete(f"/api/tasks/{task.id}")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_delete_missing_returns_404(self, task_client):
        resp = task_client.delete("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestTaskLifecycle:
    def test_assign_task(self, task_client, task_service, agent_service):
        info = _seed_agent(agent_service)
        task = task_service.create_task(title="T1")
        resp = task_client.post(f"/api/tasks/{task.id}/assign", json={"agent_id": info["id"]})
        assert resp.status_code == 200
        assert resp.json()["assigned_agent_id"] == info["id"]
        assert resp.json()["status"] == TaskStatus.ASSIGNED.value

    def test_start_task(self, task_client, task_service):
        task = task_service.create_task(title="T1")
        resp = task_client.post(f"/api/tasks/{task.id}/start", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == TaskStatus.RUNNING.value

    def test_complete_task(self, task_client, task_service):
        task = task_service.create_task(title="T1")
        task_service.start_task(task.id)
        resp = task_client.post(f"/api/tasks/{task.id}/complete", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == TaskStatus.COMPLETED.value
        assert resp.json()["completed_at"] is not None

    def test_fail_task(self, task_client, task_service):
        task = task_service.create_task(title="T1")
        resp = task_client.post(f"/api/tasks/{task.id}/fail", json={"error": "boom"})
        assert resp.status_code == 200
        assert resp.json()["status"] == TaskStatus.FAILED.value


class TestTaskEvents:
    def test_events_for_task(self, task_client, task_service):
        task = task_service.create_task(title="T1")
        task_service.start_task(task.id)
        resp = task_client.get(f"/api/tasks/{task.id}/events")
        assert resp.status_code == 200
        types = [e["event_type"] for e in resp.json()]
        assert TaskEventType.CREATED.value in types
        assert TaskEventType.STARTED.value in types

    def test_events_for_missing_task_returns_404(self, task_client):
        resp = task_client.get("/api/tasks/00000000-0000-0000-0000-000000000000/events")
        assert resp.status_code == 404


class TestFeatureFlag:
    def test_disabled_returns_404(self, cm):
        flags = FeatureFlags(cm=cm)
        flags.disable("task_dispatcher")
        app.dependency_overrides[get_connection_manager] = lambda: cm
        try:
            with TestClient(app) as c:
                resp = c.get("/api/tasks")
                assert resp.status_code == 404
                assert "disabled" in resp.json()["detail"]
        finally:
            app.dependency_overrides = {}

    def test_enabled_allows_access(self, cm):
        flags = FeatureFlags(cm=cm)
        flags.enable("task_dispatcher")
        app.dependency_overrides[get_connection_manager] = lambda: cm
        try:
            with TestClient(app) as c:
                resp = c.get("/api/tasks")
                assert resp.status_code == 200
        finally:
            app.dependency_overrides = {}
