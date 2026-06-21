from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from ..core.connection_manager import ConnectionManager


class BenchmarkSuiteRow:
    def __init__(self, row: dict):
        self.id: str = row["id"]
        self.name: str = row["name"]
        self.description: str = row.get("description", "")
        self.prompts: list[str] = json.loads(row["prompts"]) if isinstance(row["prompts"], str) else row["prompts"]
        self.media_type: str = row["media_type"]
        self.created_at: str = row["created_at"]
        self.updated_at: str = row["updated_at"]


class BenchmarkRunRow:
    def __init__(self, row: dict):
        self.id: str = row["id"]
        self.suite_id: str | None = row.get("suite_id")
        self.model_id: str = row["model_id"]
        self.prompt: str = row["prompt"]
        self.prompt_index: int | None = row.get("prompt_index")
        self.media_type: str = row["media_type"]
        self.provider_latency_ms: int | None = row.get("provider_latency_ms")
        self.total_duration_ms: int | None = row.get("total_duration_ms")
        self.file_size_bytes: int | None = row.get("file_size_bytes")
        self.quality_score_auto: float | None = row.get("quality_score_auto")
        self.quality_score_human: float | None = row.get("quality_score_human")
        self.cost_cents: float | None = row.get("cost_cents")
        self.output_storage_key: str | None = row.get("output_storage_key")
        self.error: str | None = row.get("error")
        self.created_at: str = row["created_at"]


class BenchmarkRepository:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def create_suite(self, name: str, prompts: list[str], media_type: str,
                     description: str = "") -> BenchmarkSuiteRow:
        now = datetime.now(timezone.utc).isoformat()
        suite_id = str(uuid.uuid4())
        self.cm.execute(
            "INSERT INTO benchmark_suites (id, name, description, prompts, media_type, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (suite_id, name, description, json.dumps(prompts, ensure_ascii=False),
             media_type, now, now),
        )
        self.cm.commit()
        return self.get_suite(suite_id)

    def get_suite(self, suite_id: str) -> BenchmarkSuiteRow | None:
        row = self.cm.connection.execute(
            "SELECT * FROM benchmark_suites WHERE id = ?", (suite_id,)
        ).fetchone()
        return BenchmarkSuiteRow(dict(row)) if row else None

    def list_suites(self, limit: int = 50) -> list[BenchmarkSuiteRow]:
        rows = self.cm.connection.execute(
            "SELECT * FROM benchmark_suites ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [BenchmarkSuiteRow(dict(r)) for r in rows]

    def delete_suite(self, suite_id: str) -> bool:
        self.cm.execute("DELETE FROM benchmark_runs WHERE suite_id = ?", (suite_id,))
        self.cm.execute("DELETE FROM benchmark_suites WHERE id = ?", (suite_id,))
        self.cm.commit()
        return True

    def create_run(self, model_id: str, prompt: str, media_type: str,
                   suite_id: str | None = None, prompt_index: int | None = None,
                   ) -> BenchmarkRunRow:
        now = datetime.now(timezone.utc).isoformat()
        run_id = str(uuid.uuid4())
        self.cm.execute(
            "INSERT INTO benchmark_runs (id, suite_id, model_id, prompt, prompt_index, media_type, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, suite_id, model_id, prompt, prompt_index, media_type, now),
        )
        self.cm.commit()
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> BenchmarkRunRow | None:
        row = self.cm.connection.execute(
            "SELECT * FROM benchmark_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return BenchmarkRunRow(dict(row)) if row else None

    def update_run(self, run_id: str, **kw):
        updates: list[str] = []
        params: list[Any] = []
        for key, val in kw.items():
            updates.append(f"{key} = ?")
            params.append(val)
        params.append(run_id)
        self.cm.execute(
            f"UPDATE benchmark_runs SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self.cm.commit()

    def list_runs(self, model_id: str | None = None, suite_id: str | None = None,
                  limit: int = 100) -> list[BenchmarkRunRow]:
        parts = ["SELECT * FROM benchmark_runs WHERE 1=1"]
        params: list[Any] = []
        if model_id:
            parts.append("AND model_id = ?")
            params.append(model_id)
        if suite_id:
            parts.append("AND suite_id = ?")
            params.append(suite_id)
        parts.append("ORDER BY created_at DESC LIMIT ?")
        params.append(limit)
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [BenchmarkRunRow(dict(r)) for r in rows]

    def avg_scores(self, model_id: str) -> dict:
        row = self.cm.connection.execute(
            "SELECT AVG(quality_score_auto) as avg_auto, AVG(quality_score_human) as avg_human,"
            " AVG(provider_latency_ms) as avg_latency, AVG(cost_cents) as avg_cost,"
            " COUNT(*) as run_count"
            " FROM benchmark_runs WHERE model_id = ? AND error IS NULL",
            (model_id,),
        ).fetchone()
        if not row:
            return {}
        return {
            "avg_quality_auto": round(row["avg_auto"], 2) if row["avg_auto"] else None,
            "avg_quality_human": round(row["avg_human"], 2) if row["avg_human"] else None,
            "avg_latency_ms": round(row["avg_latency"]) if row["avg_latency"] else None,
            "avg_cost_cents": round(row["avg_cost"], 4) if row["avg_cost"] else None,
            "run_count": row["run_count"],
        }
