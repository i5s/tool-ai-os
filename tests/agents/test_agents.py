import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.agents.service import AgentService
from toll.agents.models import AgentRole, AgentRank, AgentStatus


@pytest.fixture
def temp_db_path(tmp_path):
    return tmp_path / "toll_agents_test.db"


@pytest.fixture
def cm(temp_db_path):
    mgr = ConnectionManager(db_path=temp_db_path)
    yield mgr
    mgr.close()


@pytest.fixture
def feature_flags(cm):
    flags = FeatureFlags(cm=cm)
    flags.enable("agent_runtime")
    return flags


@pytest.fixture
def service(cm):
    return AgentService(cm=cm)


@pytest.fixture
def client(cm):
    flags = FeatureFlags(cm=cm)
    flags.enable("agent_runtime")
    app.dependency_overrides[get_connection_manager] = lambda: cm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def _seed_agent(service: AgentService) -> dict:
    agent = service.create_agent(
        name="Test Agent",
        role=AgentRole.DEVELOPER.value,
        rank=AgentRank.WORKER.value,
    )
    return {
        "id": agent.id,
        "name": agent.name,
        "role": agent.role,
        "rank": agent.rank,
        "status": agent.status,
    }


class TestAgentCRUD:
    def test_create_agent(self, client, service):
        payload = {
            "name": "Agent X",
            "role": AgentRole.RESEARCHER.value,
            "rank": AgentRank.ADVISOR.value,
        }
        resp = client.post("/api/agents", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Agent X"
        assert data["role"] == AgentRole.RESEARCHER.value
        assert data["rank"] == AgentRank.ADVISOR.value
        assert "id" in data

    def test_list_agents(self, client, service):
        _seed_agent(service)
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_get_agent(self, client, service):
        info = _seed_agent(service)
        resp = client.get(f"/api/agents/{info['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == info["id"]

    def test_get_missing_agent_returns_404(self, client):
        resp = client.get("/api/agents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_update_agent(self, client, service):
        info = _seed_agent(service)
        resp = client.put(
            f"/api/agents/{info['id']}",
            json={"name": "Renamed", "reputation_score": 0.9},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed"
        assert abs(resp.json()["reputation_score"] - 0.9) < 1e-6

    def test_delete_agent(self, client, service):
        info = _seed_agent(service)
        resp = client.delete(f"/api/agents/{info['id']}")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_delete_missing_returns_404(self, client):
        resp = client.delete("/api/agents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestAgentPromotion:
    def test_promote(self, client, service):
        info = _seed_agent(service)
        assert info["rank"] == AgentRank.WORKER.value
        resp = client.post(f"/api/agents/{info['id']}/promote")
        assert resp.status_code == 200
        assert resp.json()["rank"] == AgentRank.ADVISOR.value

    def test_demote(self, client, service):
        info = _seed_agent(service)
        service.promote_agent(info["id"])
        resp = client.post(f"/api/agents/{info['id']}/demote")
        assert resp.status_code == 200
        assert resp.json()["rank"] == AgentRank.WORKER.value

    def test_promote_at_leader(self, client, service):
        info = _seed_agent(service)
        service.update_agent(info["id"], rank=AgentRank.LEADER.value)
        resp = client.post(f"/api/agents/{info['id']}/promote")
        assert resp.status_code == 200
        assert resp.json()["rank"] == AgentRank.LEADER.value

    def test_demote_at_worker(self, client, service):
        info = _seed_agent(service)
        resp = client.post(f"/api/agents/{info['id']}/demote")
        assert resp.status_code == 200
        assert resp.json()["rank"] == AgentRank.WORKER.value


class TestFeatureFlag:
    def test_disabled_returns_404(self, cm):
        flags = FeatureFlags(cm=cm)
        flags.disable("agent_runtime")
        app.dependency_overrides[get_connection_manager] = lambda: cm
        try:
            with TestClient(app) as c:
                resp = c.get("/api/agents")
                assert resp.status_code == 404
                assert "disabled" in resp.json()["detail"]
        finally:
            app.dependency_overrides = {}

    def test_enabled_allows_access(self, cm):
        flags = FeatureFlags(cm=cm)
        flags.enable("agent_runtime")
        app.dependency_overrides[get_connection_manager] = lambda: cm
        try:
            with TestClient(app) as c:
                resp = c.get("/api/agents")
                assert resp.status_code == 200
        finally:
            app.dependency_overrides = {}


class TestSeedData:
    def test_seed_creates_four_agents(self, cm):
        service = AgentService(cm=cm)
        agents = service.list_agents()
        names = {a.name for a in agents}
        assert "Hermes" in names
        assert "OpenCode" in names
        assert "Open Design" in names
        assert "Ollama" in names

    def test_seed_roles(self, cm):
        service = AgentService(cm=cm)
        mapping = {a.name: a.role for a in service.list_agents()}
        assert mapping["Hermes"] == AgentRole.ARCHITECT.value
        assert mapping["OpenCode"] == AgentRole.DEVELOPER.value
        assert mapping["Open Design"] == AgentRole.DESIGNER.value
        assert mapping["Ollama"] == AgentRole.RESEARCHER.value

    def test_seed_ranks(self, cm):
        service = AgentService(cm=cm)
        mapping = {a.name: a.rank for a in service.list_agents()}
        assert mapping["Hermes"] == AgentRank.LEADER.value
        assert mapping["OpenCode"] == AgentRank.DEPUTY.value
        assert mapping["Open Design"] == AgentRank.ADVISOR.value
        assert mapping["Ollama"] == AgentRank.ADVISOR.value
