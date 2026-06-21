"""Feature flag framework for TOOL.

All new capabilities must be gated by a feature flag.
Core Layer components are enabled by default.
Layer 2 dormant features are disabled by default.
"""

from .storage import Storage

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
    "memory_auto_learning": False,
    "planner_strict_mode": False,
    "planner_fast_mode": False,
    # Layer 2 — dormant by default
    "preference_memory": False,
    "knowledge_vault": False,
    "artifact_system": False,
    "google_drive_sync": False,
    "telegram_enabled": False,
    "task_journal": False,
    "health_dashboard": False,
    "self_improvement": False,
    "users_enabled": False,
}

_PREFIX = "feature_"


class FeatureFlags:
    def __init__(self, storage: Storage | None = None):
        self.db = storage or Storage()
        self._ensure_defaults()

    def _ensure_defaults(self):
        """Persist any missing flags with their default values."""
        for name, default in DEFAULT_FLAGS.items():
            key = f"{_PREFIX}{name}"
            if self.db.get_config(key) is None:
                self.db.set_config(key, "true" if default else "false")

    def is_enabled(self, name: str, default: bool = False) -> bool:
        """Check whether a feature flag is enabled.

        Unknown flags fall back to `default` and are NOT persisted,
        allowing callers to experiment without polluting config.
        """
        if name in DEFAULT_FLAGS:
            default = DEFAULT_FLAGS[name]
        value = self.db.get_config(f"{_PREFIX}{name}")
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def enable(self, name: str):
        self.db.set_config(f"{_PREFIX}{name}", "true")

    def disable(self, name: str):
        self.db.set_config(f"{_PREFIX}{name}", "false")

    def set(self, name: str, enabled: bool):
        self.db.set_config(f"{_PREFIX}{name}", "true" if enabled else "false")

    def get_all(self) -> dict[str, bool]:
        """Return the current state of all known flags."""
        return {name: self.is_enabled(name) for name in DEFAULT_FLAGS}

    def reset_to_defaults(self):
        """Reset all known flags to their default values."""
        for name, default in DEFAULT_FLAGS.items():
            self.db.set_config(f"{_PREFIX}{name}", "true" if default else "false")
