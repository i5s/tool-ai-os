from __future__ import annotations

from typing import Optional

from .models import AgentMetrics


class AnalyticsService:
    def __init__(self, cm):
        self.cm = cm

    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        row = self.cm.execute(
            """
            SELECT
                a.id,
                a.name,
                COUNT(e.id) as total_executions,
                SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN e.status NOT IN ('completed', 'running') THEN 1 ELSE 0 END) as failed_executions,
                AVG(e.duration_ms) as average_duration_ms
            FROM agents a
            LEFT JOIN agent_executions e ON e.agent_id = a.id
            WHERE a.id = ?
            GROUP BY a.id, a.name
            """,
            (agent_id,),
        ).fetchone()

        if not row:
            return None

        total = row["total_executions"] or 0
        successful = row["successful_executions"] or 0
        failed = row["failed_executions"] or 0

        if total > 0:
            success_rate = successful / total
        else:
            success_rate = 0.0

        avg_duration = row["average_duration_ms"] or 0.0

        council_participation = (
            self.cm.execute(
                """
                SELECT COUNT(DISTINCT session_id) as council_count
                FROM council_members
                WHERE agent_id = ?
                """,
                (agent_id,),
            ).fetchone()
        )

        participation = council_participation["council_count"] if council_participation else 0

        learning_count = (
            self.cm.execute(
                """
                SELECT COUNT(*) as learning_count
                FROM learning_entries
                WHERE agent_id = ?
                """,
                (agent_id,),
            ).fetchone()
        )

        learning = learning_count["learning_count"] if learning_count else 0

        return AgentMetrics(
            agent_id=row["id"],
            agent_name=row["name"],
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            success_rate=round(success_rate, 4),
            average_duration_ms=round(avg_duration, 2) if avg_duration else 0.0,
            council_participation_count=participation,
            learning_entries_created=learning,
        )

    def get_all_agent_metrics(self) -> list[AgentMetrics]:
        rows = self.cm.execute(
            """
            SELECT
                a.id,
                a.name,
                COUNT(e.id) as total_executions,
                SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN e.status NOT IN ('completed', 'running') THEN 1 ELSE 0 END) as failed_executions,
                AVG(e.duration_ms) as average_duration_ms
            FROM agents a
            LEFT JOIN agent_executions e ON e.agent_id = a.id
            GROUP BY a.id, a.name
            """
        ).fetchall()

        result = []
        for row in rows:
            total = row["total_executions"] or 0
            successful = row["successful_executions"] or 0
            failed = row["failed_executions"] or 0
            success_rate = (successful / total) if total > 0 else 0.0
            avg_duration = row["average_duration_ms"] or 0.0

            council_participation = (
                self.cm.execute(
                    """
                    SELECT COUNT(DISTINCT session_id) as council_count
                    FROM council_members
                    WHERE agent_id = ?
                    """,
                    (row["id"],),
                ).fetchone()
            )

            participation = council_participation["council_count"] if council_participation else 0

            learning_count = (
                self.cm.execute(
                    """
                    SELECT COUNT(*) as learning_count
                    FROM learning_entries
                    WHERE agent_id = ?
                    """,
                    (row["id"],),
                ).fetchone()
            )

            learning = learning_count["learning_count"] if learning_count else 0

            result.append(
                AgentMetrics(
                    agent_id=row["id"],
                    agent_name=row["name"],
                    total_executions=total,
                    successful_executions=successful,
                    failed_executions=failed,
                    success_rate=round(success_rate, 4),
                    average_duration_ms=round(avg_duration, 2) if avg_duration else 0.0,
                    council_participation_count=participation,
                    learning_entries_created=learning,
                )
            )

        return result

    def get_top_agents(self, limit: int = 5) -> list[AgentMetrics]:
        all_metrics = self.get_all_agent_metrics()
        return sorted(all_metrics, key=lambda m: m.success_rate, reverse=True)[:limit]
