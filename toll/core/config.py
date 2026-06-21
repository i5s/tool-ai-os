import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
DB_PATH = DATA / "toll.db"

# CORS — restrict to local origins by default; override via env var
_CORS_DEFAULT = '["http://localhost", "http://127.0.0.1", "http://localhost:8000", "http://127.0.0.1:8000"]'
CORS_ORIGINS = json.loads(os.environ.get("TOLL_CORS_ORIGINS", _CORS_DEFAULT))

# AI Providers
OPENCODE_BIN = Path.home() / ".opencode" / "bin" / "opencode"
OLLAMA_BIN = "ollama"
OLLAMA_MODEL_DEFAULT = "qwen2.5"

# Browser
FREE_AI_URLS = [
    "https://chatgpt.com",
    "https://gemini.google.com",
    "https://claude.ai",
]

# Website
WEBSITE_PATH = Path.home() / "Claude" / "Projects" / "الموقع"
