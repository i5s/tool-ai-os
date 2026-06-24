"""MCP integration tests."""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from toll.core.connection_manager import ConnectionManager
from toll.core.feature_flags import FeatureFlags
from toll.mcp.client import FilesystemConnector, GitConnector, SQLiteConnector
from toll.mcp.service import MCPService
from toll.runtime.service import RuntimeService
from toll.agents.service import AgentService


PROJECT_ROOT = "/Users/S3EED/Claude/Projects/تول"


def _runtime_env():
    tmp = Path(tempfile.mkdtemp()) / "mcp_tests.db"
    cm = ConnectionManager(str(tmp))
    cm.execute("PRAGMA journal_mode=WAL;")
    cm.execute("PRAGMA foreign_keys = OFF;")
    FeatureFlags(cm=cm).enable("multi_agent_runtime")
    return cm, tmp


def test_filesystem_mcp_list_directory():
    connector = FilesystemConnector(PROJECT_ROOT)
    result = connector.call_tool("list_directory", {"path": "."})
    assert result.success is True
    assert result.error is None
    assert result.duration_ms >= 0
    text = result.output
    assert isinstance(text, str)
    assert len(text) > 0


def test_git_mcp_status():
    connector = GitConnector(PROJECT_ROOT)
    result = connector.call_tool("git_status", {"repo_path": PROJECT_ROOT})
    assert result.success is True
    assert result.error is None
    assert result.duration_ms >= 0


def test_sqlite_mcp_query():
    db_path = f"{PROJECT_ROOT}/tool.db"
    connector = SQLiteConnector(db_path=db_path)
    result = connector.call_tool("sqlite_run", {"sql": "SELECT name FROM sqlite_master WHERE type='table'"})
    assert result.success is True
    assert result.error is None
    assert result.duration_ms >= 0


def test_mcp_service_facade():
    svc = MCPService(PROJECT_ROOT)
    fs = svc.call("filesystem", "list_directory", {"path": "."})
    assert fs["success"] is True
    assert fs["server"] == "filesystem"
    git = svc.call("git", "git_status", {"repo_path": PROJECT_ROOT})
    assert git["success"] is True
    assert git["server"] == "git"
    sqlite = svc.call("sqlite", "sqlite_run", {"sql": "SELECT 1"})
    assert sqlite["success"] is True
    assert sqlite["server"] == "sqlite"


def test_runtime_mcp_execution():
    cm, tmp = _runtime_env()
    agent_svc = AgentService(cm)
    hermes = agent_svc.create_agent(name="Hermes", role="architect", rank="leader", provider="Standard", model="Hermes")
    runtime_svc = RuntimeService(cm, project_root=PROJECT_ROOT)
    job = runtime_svc.create_runtime_job(task_id="test-mcp-runtime", plan_text="MCP runtime test")
    assignments = runtime_svc.assign_agents(job.id, [
        {"agent_id": hermes.id, "fragment": '{"server":"filesystem","tool":"list_directory","arguments":{"path":"."}}'},
    ])
    results = runtime_svc.execute_assignments(job.id)
    assert len(results) == 1
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    assert len(conn.execute("SELECT * FROM runtime_jobs").fetchall()) == 1
    assert len(conn.execute("SELECT * FROM runtime_assignments").fetchall()) == 1
    assert len(conn.execute("SELECT * FROM runtime_results").fetchall()) == 1
    assert len(conn.execute("SELECT * FROM agent_executions").fetchall()) == 1
    row = conn.execute("SELECT * FROM runtime_results").fetchone()
    assert row["result"]
    assert "filesystem" in (row["result"] or "")
