import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.reputation.service import ReputationService
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
    flags.enable("agent_reputation")
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


class TestReputationEngine:
    def test_feature_flag_disabled(self, tmp_path):
        db = tmp_path / "test.db"
        mgr = ConnectionManager(str(db))
        mgr.execute("PRAGMA journal_mode=WAL;")
        FeatureFlags(cm=mgr).enable("task_dispatcher")
        app.dependency_overrides[get_connection_manager] = lambda: mgr
        with TestClient(app) as c:
            r = c.get("/api/reputation")
            assert r.status_code == 404
        app.dependency_overrides.clear()
        mgr.close()

    def test_calculate_agent_reputation_empty(self, client, agent, cm):
        svc = ReputationService(cm)
        rep = svc.calculate_agent_reputation(agent.id)
        assert rep.quality_score == 0.0
        assert rep.speed_score == 0.0
        assert rep.reliability_score == 0.0
        assert rep.learning_score == 0.0
        assert rep.council_score == 0.0
        assert rep.reputation_score == 0.0
        assert rep.recommended_rank == "worker"

    def test_refresh_and_get_agent_reputation(self, client, agent, cm):
        cm.execute(
            "INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms) VALUES (?, ?, ?, 'completed', '2026-06-23T00:00:00Z', 1200)",
            ("exec-1", "task-1", agent.id),
        )
        cm.execute(
            "INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms) VALUES (?, ?, ?, 'failed', '2026-06-23T00:00:00Z', 800)",
            ("exec-2", "task-2", agent.id),
        )
        cm.execute(
            "INSERT INTO council_members (id, session_id, agent_id, role) VALUES (?, ?, ?, 'reviewer')",
            ("member-1", "session-1", agent.id),
        )
        cm.execute(
            "INSERT INTO learning_entries (id, source_type, source_id, agent_id, title, lesson, confidence, created_at) VALUES (?, 'execution', 'exec-1', ?, 'Lesson', 'Content', 0.9, '2026-06-23T00:00:00Z')",
            ("learn-1", agent.id),
        )
        cm.execute(
            "INSERT INTO learning_feedback (id, learning_entry_id, feedback_type, created_at) VALUES (?, ?, 'useful', '2026-06-23T00:00:00Z')",
            ("fb-1", "learn-1"),
        )
        cm.commit()

        svc = ReputationService(cm)
        rep = svc.refresh_agent_reputation(agent.id)
        assert rep.recommended_rank in ("leader", "deputy", "advisor", "worker")
        stored = svc.get_agent_reputation(agent.id)
        assert stored is not None
        assert stored.agent_id == agent.id
        assert stored.reputation_score == rep.reputation_score
        assert stored.updated_at != ""

    def test_leaderboard_ordering(self, client, cm):
        a1 = AgentService(cm).create_agent(name="A1", role="worker", rank="worker")
        a2 = AgentService(cm).create_agent(name="A2", role="worker", rank="worker")
        for aid, dur in [(a1.id, 500), (a2.id, 2000)]:
            cm.execute(
                "INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms) VALUES (?, ?, ?, 'completed', '2026-06-23T00:00:00Z', ?)",
                (f"exec-{aid}", f"task-{aid}", aid, dur),
            )
        cm.commit()

        svc = ReputationService(cm)
        svc.refresh_agent_reputation(a1.id)
        svc.refresh_agent_reputation(a2.id)

        r = client.get("/api/reputation/leaderboard?limit=2")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["agent_id"] == a1.id
        assert data[0]["reputation_score"] >= data[1]["reputation_score"]

    def test_score_weighting(self, cm, agent):
        # 3 completed, fast (200ms) => high quality + speed
        for i in range(3):
            cm.execute(
                "INSERT INTO agent_executions (id, task_id, agent_id, status, started_at, duration_ms) VALUES (?, ?, ?, 'completed', '2026-06-23T00:00:00Z', 200)",
                (f"exec-good-{i}", f"task-{i}", agent.id),
            )
        cm.execute(
            "INSERT INTO council_members (id, session_id, agent_id, role) VALUES (?, ?, ?, 'reviewer')",
            ("member-w", "session-w", agent.id),
        )
        cm.execute(
            "INSERT INTO learning_entries (id, source_type, source_id, agent_id, title, lesson, confidence, created_at) VALUES (?, 'execution', 'exec-good-0', ?, 'L', 'text', 0.9, '2026-06-23T00:00:00Z')",
            ("learn-w", agent.id),
        )
        cm.execute(
            "INSERT INTO learning_feedback (id, learning_entry_id, feedback_type, created_at) VALUES (?, ?, 'useful', '2026-06-23T00:00:00Z')",
            ("fb-w", "learn-w"),
        )
        cm.commit()

        svc = ReputationService(cm)
        rep = svc.calculate_agent_reputation(agent.id)
        assert rep.quality_score == 1.0
        assert rep.speed_score > 0.8
        assert rep.reliability_score > 0.8
        assert rep.council_score >= 0.0
        assert rep.recommended_rank in ("leader", "deputy", "advisor", "worker")
