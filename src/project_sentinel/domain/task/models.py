from datetime import UTC, date, datetime
from uuid import UUID
from typing import Literal

from pydantic import Field, field_validator, model_validator

from project_sentinel.domain.common import DomainError, Entity, Priority, Source, Status

ALLOWED_STATUS_TRANSITIONS: dict[Status, set[Status]] = {
    Status.INBOX: {
        Status.PLANNED,
        Status.READY,
        Status.IN_PROGRESS,
        Status.WAITING,
        Status.BLOCKED,
        Status.COMPLETED,
        Status.CANCELLED,
        Status.ARCHIVED,
    },
    Status.PLANNED: {
        Status.INBOX,
        Status.READY,
        Status.IN_PROGRESS,
        Status.WAITING,
        Status.BLOCKED,
        Status.COMPLETED,
        Status.CANCELLED,
        Status.ARCHIVED,
    },
    Status.READY: {
        Status.PLANNED,
        Status.IN_PROGRESS,
        Status.WAITING,
        Status.BLOCKED,
        Status.COMPLETED,
        Status.CANCELLED,
        Status.ARCHIVED,
    },
    Status.IN_PROGRESS: {
        Status.WAITING,
        Status.BLOCKED,
        Status.COMPLETED,
        Status.CANCELLED,
        Status.ARCHIVED,
    },
    Status.WAITING: {
        Status.READY,
        Status.IN_PROGRESS,
        Status.BLOCKED,
        Status.COMPLETED,
        Status.CANCELLED,
        Status.ARCHIVED,
    },
    Status.BLOCKED: {
        Status.READY,
        Status.IN_PROGRESS,
        Status.WAITING,
        Status.COMPLETED,
        Status.CANCELLED,
        Status.ARCHIVED,
    },
    Status.COMPLETED: {Status.ARCHIVED},
    Status.CANCELLED: {Status.ARCHIVED},
    Status.ARCHIVED: set(),
}


class InvalidTaskTransitionError(DomainError):
    """Raised when a task status change is not allowed."""


class Task(Entity):
    """A unit of work tracked by Sentinel."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: Status = Status.INBOX
    priority: Priority = Priority.MEDIUM
    source: Source = Source.MANUAL
    tags: list[str] = Field(default_factory=list)
    due_date: date | None = None
    scheduled_date: date | None = None
    recurring: bool = False
    repeat_every: int | None = None
    repeat_unit: Literal["day", "week", "month", "year"] | None = None
    completed_at: datetime | None = None
    estimated_minutes: int | None = Field(default=None, ge=0)
    actual_minutes: int | None = Field(default=None, ge=0)
    parent_task_id: UUID | None = None
    project_id: UUID | None = None
    workspace_id: UUID | None = None

    def complete(self) -> None:
        self.change_status(Status.COMPLETED)

    def change_status(self, status: Status) -> None:
        if status == self.status:
            return
        if status not in ALLOWED_STATUS_TRANSITIONS[self.status]:
            raise InvalidTaskTransitionError(
                f"Cannot transition task from {self.status.value} to {status.value}"
            )
        self.status = status
        self.completed_at = datetime.now(UTC) if status == Status.COMPLETED else None
        self.touch()

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            value = tag.strip().lower()
            if value and value not in seen:
                normalized.append(value)
                seen.add(value)
        return normalized

    @model_validator(mode="after")
    def validate_dates(self) -> "Task":
        if (
            self.due_date is not None
            and self.scheduled_date is not None
            and self.scheduled_date > self.due_date
        ):
            raise ValueError("scheduled_date cannot be after due_date")
        if self.status == Status.COMPLETED and self.completed_at is None:
            self.completed_at = datetime.now(UTC)
        if self.status != Status.COMPLETED and self.completed_at is not None:
            raise ValueError("completed_at requires completed status")
        return self
