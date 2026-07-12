from __future__ import annotations

import builtins
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol
from uuid import UUID
from collections.abc import Iterable

from project_sentinel.domain.common import Priority, Status, Importance
from project_sentinel.domain.task.models import Task


class TaskSort(StrEnum):
    CREATED = "creation"
    PRIORITY = "priority"
    DUE_DATE = "due_date"
    ALPHABETICAL = "alphabetical"


@dataclass(frozen=True)
class TaskFilters:
    status: Status | None = None
    priority: Priority | None = None
    importance: Importance | None = None
    project_id: UUID | None = None
    workspace_id: UUID | None = None
    due_today: date | None = None
    overdue_before: date | None = None
    completed: bool | None = None


class TaskRepository(Protocol):
    async def add(self, task: Task) -> Task:
        """Persist a task."""

    async def list(
        self,
        filters: TaskFilters | None = None,
        sort: TaskSort = TaskSort.CREATED,
    ) -> builtins.list[Task]:
        """Return all tasks."""

    async def search(self, text: str) -> builtins.list[Task]:
        """Search tasks by title and description."""

    async def get(self, task_id: UUID) -> Task | None:
        """Return one task by ID."""

    async def children(
        self,
        parent_task_id: UUID,
    ) -> builtins.list[Task]:
        """Return the immediate child tasks."""

    async def root_tasks(self) -> builtins.list[Task]:
        """Return all tasks that do not have a parent."""

    async def save(self, task: Task) -> Task:
        """Persist changes to a task."""

    async def delete(self, task_id: UUID) -> bool:
        """Delete one task by ID."""

    async def get_many(
        self,
        task_ids: Iterable[UUID],
    ) -> builtins.list[Task]:
        """Return multiple tasks."""

    async def save_many(
        self,
        tasks: Iterable[Task],
    ) -> builtins.list[Task]:
        """Persist multiple tasks."""

    async def delete_many(
        self,
        task_ids: Iterable[UUID],
    ) -> int:
        """Delete multiple tasks and return number deleted."""
