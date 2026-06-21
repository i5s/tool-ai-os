"""Centralized settings system.

Precedence (highest to lowest):
1. Environment variables (TOLL_*)
2. SQLite config store
3. Default values
"""

import os
from typing import Any
from .storage import Storage
from .connection_manager import ConnectionManager
from ..ports.settings import SettingsPort
from ..core.config import DB_PATH


DEFAULTS = {
    "daily_limit_opencode": "20",
    "daily_limit_ollama": "50",
    "daily_limit_browser": "20",
    "ollama_model": "qwen2.5",
    "opencode_bin": str(os.path.expanduser("~/.opencode/bin/opencode")),
    "website_path": str(os.path.expanduser("~/Claude/Projects/الموقع")),
}

_ENV_PREFIX = "TOLL_"


class Settings(SettingsPort):
    def __init__(self, cm: ConnectionManager | None = None, storage: Storage | None = None):
        if storage:
            self.db = storage
        else:
            m = cm or ConnectionManager(DB_PATH)
            self.db = Storage(cm=m)

    def get(self, key: str, default=None) -> Any:
        env_key = f"{_ENV_PREFIX}{key.upper()}"
        if env_key in os.environ:
            return os.environ[env_key]

        db_value = self.db.get_config(key)
        if db_value is not None and db_value != "":
            return db_value

        return DEFAULTS.get(key, default)

    def set(self, key: str, value):
        self.db.set_config(key, str(value))

    def all(self) -> dict:
        result = dict(DEFAULTS)
        for key in DEFAULTS:
            db_value = self.db.get_config(key)
            if db_value is not None:
                result[key] = db_value
        for key in DEFAULTS:
            env_key = f"{_ENV_PREFIX}{key.upper()}"
            if env_key in os.environ:
                result[key] = os.environ[env_key]
        return result

    def opencode_bin(self) -> str:
        return self.get("opencode_bin", DEFAULTS["opencode_bin"])

    def ollama_bin(self) -> str:
        return "ollama"

    def ollama_model(self) -> str:
        return self.get("ollama_model", DEFAULTS["ollama_model"])

    def website_path(self) -> str:
        return self.get("website_path", DEFAULTS["website_path"])
