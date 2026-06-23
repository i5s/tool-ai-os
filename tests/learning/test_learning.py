import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.learning.service import LearningService
from toll.agents.service import AgentService


@pytest.fixture
def cm(tmp_path):
    db = tmp_path / "test.db"
    mgr = ConnectionManager(str(db))
    mgr.execute("PRAGMA journal_mode=WAL;")
    flags = FeatureFlags(cm=mgr)
    flags.enable("learning_loop")
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
def agent(cm):
    svc = AgentService(cm)
    return svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")


class TestLearningLoop:
    def test_feature_flag_disabled(self, tmp_path):
        db = tmp_path / "test.db"
        mgr = ConnectionManager(str(db))
        mgr.execute("PRAGMA journal_mode=WAL;")
        FeatureFlags(cm=mgr).enable("task_dispatcher")
        app.dependency_overrides[get_connection_manager] = lambda: mgr
        with TestClient(app) as c:
            r = c.get("/api/learning")
            assert r.status_code == 404
        app.dependency_overrides.clear()
        mgr.close()

    def test_create_learning(self, client, agent):
        payload = {
            "source_type": "execution",
            "source_id": "exec-123",
            "agent_id": agent.id,
            "title": "Test lesson",
            "lesson": "This is a test lesson",
            "confidence": 0.9,
        }
        r = client.post("/api/learning", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["id"].startswith("learn-")
        assert data["title"] == "Test lesson"
        assert data["source_type"] == "execution"
        assert data["source_id"] == "exec-123"
        assert data["confidence"] == 0.9

    def test_list_learning(self, client, agent, cm):
        LearningService(cm).create_learning(
            source_type="execution",
            source_id="exec-1",
            agent_id=agent.id,
            title="Lesson A",
            lesson="Content A",
        )
        LearningService(cm).create_learning(
            source_type="council",
            source_id="council-1",
            agent_id=agent.id,
            title="Lesson B",
            lesson="Content B",
        )
        all_entries = client.get("/api/learning").json()
        assert len(all_entries) == 2

        exec_entries = client.get("/api/learning?source_type=execution").json()
        assert len(exec_entries) == 1
        assert exec_entries[0]["title"] == "Lesson A"

    def test_get_learning(self, client, agent, cm):
        entry = LearningService(cm).create_learning(
            source_type="task",
            source_id="task-1",
            agent_id=agent.id,
            title="Fetched lesson",
            lesson="Details",
        )
        r = client.get(f"/api/learning/{entry.id}")
        assert r.status_code == 200
        assert r.json()["title"] == "Fetched lesson"

    def test_memory_integration(self, client, agent, cm):
        LearningService(cm).create_learning(
            source_type="execution",
            source_id="exec-99",
            agent_id=agent.id,
            title="Memory lesson",
            lesson="Should appear in memory",
        )
        mem = client.get("/api/memory?scope_id=exec-99").json()
        assert len(mem) == 1
        assert mem[0]["type"] == "lesson"

    def test_feedback_useful(self, client, agent, cm):
        entry = LearningService(cm).create_learning(
            source_type="council",
            source_id="council-5",
            agent_id=agent.id,
            title="Feedback lesson",
            lesson="Rate me",
        )
        r = client.post(f"/api/learning/{entry.id}/useful")
        assert r.status_code == 200
        assert r.json()["feedback_type"] == "useful"

    def test_feedback_ignored(self, client, agent, cm):
        entry = LearningService(cm).create_learning(
            source_type="council",
            source_id="council-6",
            agent_id=agent.id,
            title="Ignored lesson",
            lesson="Ignore me",
        )
        r = client.post(f"/api/learning/{entry.id}/ignored")
        assert r.status_code == 200
        assert r.json()["feedback_type"] == "ignored"

    def test_feedback_incorrect(self, client, agent, cm):
        entry = LearningService(cm).create_learning(
            source_type="council",
            source_id="council-7",
            agent_id=agent.id,
            title="Incorrect lesson",
            lesson="Wrong",
        )
        r = client.post(f"/api/learning/{entry.id}/incorrect")
        assert r.status_code == 200
        assert r.json()["feedback_type"] == "incorrect"
