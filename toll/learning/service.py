from __future__ import annotations

import json
from typing import Optional

from .repository import LearningRepository
from .models import LearningEntry, LearningFeedback, LearningSourceType, LearningFeedbackType
from ..shared_memory.service import SharedMemoryService


class LearningService:
    def __init__(self, cm, shared_memory_service=None):
        self.cm = cm
        self.repo = LearningRepository(cm)
        self.shared_memory_service = shared_memory_service or SharedMemoryService(cm)

    def create_learning(
        self,
        source_type: str,
        source_id: str,
        agent_id: str,
        title: str,
        lesson: str,
        confidence: float = 1.0,
    ) -> LearningEntry:
        entry = self.repo.create_entry(
            source_type=source_type,
            source_id=source_id,
            agent_id=agent_id,
            title=title,
            lesson=lesson,
            confidence=confidence,
        )
        if self.shared_memory_service:
            self.shared_memory_service.create_memory(
                type="lesson",
                scope=source_type,
                scope_id=source_id,
                title=title,
                content=lesson,
                created_by=agent_id,
                metadata={
                    "source_type": source_type,
                    "source_id": source_id,
                    "confidence": confidence,
                    "learning_entry_id": entry.id,
                },
            )
        return entry

    def get_learning(self, entry_id: str) -> Optional[dict]:
        return self.repo.get_entry(entry_id)

    def list_learning(
        self,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> list[dict]:
        return self.repo.list_entries(source_type=source_type, source_id=source_id)

    def mark_useful(self, entry_id: str) -> LearningFeedback:
        return self.repo.add_feedback(entry_id, LearningFeedbackType.USEFUL.value)

    def mark_ignored(self, entry_id: str) -> LearningFeedback:
        return self.repo.add_feedback(entry_id, LearningFeedbackType.IGNORED.value)

    def mark_incorrect(self, entry_id: str) -> LearningFeedback:
        return self.repo.add_feedback(entry_id, LearningFeedbackType.INCORRECT.value)

    def record_execution_learning(
        self,
        execution_id: str,
        agent_id: str,
        task_id: str,
        status: str,
        stdout: str,
        stderr: str,
        duration_ms: int,
    ) -> Optional[LearningEntry]:
        if status != "completed":
            return None
        title = f"Execution of task {task_id}"
        lesson_parts = [f"Status: {status}", f"Duration: {duration_ms}ms"]
        if stdout:
            lesson_parts.append(f"Stdout: {stdout[:500]}")
        if stderr:
            lesson_parts.append(f"Stderr: {stderr[:500]}")
        lesson = "\n".join(lesson_parts)
        return self.create_learning(
            source_type=LearningSourceType.EXECUTION.value,
            source_id=execution_id,
            agent_id=agent_id,
            title=title,
            lesson=lesson,
            confidence=1.0,
        )

    def record_council_learning(
        self,
        session_id: str,
        agent_id: str,
        strategy: str,
        decision_summary: str,
        rationale: str,
        winning_agent_id: Optional[str] = None,
    ) -> LearningEntry:
        title = f"Council decision ({strategy})"
        lesson_parts = [f"Strategy: {strategy}", f"Summary: {decision_summary}"]
        if winning_agent_id:
            lesson_parts.append(f"Winner: {winning_agent_id}")
        lesson_parts.append(f"Rationale: {rationale}")
        lesson = "\n".join(lesson_parts)
        return self.create_learning(
            source_type=LearningSourceType.COUNCIL.value,
            source_id=session_id,
            agent_id=agent_id,
            title=title,
            lesson=lesson,
            confidence=1.0,
        )
