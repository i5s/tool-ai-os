import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.tasks.service import TaskService
from toll.agents.service import AgentService
from toll.executions.service import ExecutionService


@pytest.fixture
def cm(tmp_path):
    db = tmp_path / "test.db"
    mgr = ConnectionManager(str(db))
    mgr.execute("PRAGMA journal_mode=WAL;")
    flags = FeatureFlags(cm=mgr)
    flags.enable("agent_execution_history")
    flags.enable("task_dispatcher")
    flags.enable("agent_runtime")
    flags.enable("shared_memory")
    yield mgr
    mgr.close()


@pytest.fixture
def client(cm):
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seeded(cm):
    task_svc = TaskService(cm)
    agent_svc = AgentService(cm)
    task = task_svc.create_task(title="History task", created_by="test")
    agent = agent_svc.create_agent(name="HistoryAgent", role="worker", rank="junior")
    return task, agent


class TestExecutionHistory:
    def test_start_execution_creates_record(self, cm, seeded):
        svc = ExecutionService(cm)
        task, agent = seeded
        ex = svc.start_execution(task_id=task.id, agent_id=agent.id)
        assert ex is not None
        assert ex.status == "running"
        assert ex.task_id == task.id
        assert ex.agent_id == agent.id
        assert ex.started_at is not None
        assert ex.completed_at is None
        assert ex.duration_ms is None

    def test_complete_execution_updates_record(self, cm, seeded):
        svc = ExecutionService(cm)
        task, agent = seeded
        ex = svc.start_execution(task_id=task.id, agent_id=agent.id)
        done = svc.complete_execution(ex.id, duration_ms=120, stdout="ok", stderr="")
        assert done is not None
        assert done.status == "completed"
        assert done.duration_ms == 120
        assert done.stdout == "ok"
        assert done.completed_at is not None

    def test_fail_execution_updates_record(self, cm, seeded):
        svc = ExecutionService(cm)
        task, agent = seeded
        ex = svc.start_execution(task_id=task.id, agent_id=agent.id)
        failed = svc.fail_execution(ex.id, duration_ms=30, error="boom")
        assert failed is not None
        assert failed.status == "failed"
        assert failed.duration_ms == 30
        assert failed.stderr == "boom"

    def test_list_executions_by_task(self, cm, seeded):
        svc = ExecutionService(cm)
        task, agent = seeded
        svc.start_execution(task_id=task.id, agent_id=agent.id)
        other_task = TaskService(cm).create_task(title="Other")
        svc.start_execution(task_id=other_task.id, agent_id=agent.id)
        results = svc.list_executions(task_id=task.id)
        assert len(results) == 1
        assert results[0].task_id == task.id

    def test_list_executions_by_agent(self, cm, seeded):
        svc = ExecutionService(cm)
        task, agent = seeded
        other_agent = AgentService(cm).create_agent(name="OtherAgent", role="worker", rank="junior")
        svc.start_execution(task_id=task.id, agent_id=agent.id)
        svc.start_execution(task_id=task.id, agent_id=other_agent.id)
        results = svc.list_executions(agent_id=agent.id)
        assert len(results) == 1
        assert results[0].agent_id == agent.id

    def test_feature_flag_disabled(self, tmp_path):
        db = tmp_path / "disabled.db"
        cm = ConnectionManager(str(db))
        cm.execute("PRAGMA journal_mode=WAL;")
        FeatureFlags(cm=cm)

        app.dependency_overrides[get_connection_manager] = lambda: cm
        with TestClient(app) as c:
            resp = c.get("/api/executions")
            assert resp.status_code == 404
        app.dependency_overrides.clear()
        cm.close()

    def test_feature_flag_enabled_allows_access(self, cm, client):
        resp = client.get("/api/executions")
        assert resp.status_code == 200
        assert resp.json() == []
