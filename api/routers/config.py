import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter
from toll.core.storage import Storage

router = APIRouter()

@router.get("/config")
def get_config():
    db = Storage()
    keys = ["daily_limit_opencode", "daily_limit_ollama", "ollama_model", "opencode_bin", "website_path"]
    return {k: db.get_config(k) for k in keys}

@router.post("/config/{key}/{value}")
def set_config(key: str, value: str):
    db = Storage()
    db.set_config(key, value)
    return {"key": key, "value": value}

@router.get("/history")
def history(limit: int = 20):
    db = Storage()
    return [dict(r) for r in db.history(limit)]
