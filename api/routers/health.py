from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import asyncio
import shutil
from pathlib import Path

from api.dependencies import get_settings
from toll.core.settings import Settings
from toll.core.feature_flags import FeatureFlags
from toll.agents.adapters.hermes import HermesAdapter
from toll.adapters.llm.opencode import OpenCodeProvider

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/agents")
def health_agents(settings: Settings = Depends(get_settings)):
    results = {}
    hermes_adapter = HermesAdapter()
    results["hermes"] = {
        "available": hermes_adapter.validate(),
        "path": "/Users/S3EED/.hermes/hermes-agent/venv/bin/hermes" if hermes_adapter.validate() else None,
    }
    opencode_path = settings.opencode_bin()
    opencode_available = Path(opencode_path).exists() if opencode_path else False
    results["opencode"] = {
        "available": opencode_available,
        "path": opencode_path if opencode_available else None,
    }
    return results


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
