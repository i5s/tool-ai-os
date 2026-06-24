"""Operational health tests."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags

DB_PATH = "/Users/S3EED/Claude/Projects/تول/tool.db"


def _prepare_db():
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
    cm = ConnectionManager(DB_PATH)
    cm.execute("PRAGMA journal_mode=WAL;")
    cm.execute("PRAGMA foreign_keys = OFF;")
    FeatureFlags(cm=cm).enable("multi_agent_runtime")
    cm.commit()
    cm.close()


_prepare_db()


def test_health_ok():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_health_agents():
    with TestClient(app) as client:
        response = client.get("/api/health/agents")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] in {"ok", "degraded"}
        assert "hermes" in body["agents"]
        assert "opencode" in body["agents"]
        assert "ollama" in body["agents"]
        assert "opendesign" in body["agents"]


def test_health_runtime():
    with TestClient(app) as client:
        response = client.get("/api/health/runtime")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["runtime_feature_enabled"] is True
        assert "running" in body
        assert "queued" in body
        assert "failed" in body
        assert body["running"] >= 0
        assert body["queued"] >= 0
        assert body["failed"] >= 0


def test_health_mcp():
    with TestClient(app) as client:
        response = client.get("/api/health/mcp")
        assert response.status_code == 200
        body = response.json()
        assert "filesystem" in body["servers"]
        assert "git" in body["servers"]
        assert "sqlite" in body["servers"]


def test_health_database():
    with TestClient(app) as client:
        response = client.get("/api/health/database")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "table_count" in body
        assert isinstance(body["tables"], list)


def test_health_providers():
    with TestClient(app) as client:
        response = client.get("/api/health/providers")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "hermes" in body["providers"]
        assert "opencode" in body["providers"]
        assert "ollama" in body["providers"]
        assert "opendesign" in body["providers"]
