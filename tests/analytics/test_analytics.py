import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.analytics.service import AnalyticsService
from toll.agents.service import AgentService


@pytest.fixture
def cm(tmp_path):
    db = tmp_path / "test.db"
    mgr = ConnectionManager(str(db))
    mgr.execute("PRAGMA journal_mode=WAL;")
    mgr.execute("PRAGMA foreign_keys = OFF;")
    flags = FeatureFlags(cm=mgr)
    flags.enable("task_dispatcher")
    flags.enable("agent_runtime")
    flags.enable("shared_memory")
    flags.enable("agent_execution_history")
    flags.enable("agent_council")
    flags.enable("learning_loop")
    flags.enable("agent_analytics")
    yield mgr
    mgr.close()


@pytest.fixture
def client(cm):
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def agent(cm):
    svc = AgentService(cm)
    return svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")


class TestAgentAnalytics:
    def test_feature_flag_disabled(self, tmp_path):
        db = tmp_path / "test.db"
        mgr = ConnectionManager(str(db))
        mgr.execute("PRAGMA journal_mode=WAL;")
        FeatureFlags(cm=mgr).enable("task_dispatcher")
        app.dependency_overrides[get_connection_manager] = lambda: mgr
        with TestClient(app) as c:
            r = c.get("/api/analytics/agents")
            assert r.status_code == 404
        app.dependency_overrides.clear()
        mgr.close()

    def test_empty_metrics(self, client, agent):
        r = client.get("/api/analytics/agents")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        found = next((m for m in data if m["agent_id"] == agent.id), None)
        assert found is not None
        assert found["agent_name"] == "Hermes"
        assert found["total_executions"] == 0
        assert found["successful_executions"] == 0
        assert found["failed_executions"] == 0
        assert found["success_rate"] == 0.0
        assert found["average_duration_ms"] == 0.0
        assert found["council_participation_count"] == 0
        assert found["learning_entries_created"] == 0

    def test_single_agent_metrics(self, client, agent, cm):
        cm.execute(
            """
            INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms)
            VALUES (?, ?, ?, 'completed', '2026-06-23T00:00:00Z', 1500)
            """,
            ("exec-1", "task-1", agent.id),
        )
        cm.execute(
            """
            INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms)
            VALUES (?, ?, ?, 'failed', '2026-06-23T00:00:00Z', 800)
            """,
            ("exec-2", "task-2", agent.id),
        )
        cm.execute(
            """
            INSERT INTO council_members (id, session_id, agent_id, role)
            VALUES (?, ?, ?, 'reviewer')
            """,
            ("member-1", "session-1", agent.id),
        )
        cm.execute(
            """
            INSERT INTO learning_entries (id, source_type, source_id, agent_id, title, lesson, confidence, created_at)
            VALUES (?, 'execution', 'exec-1', ?, 'Lesson', 'Content', 0.9, '2026-06-23T00:00:00Z')
            """,
            ("learn-1", agent.id),
        )
        cm.commit()

        r = client.get(f"/api/analytics/agents/{agent.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["agent_id"] == agent.id
        assert data["total_executions"] == 2
        assert data["successful_executions"] == 1
        assert data["failed_executions"] == 1
        assert abs(data["success_rate"] - 0.5) < 0.001
        assert data["average_duration_ms"] == 1150.0
        assert data["council_participation_count"] == 1
        assert data["learning_entries_created"] == 1

    def test_ranking_order(self, client, cm):
        second = AgentService(cm).create_agent(name="Beta", role="worker", rank="worker")
        third = AgentService(cm).create_agent(name="Gamma", role="worker", rank="worker")

        # Beta: 2 completed
        for i in range(2):
            cm.execute(
                "INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms) VALUES (?, ?, ?, 'completed', '2026-06-23T00:00:00Z', 1000)",
                (f"exec-b-{i}", f"task-b-{i}", second.id),
            )
        # Gamma: 1 completed
        cm.execute(
            "INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms) VALUES (?, ?, ?, 'completed', '2026-06-23T00:00:00Z', 500)",
            ("exec-g-1", "task-g-1", third.id),
        )
        cm.commit()

        r = client.get("/api/analytics/agents/top?limit=3")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        agents_by_id = {m["agent_id"]: m for m in data}
        assert second.id in agents_by_id
        assert third.id in agents_by_id
        assert agents_by_id[second.id]["success_rate"] >= agents_by_id[third.id]["success_rate"]
