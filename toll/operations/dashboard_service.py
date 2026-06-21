from __future__ import annotations

from ..core.connection_manager import ConnectionManager
from ..core.registry import ProviderRegistry
from ..model_registry.service import ModelRegistryService
from .usage_service import UsageService


class ProviderDashboardService:
    def __init__(self, cm: ConnectionManager, registry: ProviderRegistry,
                 model_registry: ModelRegistryService | None = None):
        self.cm = cm
        self.registry = registry
        self.model_registry = model_registry
        self.usage = UsageService(cm)

    def summary(self, hours: int = 24) -> list[dict]:
        since = self._hours_ago(hours)
        status = self.registry.status()
        providers = []

        for category in ("llm", "media", "search"):
            for name, available in status.get(category, {}).items():
                stats = self._provider_stats(name, since)
                models = []
                if self.model_registry:
                    matched = self.model_registry.list(provider=name)
                    models = [
                        {"id": m.id, "name": m.name, "status": m.status}
                        for m in matched[:5]
                    ]
                providers.append({
                    "name": name,
                    "category": category,
                    "available": available,
                    "last_request": stats.get("last_request"),
                    "error_rate": stats.get("error_rate", 0.0),
                    "avg_latency_ms": stats.get("avg_latency_ms"),
                    "requests": stats.get("requests", 0),
                    "models": models,
                })

        providers.sort(key=lambda p: p["requests"], reverse=True)
        return providers

    def provider_detail(self, name: str) -> dict | None:
        for p in self.summary():
            if p["name"] == name:
                detail = self.usage.by_model(30)
                detail = [m for m in detail if m.get("provider") == name]
                p["model_breakdown"] = detail[:10]
                return p
        return None

    def _provider_stats(self, name: str, since: str) -> dict:
        row = self.cm.connection.execute(
            "SELECT COUNT(*) as requests,"
            " SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as errors,"
            " AVG(CASE WHEN duration_ms>0 THEN duration_ms ELSE NULL END) as avg_latency,"
            " MAX(CASE WHEN success=1 THEN created_at ELSE NULL END) as last_request"
            " FROM usage_log WHERE provider = ? AND created_at >= ?",
            (name, since),
        ).fetchone()
        if not row or row["requests"] == 0:
            return {}
        return {
            "requests": row["requests"],
            "error_rate": round(row["errors"] / row["requests"], 3) if row["requests"] else 0.0,
            "avg_latency_ms": round(row["avg_latency"]) if row["avg_latency"] else None,
            "last_request": row["last_request"],
        }

    def _hours_ago(self, hours: int) -> str:
        from datetime import datetime, timedelta, timezone
        return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
