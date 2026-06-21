from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..core.connection_manager import ConnectionManager


class UsageService:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def record(self, provider: str, media_type: str = "text",
               model_id: str | None = None,
               resource_type: str = "request",
               resource_count: int = 1,
               estimated_cost_cents: float | None = None,
               duration_ms: int = 0,
               success: bool = True,
               error: str | None = None,
               artifact_id: str | None = None,
               profile_id: str | None = None,
               workspace_type: str | None = None,
               workspace_id: str | None = None):
        now = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """INSERT INTO usage_log
               (id, provider, model_id, media_type, resource_type,
                resource_count, estimated_cost_cents, duration_ms,
                success, error, artifact_id, profile_id,
                workspace_type, workspace_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), provider, model_id, media_type,
                resource_type, resource_count, estimated_cost_cents,
                duration_ms, 1 if success else 0, error,
                artifact_id, profile_id, workspace_type, workspace_id, now,
            ),
        )
        self.cm.commit()

    def summary(self, days: int = 30) -> dict:
        today = datetime.now(timezone.utc).isoformat()[:10]
        seven_ago = self._days_ago(7)
        thirty_ago = self._days_ago(30)

        def _agg(since: str) -> dict:
            row = self.cm.connection.execute(
                "SELECT COUNT(*) as requests,"
                " SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as errors,"
                " AVG(CASE WHEN duration_ms>0 THEN duration_ms ELSE NULL END) as avg_latency,"
                " SUM(estimated_cost_cents) as total_cost"
                " FROM usage_log WHERE created_at >= ?",
                (since,),
            ).fetchone()
            return {
                "requests": row["requests"],
                "errors": row["errors"],
                "avg_latency_ms": round(row["avg_latency"]) if row["avg_latency"] else None,
                "total_cost_cents": round(row["total_cost"], 2) if row["total_cost"] else 0.0,
            } if row else {}

        return {
            "today": _agg(today),
            "this_week": _agg(seven_ago),
            "this_month": _agg(thirty_ago),
        }

    def by_provider(self, days: int = 30) -> list[dict]:
        since = self._days_ago(days)
        rows = self.cm.connection.execute(
            "SELECT provider, COUNT(*) as requests,"
            " SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as errors,"
            " AVG(CASE WHEN duration_ms>0 THEN duration_ms ELSE NULL END) as avg_latency,"
            " SUM(estimated_cost_cents) as total_cost"
            " FROM usage_log WHERE created_at >= ?"
            " GROUP BY provider ORDER BY requests DESC",
            (since,),
        ).fetchall()
        return [
            {
                "provider": r["provider"],
                "requests": r["requests"],
                "errors": r["errors"],
                "avg_latency_ms": round(r["avg_latency"]) if r["avg_latency"] else None,
                "total_cost_cents": round(r["total_cost"], 2) if r["total_cost"] else 0.0,
            }
            for r in rows
        ]

    def by_model(self, days: int = 30) -> list[dict]:
        since = self._days_ago(days)
        rows = self.cm.connection.execute(
            "SELECT model_id, provider, COUNT(*) as requests,"
            " SUM(estimated_cost_cents) as total_cost"
            " FROM usage_log WHERE created_at >= ? AND model_id IS NOT NULL"
            " GROUP BY model_id ORDER BY requests DESC",
            (since,),
        ).fetchall()
        return [
            {
                "model_id": r["model_id"],
                "provider": r["provider"],
                "requests": r["requests"],
                "total_cost_cents": round(r["total_cost"], 2) if r["total_cost"] else 0.0,
            }
            for r in rows
        ]

    def daily_cost(self, days: int = 30) -> list[dict]:
        since = self._days_ago(days)
        rows = self.cm.connection.execute(
            "SELECT substr(created_at, 1, 10) as day,"
            " COUNT(*) as requests,"
            " SUM(estimated_cost_cents) as total_cost"
            " FROM usage_log WHERE created_at >= ?"
            " GROUP BY day ORDER BY day ASC",
            (since,),
        ).fetchall()
        return [
            {
                "day": r["day"],
                "requests": r["requests"],
                "total_cost_cents": round(r["total_cost"], 2) if r["total_cost"] else 0.0,
            }
            for r in rows
        ]

    def recent(self, limit: int = 20) -> list[dict]:
        rows = self.cm.connection.execute(
            "SELECT * FROM usage_log ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def _days_ago(self, days: int) -> str:
        from datetime import timedelta
        return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
