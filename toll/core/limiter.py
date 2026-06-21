from .storage import Storage
from . import config

class Limiter:
    def __init__(self):
        self.db = Storage()

    def can_use(self, provider):
        limit_key = f"daily_limit_{provider}"
        limit = int(self.db.get_config(limit_key, "20"))
        used = self.db.usage_today(provider)
        return used < limit

    def remaining(self, provider):
        limit_key = f"daily_limit_{provider}"
        limit = int(self.db.get_config(limit_key, "20"))
        used = self.db.usage_today(provider)
        return max(0, limit - used)

    def log_usage(self, provider):
        self.db.log_usage(provider)

    def status(self):
        return {
            "opencode": {"remaining": self.remaining("opencode"), "can_use": self.can_use("opencode")},
            "ollama": {"remaining": self.remaining("ollama"), "can_use": self.can_use("ollama")},
            "browser": {"remaining": self.remaining("browser"), "can_use": self.can_use("browser")},
        }
