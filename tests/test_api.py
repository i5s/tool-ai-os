from fastapi.testclient import TestClient
from api.main import app
from toll.core.config import CORS_ORIGINS


def test_cors_origins_restricted():
    assert "*" not in CORS_ORIGINS
    assert "http://localhost" in CORS_ORIGINS or "http://127.0.0.1" in CORS_ORIGINS


def test_status_endpoint_available():
    with TestClient(app) as client:
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "limits" in data
        assert "providers" in data
        assert "opencode" in data["limits"]
        assert "ollama" in data["limits"]


def test_chat_endpoint_available():
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


def test_config_endpoint_available():
    with TestClient(app) as client:
        response = client.get("/api/config")
        assert response.status_code == 200
