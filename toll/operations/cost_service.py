from __future__ import annotations

from ..core.connection_manager import ConnectionManager
from .usage_service import UsageService


class CostService:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm
        self.usage = UsageService(cm)

    def total(self, days: int = 30) -> dict:
        summary = self.usage.summary(days)
        return {
            "total_cost_cents": summary.get("this_month", {}).get("total_cost_cents", 0.0),
            "total_requests": summary.get("this_month", {}).get("requests", 0),
        }

    def by_provider(self, days: int = 30) -> list[dict]:
        return self.usage.by_provider(days)

    def by_model(self, days: int = 30) -> list[dict]:
        return self.usage.by_model(days)

    def daily(self, days: int = 30) -> list[dict]:
        return self.usage.daily_cost(days)
