from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
DB_PATH = DATA / "toll.db"

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
