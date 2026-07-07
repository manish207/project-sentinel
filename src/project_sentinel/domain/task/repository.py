from typing import Protocol
from uuid import UUID

from project_sentinel.domain.task.models import Task


class TaskRepository(Protocol):
    async def add(self, task: Task) -> Task:
        """Persist a task."""

    async def list(self) -> list[Task]:
        """Return all tasks."""

    async def get(self, task_id: UUID) -> Task | None:
        """Return one task by ID."""

    async def save(self, task: Task) -> Task:
        """Persist changes to a task."""

    async def delete(self, task_id: UUID) -> bool:
        """Delete one task by ID."""
