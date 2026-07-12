from dataclasses import dataclass
from datetime import date
from uuid import UUID
from typing import Literal
from project_sentinel.domain.common import Priority, Status, Importance


@dataclass(frozen=True)
class TaskCreate:
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    importance: Importance = Importance.HIGH
    tags: list[str] | None = None
    due_date: date | None = None
    scheduled_date: date | None = None
    recurring: bool = False
    repeat_every: int | None = None
    repeat_unit: (
        Literal[
            "day",
            "week",
            "month",
            "year",
        ]
        | None
    ) = None
    estimated_minutes: int | None = None
    parent_task_id: UUID | None = None
    project_id: UUID | None = None
    workspace_id: UUID | None = None


@dataclass(frozen=True)
class TaskUpdate:
    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    importance: Importance | None = None
    status: Status | None = None
    tags: list[str] | None = None
    due_date: date | None = None
    scheduled_date: date | None = None
    recurring: bool | None = None
    repeat_every: int | None = None
    repeat_unit: (
        Literal[
            "day",
            "week",
            "month",
            "year",
        ]
        | None
    ) = None
    estimated_minutes: int | None = None
    actual_minutes: int | None = None
    parent_task_id: UUID | None = None
    project_id: UUID | None = None
    workspace_id: UUID | None = None
