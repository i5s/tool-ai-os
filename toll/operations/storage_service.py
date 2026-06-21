from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone

from ..core.connection_manager import ConnectionManager
from ..model.artifact import ArtifactRepository, ArtifactStatus, ArtifactType


class StorageService:
    def __init__(self, cm: ConnectionManager):
        self.cm = cm
        self.artifact_repo = ArtifactRepository(cm)

    def summary(self) -> dict:
        rows = self.cm.connection.execute(
            "SELECT type, COUNT(*) as count FROM artifacts"
            " WHERE status NOT IN ('deleted', 'archived')"
            " GROUP BY type"
        ).fetchall()
        by_type = {}
        total_count = 0
        for r in rows:
            by_type[r["type"]] = {"count": r["count"]}
            total_count += r["count"]

        media_rows = self.cm.connection.execute(
            "SELECT media_type, COUNT(*) as count FROM media_meta GROUP BY media_type"
        ).fetchall()
        for r in media_rows:
            key = r["media_type"]
            if key not in by_type:
                by_type[key] = {"count": 0}
            by_type[key]["media_count"] = r["count"]

        return {
            "total_artifacts": total_count,
            "by_type": by_type,
        }

    def published_assets(self, limit: int = 50) -> list[dict]:
        rows = self.cm.connection.execute(
            "SELECT id, type, title, rendered_path, preview_url,"
            " created_at, updated_at"
            " FROM artifacts"
            " WHERE rendered_path IS NOT NULL"
            " AND status NOT IN ('deleted', 'archived')"
            " ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def pending_cleanup(self, older_than_days: int = 4) -> list[dict]:
        cutoff = self._days_ago(older_than_days)
        rows = self.cm.connection.execute(
            "SELECT id, type, title, rendered_path,"
            " LENGTH(content) as content_size, created_at"
            " FROM artifacts"
            " WHERE created_at < ?"
            " AND rendered_path IS NOT NULL"
            " AND status NOT IN ('deleted', 'archived')"
            " ORDER BY created_at ASC",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def total_size_mb(self) -> float:
        total = 0
        artifacts_dir = os.path.join(
            os.path.dirname(os.path.dirname(self.cm.db_path)), "data", "artifacts"
        )
        media_dir = os.path.join(
            os.path.dirname(os.path.dirname(self.cm.db_path)), "data", "media"
        )
        for d in [artifacts_dir, media_dir]:
            if os.path.isdir(d):
                for root, dirs, files in os.walk(d):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            total += os.path.getsize(fp)
                        except OSError:
                            pass
        return round(total / (1024 * 1024), 1)

    def retention_policies(self) -> list[dict]:
        rows = self.cm.connection.execute(
            "SELECT * FROM retention_policies ORDER BY name ASC"
        ).fetchall()
        return [dict(r) for r in rows]

    def upsert_retention_policy(self, policy_id: str | None = None,
                                name: str = "Default",
                                retention_days: int = 4,
                                keep_metadata: bool = True,
                                enabled: bool = True,
                                workspace_type: str | None = None,
                                workspace_id: str | None = None,
                                media_type: str | None = None) -> dict:
        import uuid
        now = datetime.now(timezone.utc).isoformat()
        pid = policy_id or str(uuid.uuid4())
        self.cm.execute(
            """INSERT OR REPLACE INTO retention_policies
               (id, name, workspace_type, workspace_id, media_type,
                retention_days, keep_metadata, enabled, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, name, workspace_type, workspace_id, media_type,
             retention_days, 1 if keep_metadata else 0,
             1 if enabled else 0, now),
        )
        self.cm.commit()
        return {"id": pid, "name": name, "retention_days": retention_days}

    def delete_retention_policy(self, policy_id: str) -> bool:
        self.cm.execute("DELETE FROM retention_policies WHERE id = ?", (policy_id,))
        self.cm.commit()
        return True

    def _days_ago(self, days: int) -> str:
        from datetime import timedelta
        return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
