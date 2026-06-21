"""Feature flag framework for TOOL.

All new capabilities must be gated by a feature flag.
Core Layer components are enabled by default.
Layer 2 dormant features are disabled by default.
"""

from .connection_manager import ConnectionManager

DEFAULT_FLAGS = {
    # Core Layer — always enabled in V1
    "core_chat": True,
    "provider_opencode": True,
    "provider_ollama": True,
    "rate_limiting": True,
    "web_dashboard": True,
    "cli_enabled": True,
    "artifact_basic": True,
    "settings_system": True,
    "planner_enabled": True,
    "workflow_enabled": True,
    "memory_graph": True,
    "workspace_manager": True,
    "context_engine": True,
    "artifact_system": True,
    "carousel_engine": True,
    "report_engine": True,
    "presentation_engine": True,
    "memory_auto_learning": False,
    "planner_strict_mode": False,
    "planner_fast_mode": False,
    # Layer 2 — dormant by default
    "preference_memory": False,
    "knowledge_vault": False,
    "google_drive_sync": False,
    "telegram_enabled": False,
    "task_journal": False,
    "health_dashboard": False,
    "self_improvement": False,
    "users_enabled": False,
    "opendesign_integration": False,
    # Research Layer — Sprint 5A
    "research_provider": True,
    "research_deep": False,
    "citation_engine": True,
    "source_dedup": True,
    "source_import": False,
    "google_drive_backup": False,
    "provider_semantic_scholar": False,
    "provider_google_scholar": False,
    "provider_arxiv": False,
    "provider_crossref": False,
    "provider_zotero": False,
    # Image & Misc
    "image_generation": False,
    "provider_replicate": False,
}

_PREFIX = "feature_"


class FeatureFlags:
    def __init__(self, cm: ConnectionManager, settings=None):
        self.cm = cm
        self._settings = settings
        self._ensure_defaults()

    def _ensure_defaults(self):
        for name, default in DEFAULT_FLAGS.items():
            key = f"{_PREFIX}{name}"
            row = self.cm.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
            if row is None:
                self.cm.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    (key, "true" if default else "false"),
                )
                self.cm.commit()

    def is_enabled(self, name: str, default: bool = False) -> bool:
        if name in DEFAULT_FLAGS:
            default = DEFAULT_FLAGS[name]
        if self._settings:
            val = self._settings.get(f"{_PREFIX}{name}")
            if val is not None:
                return val.lower() in ("true", "1", "yes", "on")
        row = self.cm.execute(
            "SELECT value FROM config WHERE key = ?", (f"{_PREFIX}{name}",)
        ).fetchone()
        if row is None:
            return default
        return row["value"].lower() in ("true", "1", "yes", "on")

    def enable(self, name: str):
        self.cm.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (f"{_PREFIX}{name}", "true"),
        )
        self.cm.commit()

    def disable(self, name: str):
        self.cm.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (f"{_PREFIX}{name}", "false"),
        )
        self.cm.commit()

    def set(self, name: str, enabled: bool):
        self.cm.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (f"{_PREFIX}{name}", "true" if enabled else "false"),
        )
        self.cm.commit()

    def get_all(self) -> dict[str, bool]:
        return {name: self.is_enabled(name) for name in DEFAULT_FLAGS}

    def reset_to_defaults(self):
        for name, default in DEFAULT_FLAGS.items():
            self.cm.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (f"{_PREFIX}{name}", "true" if default else "false"),
            )
            self.cm.commit()
