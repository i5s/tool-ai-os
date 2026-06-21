from .connection_manager import ConnectionManager


class Limiter:
    def __init__(self, cm: ConnectionManager, settings=None):
        self.cm = cm
        self._settings = settings

    def _limit(self, provider: str) -> int:
        if self._settings:
            val = self._settings.get(f"daily_limit_{provider}")
            if val is not None:
                return int(val)
        row = self.cm.execute(
            "SELECT value FROM config WHERE key = ?", (f"daily_limit_{provider}",)
        ).fetchone()
        return int(row["value"]) if row else 20

    def _used(self, provider: str) -> int:
        row = self.cm.execute(
            "SELECT COUNT(*) as c FROM usage WHERE provider = ? AND date(timestamp) = date('now')",
            (provider,),
        ).fetchone()
        return row["c"] if row else 0

    def can_use(self, provider):
        return self._used(provider) < self._limit(provider)

    def remaining(self, provider):
        return max(0, self._limit(provider) - self._used(provider))

    def log_usage(self, provider):
        self.cm.execute("INSERT INTO usage (provider, action) VALUES (?, ?)", (provider, "ask"))
        self.cm.commit()

    def status(self):
        return {
            "opencode": {"remaining": self.remaining("opencode"), "can_use": self.can_use("opencode")},
            "ollama": {"remaining": self.remaining("ollama"), "can_use": self.can_use("ollama")},
            "browser": {"remaining": self.remaining("browser"), "can_use": self.can_use("browser")},
        }
