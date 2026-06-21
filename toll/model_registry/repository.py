from __future__ import annotations

import json
from typing import Any

from ..ports.model_registry import Model


class ModelRepository:
    def __init__(self, cm):
        self.cm = cm

    def create(self, model: Model) -> Model:
        self.cm.execute(
            """INSERT OR REPLACE INTO models
               (id, provider, provider_model_id, name, description, version, family,
                media_types, capabilities, default_params, status,
                cost_per_unit, cost_unit, metadata, registered_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (
                model.id, model.provider, model.provider_model_id, model.name,
                model.description, model.version, model.family,
                json.dumps(model.media_types, ensure_ascii=False),
                json.dumps(model.capabilities, ensure_ascii=False),
                json.dumps(model.default_params, ensure_ascii=False),
                model.status, model.cost_per_unit, model.cost_unit,
                json.dumps(model.metadata, ensure_ascii=False),
            ),
        )
        for tag in model.tags:
            self.cm.execute(
                "INSERT OR IGNORE INTO model_tags (id, model_id, tag) VALUES (?, ?, ?)",
                (f"{model.id}:{tag}", model.id, tag),
            )
        self.cm.commit()
        return model

    def get(self, model_id: str) -> Model | None:
        row = self.cm.connection.execute(
            "SELECT * FROM models WHERE id = ?", (model_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_model(row)

    def get_by_provider(self, provider: str, provider_model_id: str) -> Model | None:
        row = self.cm.connection.execute(
            "SELECT * FROM models WHERE provider = ? AND provider_model_id = ?",
            (provider, provider_model_id),
        ).fetchone()
        if not row:
            return None
        return self._row_to_model(row)

    def list(self, provider: str | None = None, media_type: str | None = None,
             status: str | None = None, family: str | None = None,
             tag: str | None = None) -> list[Model]:
        parts = ["SELECT DISTINCT m.* FROM models m"]
        params: list[Any] = []
        where = []
        if tag:
            parts.append("JOIN model_tags t ON t.model_id = m.id")
            where.append("t.tag = ?")
            params.append(tag)
        if provider:
            where.append("m.provider = ?")
            params.append(provider)
        if media_type:
            where.append("m.media_types LIKE ?")
            params.append(f"%{media_type}%")
        if status:
            where.append("m.status = ?")
            params.append(status)
        if family:
            where.append("m.family = ?")
            params.append(family)
        if where:
            parts.append("WHERE " + " AND ".join(where))
        parts.append("ORDER BY m.name")
        rows = self.cm.connection.execute(" ".join(parts), params).fetchall()
        return [self._row_to_model(r) for r in rows]

    def update(self, model_id: str, data: dict) -> Model | None:
        allowed = {"name", "description", "version", "status", "cost_per_unit",
                    "cost_unit", "capabilities", "default_params", "metadata"}
        sets = []
        params: list[Any] = []
        for key, value in data.items():
            if key in allowed:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                sets.append(f"{key} = ?")
                params.append(value)
        if not sets:
            return self.get(model_id)
        sets.append("updated_at = datetime('now')")
        params.append(model_id)
        self.cm.execute(
            f"UPDATE models SET {', '.join(sets)} WHERE id = ?", params
        )
        self.cm.commit()
        return self.get(model_id)

    def disable(self, model_id: str) -> bool:
        self.cm.execute(
            "UPDATE models SET status = 'disabled', updated_at = datetime('now') WHERE id = ?",
            (model_id,),
        )
        self.cm.commit()
        return self.cm.connection.total_changes > 0

    def list_providers(self) -> list[str]:
        rows = self.cm.connection.execute(
            "SELECT DISTINCT provider FROM models ORDER BY provider"
        ).fetchall()
        return [r["provider"] for r in rows]

    def count_by_status(self) -> dict[str, int]:
        rows = self.cm.connection.execute(
            "SELECT status, COUNT(*) as cnt FROM models GROUP BY status"
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def _row_to_model(self, row) -> Model:
        return Model(
            id=row["id"],
            provider=row["provider"],
            provider_model_id=row["provider_model_id"],
            name=row["name"],
            description=row["description"] or "",
            version=row["version"],
            family=row["family"],
            media_types=json.loads(row["media_types"]) if row["media_types"] else ["image"],
            capabilities=json.loads(row["capabilities"]) if row["capabilities"] else {},
            default_params=json.loads(row["default_params"]) if row["default_params"] else {},
            status=row["status"],
            cost_per_unit=row["cost_per_unit"],
            cost_unit=row["cost_unit"],
            tags=self._get_tags(row["id"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            registered_at=row["registered_at"],
            updated_at=row["updated_at"],
        )

    def _get_tags(self, model_id: str) -> list[str]:
        rows = self.cm.connection.execute(
            "SELECT tag FROM model_tags WHERE model_id = ? ORDER BY tag", (model_id,)
        ).fetchall()
        return [r["tag"] for r in rows]
