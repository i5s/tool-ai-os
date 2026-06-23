import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.council.service import CouncilService
from toll.agents.service import AgentService
from toll.agents.models import AgentStatus


@pytest.fixture
def cm(tmp_path):
    db = tmp_path / "test.db"
    mgr = ConnectionManager(str(db))
    mgr.execute("PRAGMA journal_mode=WAL;")
    flags = FeatureFlags(cm=mgr)
    flags.enable("agent_council")
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
    agent_svc = AgentService(cm)
    self_id = agent_svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")
    other_agent = agent_svc.create_agent(name="OpenCode", role="developer", rank="deputy", provider="Standard", model="OpenCode")
    return self_id, other_agent


class TestAgentCouncil:
    def test_create_session(self, cm, client):
        resp = client.post("/api/council", json={"strategy": "majority"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "open"
        assert body["strategy"] == "majority"

    def test_feature_flag_disabled(self, tmp_path):
        db = tmp_path / "disabled.db"
        cm = ConnectionManager(str(db))
        cm.execute("PRAGMA journal_mode=WAL;")
        FeatureFlags(cm=cm)
        app.dependency_overrides[get_connection_manager] = lambda: cm
        with TestClient(app) as c:
            resp = c.get("/api/council")
            assert resp.status_code == 404
        app.dependency_overrides.clear()
        cm.close()

    def test_list_sessions(self, cm, client):
        client.post("/api/council", json={"strategy": "majority"})
        client.post("/api/council", json={"strategy": "consensus"})
        resp = client.get("/api/council")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_member_management_initial(self, cm, client, seeded):
        self_id, _ = seeded
        resp = client.post("/api/council", json={"strategy": "majority", "member_ids": ["Hermes", "OpenCode"]})
        session_id = resp.json()["id"]
        resp = client.get(f"/api/council/{session_id}")
        assert resp.status_code == 200
        members = resp.json()["members"]
        assert len(members) == 2

    def test_submit_vote(self, cm, client, seeded):
        self_id, other_id = seeded
        session = client.post("/api/council", json={"strategy": "majority"}).json()
        session_id = session["id"]
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "Hermes", "vote": "approve"})
        session = client.get(f"/api/council/{session_id}").json()
        votes = session["votes"]
        assert len(votes) == 1
        assert votes[0]["vote"] == "approve"

    def test_majority_strategy(self, cm, client, seeded):
        self_id, other_id = seeded
        session = client.post("/api/council", json={"strategy": "majority"}).json()
        session_id = session["id"]
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "Hermes", "vote": "approve"})
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "OpenCode", "vote": "reject"})
        result = client.post(f"/api/council/{session_id}/finalize", json={}).json()
        assert result["session"]["status"] == "completed"
        assert result["decision"]["winning_agent_id"] in ("Hermes", "OpenCode")

    def test_consensus_strategy_success(self, cm, client, seeded):
        session = client.post("/api/council", json={"strategy": "consensus"}).json()
        session_id = session["id"]
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "Hermes", "vote": "approve"})
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "OpenCode", "vote": "approve"})
        result = client.post(f"/api/council/{session_id}/finalize", json={}).json()
        assert result["session"]["status"] == "completed"
        assert result["decision"]["winning_agent_id"] in ("Hermes", "OpenCode")

    def test_consensus_strategy_failure(self, cm, client, seeded):
        session = client.post("/api/council", json={"strategy": "consensus"}).json()
        session_id = session["id"]
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "Hermes", "vote": "approve"})
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "OpenCode", "vote": "reject"})
        result = client.post(f"/api/council/{session_id}/finalize", json={}).json()
        assert result["session"]["status"] == "completed"
        assert result["decision"]["winning_agent_id"] is None

    def test_decision_endpoint(self, cm, client, seeded):
        session = client.post("/api/council", json={"strategy": "majority"}).json()
        session_id = session["id"]
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "Hermes", "vote": "approve"})
        client.post(f"/api/council/{session_id}/vote", json={"agent_id": "OpenCode", "vote": "approve"})
        client.post(f"/api/council/{session_id}/finalize", json={})
        resp = client.get(f"/api/council/{session_id}/decision")
        assert resp.status_code == 200
        assert "decision" in resp.json()

    def test_agent_pool_enforcement(self, cm, client):
        with pytest.raises(ValueError) as exc:
            CouncilService(cm).create_session(task_id=None, strategy="majority", member_ids=["GhostBot"])
        assert "GhostBot not found" in str(exc.value)
