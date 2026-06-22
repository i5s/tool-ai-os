from __future__ import annotations

from typing import Optional
import json

from .models import Task, TaskEvent, TaskStatus, TaskPriority, TaskEventType
from .repository import TaskRepository


class TaskService:
    def __init__(self, cm):
        self.cm = cm
        self.repo = TaskRepository(cm)

    def create_task(self, title: str, description: Optional[str] = None,
                    priority: str = TaskPriority.MEDIUM.value,
                    created_by: Optional[str] = None) -> Task:
        task = self.repo.create_task(
            Task(title=title, description=description, priority=priority, created_by=created_by)
        )
        self.repo.add_event(
            TaskEvent(task_id=task.id, event_type=TaskEventType.CREATED.value,
                      actor=created_by,
                      payload='{"title": ' + json.dumps(title) + '}')
        )
        return task

    def update_task(self, task_id: str, **fields) -> Optional[Task]:
        return self.repo.update_task(task_id, **fields)

    def assign_task(self, task_id: str, agent_id: str, actor: Optional[str] = None) -> Optional[Task]:
        task = self.repo.update_task(task_id, assigned_agent_id=agent_id, status=TaskStatus.ASSIGNED.value)
        if task:
            self.repo.add_event(
                TaskEvent(task_id=task_id, event_type=TaskEventType.ASSIGNED.value,
                          actor=actor, payload=json.dumps({"agent_id": agent_id}))
            )
        return task

    def start_task(self, task_id: str, actor: Optional[str] = None) -> Optional[Task]:
        task = self.repo.update_task(task_id, status=TaskStatus.RUNNING.value)
        if task:
            self.repo.add_event(
                TaskEvent(task_id=task_id, event_type=TaskEventType.STARTED.value, actor=actor)
            )
        return task

    def complete_task(self, task_id: str, actor: Optional[str] = None) -> Optional[Task]:
        task = self.repo.update_task(task_id, status=TaskStatus.COMPLETED.value)
        if task:
            self.repo.add_event(
                TaskEvent(task_id=task_id, event_type=TaskEventType.COMPLETED.value, actor=actor)
            )
        return task

    def fail_task(self, task_id: str, actor: Optional[str] = None, error: Optional[str] = None) -> Optional[Task]:
        payload = json.dumps({"error": error}) if error else None
        task = self.repo.update_task(task_id, status=TaskStatus.FAILED.value)
        if task:
            self.repo.add_event(
                TaskEvent(task_id=task_id, event_type=TaskEventType.FAILED.value, actor=actor, payload=payload)
            )
        return task

    def list_tasks(self, **filters) -> list[Task]:
        return self.repo.list_tasks(**filters)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.repo.get_task(task_id)
