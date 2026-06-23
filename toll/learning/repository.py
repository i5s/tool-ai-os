from __future__ import annotations

import uuid
from typing import Optional

from .models import LearningEntry, LearningFeedback, LearningSourceType, LearningFeedbackType


class LearningRepository:
    def __init__(self, cm):
        self.cm = cm

    def create_entry(
        self,
        source_type: str,
        source_id: str,
        agent_id: str,
        title: str,
        lesson: str,
        confidence: float = 1.0,
    ) -> LearningEntry:
        entry = LearningEntry(
            id=f"learn-{uuid.uuid4().hex[:8]}",
            source_type=source_type,
            source_id=source_id,
            agent_id=agent_id,
            title=title,
            lesson=lesson,
            confidence=confidence,
        )
        self.cm.execute(
            """INSERT INTO learning_entries
            (id, source_type, source_id, agent_id, title, lesson, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.id,
                entry.source_type,
                entry.source_id,
                entry.agent_id,
                entry.title,
                entry.lesson,
                entry.confidence,
                entry.created_at,
            ),
        )
        self.cm.commit()
        return entry

    def get_entry(self, entry_id: str) -> Optional[dict]:
        row = self.cm.execute(
            "SELECT * FROM learning_entries WHERE id = ?", (entry_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_entries(
        self,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> list[dict]:
        sql = "SELECT * FROM learning_entries"
        params = []
        clauses = []
        if source_type is not None:
            clauses.append("source_type = ?")
            params.append(source_type)
        if source_id is not None:
            clauses.append("source_id = ?")
            params.append(source_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC"
        return [dict(r) for r in self.cm.execute(sql, params).fetchall()]

    def add_feedback(self, entry_id: str, feedback_type: str) -> LearningFeedback:
        feedback = LearningFeedback(
            id=f"fb-{uuid.uuid4().hex[:8]}",
            learning_entry_id=entry_id,
            feedback_type=feedback_type,
        )
        self.cm.execute(
            """INSERT INTO learning_feedback
            (id, learning_entry_id, feedback_type, created_at)
            VALUES (?, ?, ?, ?)""",
            (feedback.id, feedback.learning_entry_id, feedback.feedback_type, feedback.created_at),
        )
        self.cm.commit()
        return feedback

    def list_feedback(self, entry_id: str) -> list[dict]:
        return [
            dict(r)
            for r in self.cm.execute(
                "SELECT * FROM learning_feedback WHERE learning_entry_id = ? ORDER BY created_at DESC",
                (entry_id,),
            ).fetchall()
        ]
