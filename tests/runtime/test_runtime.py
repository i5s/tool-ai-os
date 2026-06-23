import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_connection_manager
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.runtime.service import RuntimeService
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
    flags.enable("multi_agent_runtime")
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


class TestRuntime:
    def test_feature_flag_disabled(self, tmp_path):
        db = tmp_path / "test.db"
        mgr = ConnectionManager(str(db))
        mgr.execute("PRAGMA journal_mode=WAL;")
        FeatureFlags(cm=mgr).enable("task_dispatcher")
        app.dependency_overrides[get_connection_manager] = lambda: mgr
        with TestClient(app) as c:
            r = c.get("/api/runtime/jobs")
            assert r.status_code == 404
        app.dependency_overrides.clear()
        mgr.close()

    def test_create_and_get_job(self, client, agent, cm):
        r = client.post("/api/runtime/jobs", json={"task_id": "task-1", "plan_text": "Plan"})
        assert r.status_code == 200
        job = r.json()
        assert job["status"] == "pending"
        r2 = client.get(f"/api/runtime/jobs/{job['id']}")
        assert r2.status_code == 200
        assert r2.json()["id"] == job["id"]

    def _mock_run_agent(self, agent_id: str, prompt: str) -> dict:
        return {
            "status": "success",
            "output": f"Mock real execution for {agent_id}: {prompt}",
            "duration_ms": 1000,
            "metadata": {"mocked": True},
        }

    def test_task_assignment_and_execution(self, client, cm):
        agent_svc = AgentService(cm)
        hermes = agent_svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")
        opencode = agent_svc.create_agent(name="OpenCode", role="developer", rank="deputy", provider="Standard", model="OpenCode")
        ollama = agent_svc.create_agent(name="Ollama", role="researcher", rank="advisor", provider="Local", model="Ollama")
        job_resp = client.post("/api/runtime/jobs", json={"task_id": "task-1", "plan_text": "Multi-agent test"}).json()
        job_id = job_resp["id"]
        assign_resp = client.post(
            f"/api/runtime/jobs/{job_id}/assign",
            json={
                "fragments": [
                    {"fragment": "Architecture design", "agent_id": hermes.id},
                    {"fragment": "Implementation", "agent_id": opencode.id},
                    {"fragment": "Research", "agent_id": ollama.id},
                ]
            },
        )
        assert assign_resp.status_code == 200
        assignments = assign_resp.json()
        assert len(assignments) == 3
        with patch.object(RuntimeService, "_run_agent", side_effect=self._mock_run_agent):
            r = client.post(f"/api/runtime/jobs/{job_id}/execute")
        assert r.status_code == 200
        data = r.json()
        assert data["job"]["status"] == "completed"
        assert len(data["assignments"]) == 3
        statuses = {a["assigned_agent_id"]: a["status"] for a in data["assignments"]}
        assert statuses[hermes.id] == "completed"
        assert statuses[opencode.id] == "completed"
        assert statuses[ollama.id] == "completed"

    def test_results_after_execution(self, client, cm):
        agent_svc = AgentService(cm)
        hermes = agent_svc.create_agent(name="Hermes-Result", role="architect", rank="leader", provider="Standard", model="Hermes")
        opencode = agent_svc.create_agent(name="OpenCode-Result", role="developer", rank="deputy", provider="Standard", model="OpenCode")
        ollama = agent_svc.create_agent(name="Ollama-Result", role="researcher", rank="advisor", provider="Local", model="Ollama")
        job_resp = client.post("/api/runtime/jobs", json={"task_id": "task-2", "plan_text": "Results test"}).json()
        job_id = job_resp["id"]
        assign_resp = client.post(
            f"/api/runtime/jobs/{job_id}/assign",
            json={
                "fragments": [
                    {"fragment": "Plan", "agent_id": hermes.id},
                    {"fragment": "Code", "agent_id": opencode.id},
                    {"fragment": "Research", "agent_id": ollama.id},
                ]
            },
        )
        assert assign_resp.status_code == 200
        assignments = assign_resp.json()
        assert len(assignments) == 3
        with patch.object(RuntimeService, "_run_agent", side_effect=self._mock_run_agent):
            client.post(f"/api/runtime/jobs/{job_id}/execute")
        r = client.get(f"/api/runtime/jobs/{job_id}/results")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 3
        agent_ids = {row["agent_id"] for row in data}
        assert hermes.id in agent_ids
        assert opencode.id in agent_ids
        assert ollama.id in agent_ids
