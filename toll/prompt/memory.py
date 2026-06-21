from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from ..core.connection_manager import ConnectionManager


class PromptMemory:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def record_success(self, profile_id: str, model_id: str,
                       prompt: str, artifact_id: str | None = None,
                       score: float | None = None):
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        now = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """INSERT INTO prompt_scores
               (profile_id, model_id, score, prompt_hash, artifact_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (profile_id, model_id, score, prompt_hash, artifact_id, now),
        )
        self.cm.commit()

    def record_failure(self, profile_id: str, model_id: str, reason: str):
        now = datetime.now(timezone.utc).isoformat()
        self.cm.execute(
            """INSERT OR IGNORE INTO prompt_blacklist
               (model_id, profile_id, reason, flagged_at)
               VALUES (?, ?, ?, ?)""",
            (model_id, profile_id, reason, now),
        )
        self.cm.commit()

    def is_blacklisted(self, profile_id: str, model_id: str) -> bool:
        row = self.cm.connection.execute(
            "SELECT 1 FROM prompt_blacklist WHERE model_id = ? AND profile_id = ?",
            (model_id, profile_id),
        ).fetchone()
        return row is not None

    def get_consecutive_failures(self, profile_id: str, model_id: str) -> int:
        row = self.cm.connection.execute(
            "SELECT COUNT(*) as cnt FROM prompt_scores"
            " WHERE profile_id = ? AND model_id = ? AND score IS NULL"
            " ORDER BY created_at DESC LIMIT 5",
            (profile_id, model_id),
        ).fetchone()
        return row["cnt"] if row else 0

    def get_avg_score(self, profile_id: str, model_id: str | None = None,
                      limit: int = 20) -> float | None:
        parts = [
            "SELECT AVG(score) as avg_score FROM prompt_scores"
            " WHERE profile_id = ? AND score IS NOT NULL"
        ]
        params: list = [profile_id]
        if model_id:
            parts.append("AND model_id = ?")
            params.append(model_id)
        row = self.cm.connection.execute(" ".join(parts), params).fetchone()
        return round(row["avg_score"], 3) if row and row["avg_score"] else None
