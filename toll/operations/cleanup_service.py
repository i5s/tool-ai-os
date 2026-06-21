from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from ..core.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm

    def simulate(self) -> dict:
        policies = self._enabled_policies()
        total_files = 0
        total_bytes = 0
        by_policy = []
        for policy in policies:
            artifacts = self._match_artifacts(policy)
            count = len(artifacts)
            size = sum(
                a.get("file_size_bytes", 0) or 0 for a in artifacts
            )
            if count > 0:
                total_files += count
                total_bytes += size
                by_policy.append({
                    "policy_id": policy["id"],
                    "policy_name": policy["name"],
                    "retention_days": policy["retention_days"],
                    "artifact_count": count,
                    "total_bytes": size,
                    "keep_metadata": bool(policy["keep_metadata"]),
                })
        return {
            "total_artifacts": total_files,
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 1),
            "by_policy": by_policy,
        }

    def execute(self) -> dict:
        policies = self._enabled_policies()
        total_deleted = 0
        total_bytes = 0
        by_policy = []
        for policy in policies:
            artifacts = self._match_artifacts(policy)
            policy_count = 0
            policy_bytes = 0
            for art in artifacts:
                self._cleanup_one(art, policy)
                policy_count += 1
                policy_bytes += art.get("file_size_bytes", 0) or 0
            if policy_count > 0:
                total_deleted += policy_count
                total_bytes += policy_bytes
                by_policy.append({
                    "policy_id": policy["id"],
                    "policy_name": policy["name"],
                    "cleaned": policy_count,
                    "freed_bytes": policy_bytes,
                })
        return {
            "total_cleaned": total_deleted,
            "total_freed_bytes": total_bytes,
            "total_freed_mb": round(total_bytes / (1024 * 1024), 1),
            "by_policy": by_policy,
        }

    def log(self, limit: int = 20) -> list[dict]:
        rows = self.cm.connection.execute(
            "SELECT * FROM cleanup_log ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def _enabled_policies(self) -> list[dict]:
        rows = self.cm.connection.execute(
            "SELECT * FROM retention_policies WHERE enabled = 1"
        ).fetchall()
        return [dict(r) for r in rows]

    def _match_artifacts(self, policy: dict) -> list[dict]:
        cutoff = self._days_ago(policy["retention_days"])
        conditions = [
            "created_at < ?",
            "rendered_path IS NOT NULL",
            "status NOT IN ('deleted', 'archived')",
        ]
        params: list[Any] = [cutoff]
        if policy.get("media_type"):
            conditions.append("type = ?")
            params.append(policy["media_type"])
        rows = self.cm.connection.execute(
            "SELECT id, type, title, rendered_path, created_at,"
            " LENGTH(content) as file_size_bytes"
            " FROM artifacts WHERE " + " AND ".join(conditions)
            + " ORDER BY created_at ASC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def _cleanup_one(self, art: dict, policy: dict):
        rendered_path = art.get("rendered_path")
        if rendered_path and os.path.isfile(rendered_path):
            try:
                os.remove(rendered_path)
                logger.info("Cleaned up %s", rendered_path)
            except OSError as e:
                logger.warning("Failed to delete %s: %s", rendered_path, e)

        keep = bool(policy.get("keep_metadata", 1))
        if keep:
            self.cm.execute(
                "UPDATE artifacts SET rendered_path = NULL, preview_url = NULL,"
                " content = json_set(content, '$.cleaned_at', ?)"
                " WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), art["id"]),
            )
        else:
            self.cm.execute(
                "UPDATE artifacts SET status = 'archived' WHERE id = ?",
                (art["id"],),
            )
        self.cm.commit()

        self.cm.execute(
            "INSERT INTO cleanup_log (id, policy_id, artifact_id, action,"
            " file_size_bytes, details, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()), policy["id"], art["id"],
                "keep_metadata" if keep else "archived",
                art.get("file_size_bytes"),
                f"Deleted rendered file for {art.get('title', '')}",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.cm.commit()

    def _days_ago(self, days: int) -> str:
        from datetime import timedelta
        return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
