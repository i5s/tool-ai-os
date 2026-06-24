from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import asyncio
import sqlite3
import time
from pathlib import Path

from api.dependencies import get_connection_manager, get_settings, get_feature_flags
from toll.core.settings import Settings
from toll.core.feature_flags import FeatureFlags
from toll.core.config import ROOT, DB_PATH
from toll.agents.adapters.hermes import HermesAdapter
from toll.adapters.llm.opencode import OpenCodeProvider
from toll.adapters.llm.ollama import OllamaProvider
from toll.agents.adapters.opendesign import OpenDesignAdapter
from toll.mcp.client import FilesystemConnector, GitConnector, SQLiteConnector

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


def _agent_meta(name: str, available: bool, response_time_ms: int | None = None):
    status = "ok" if available else "error"
    return {
        "name": name,
        "available": available,
        "status": status,
        "last_response_time_ms": response_time_ms,
    }


@router.get("/health/agents")
def health_agents(settings: Settings = Depends(get_settings)):
    results = {}

    started = time.time()
    hermes_adapter = HermesAdapter()
    hermes_available = hermes_adapter.validate()
    hermes_duration = int((time.time() - started) * 1000) if hermes_available else None
    results["hermes"] = _agent_meta("Hermes", hermes_available, hermes_duration)
    if hermes_available:
        results["hermes"]["path"] = "/Users/S3EED/.hermes/hermes-agent/venv/bin/hermes"

    started = time.time()
    opencode_path = settings.opencode_bin()
    opencode_available = Path(opencode_path).exists() if opencode_path else False
    opencode_duration = int((time.time() - started) * 1000) if opencode_available else None
    results["opencode"] = _agent_meta("OpenCode", opencode_available, opencode_duration)
    if opencode_available:
        results["opencode"]["path"] = opencode_path

    started = time.time()
    ollama_provider = OllamaProvider(settings=settings)
    ollama_available = ollama_provider.is_available()
    ollama_duration = int((time.time() - started) * 1000) if ollama_available else None
    results["ollama"] = _agent_meta("Ollama", ollama_available, ollama_duration)

    started = time.time()
    opendesign_adapter = OpenDesignAdapter()
    opendesign_available = opendesign_adapter.validate()
    opendesign_duration = int((time.time() - started) * 1000) if opendesign_available else None
    results["opendesign"] = _agent_meta("OpenDesign", opendesign_available, opendesign_duration)
    if opendesign_available:
        results["opendesign"]["path"] = "/Applications/Open Design.app/Contents/Resources/open-design/bin/vela"

    overall_ok = all(item["available"] for item in results.values())
    return {"status": "ok" if overall_ok else "degraded", "agents": results}


@router.post("/health/agents/{agent_name}/test")
def test_agent(agent_name: str, prompt: str = "Hello", settings: Settings = Depends(get_settings)):
    name = agent_name.strip().lower()
    if name == "hermes":
        adapter = HermesAdapter()
        if not adapter.validate():
            raise HTTPException(status_code=503, detail="Hermes binary not found")
        result = adapter.execute(task_id="", title=prompt, description=None, context=None)
        return result
    if name in {"opencode", "open code"}:
        provider = OpenCodeProvider(settings=settings)
        if not provider.is_available():
            raise HTTPException(status_code=503, detail="OpenCode binary not found")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            resp = loop.run_until_complete(provider.ask(prompt))
            loop.close()
            return {"status": "success", "output": resp.text, "provider": "opencode"}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")


def _runtime_job_counts(cm):
    try:
        rows = cm.execute(
            "SELECT status, COUNT(*) as cnt FROM runtime_jobs GROUP BY status"
        ).fetchall()
        counts = {}
        for row in rows:
            counts[row["status"]] = row["cnt"]
        return {
            "running": counts.get("running", 0),
            "queued": counts.get("queued", counts.get("assigned", 0)),
            "failed": counts.get("failed", 0),
        }
    except Exception:
        return {"running": 0, "queued": 0, "failed": 0}


@router.get("/health/runtime")
def health_runtime(cm=Depends(get_connection_manager), flags: FeatureFlags = Depends(get_feature_flags)):
    return {
        "status": "ok",
        "runtime_feature_enabled": flags.is_enabled("multi_agent_runtime"),
        **_runtime_job_counts(cm),
    }


@router.get("/health/mcp")
def health_mcp():
    connector = FilesystemConnector(str(ROOT))
    git = GitConnector(str(ROOT))
    sqlite = SQLiteConnector(db_path=str(DB_PATH))

    fs_res = connector.call_tool("list_directory", {"path": str(ROOT)})
    git_res = git.call_tool("git_status", {"repo_path": str(ROOT)})
    sqlite_res = sqlite.call_tool("list_tables", {})

    servers = {
        "filesystem": {"available": fs_res.success, "error": fs_res.error, "duration_ms": fs_res.duration_ms},
        "git": {"available": git_res.success, "error": git_res.error, "duration_ms": git_res.duration_ms},
        "sqlite": {"available": sqlite_res.success, "error": sqlite_res.error, "duration_ms": sqlite_res.duration_ms},
    }
    return {"status": "ok", "servers": servers}


@router.get("/health/database")
def health_database():
    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("PRAGMA integrity_check")
            cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
        return {
            "status": "ok",
            "connection": "open",
            "table_count": len(tables),
            "tables": tables,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health/providers")
def health_providers(settings: Settings = Depends(get_settings)):
    providers = {}

    hermes_path = Path("/Users/S3EED/.hermes/hermes-agent/venv/bin/hermes")
    providers["hermes"] = {
        "type": "cli",
        "path": str(hermes_path),
        "available": hermes_path.exists() and hermes_path.is_file(),
    }

    opencode_path = settings.opencode_bin()
    providers["opencode"] = {
        "type": "cli",
        "path": opencode_path,
        "available": Path(opencode_path).exists() if opencode_path else False,
    }

    ollama_model = settings.ollama_model()
    providers["ollama"] = {"type": "service", "model": ollama_model, "available": True}

    opendesign_cli = Path("/Applications/Open Design.app/Contents/Resources/open-design/bin/vela")
    providers["opendesign"] = {
        "type": "daemon",
        "path": str(opendesign_cli),
        "available": opendesign_cli.exists() and opendesign_cli.is_file(),
    }

    return {"status": "ok", "providers": providers}
