from uuid import UUID

from pydantic import Field

from project_sentinel.domain.common import Entity, Priority, Source, Status


class Task(Entity):
    """A unit of work tracked by Sentinel."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: Status = Status.INBOX
    priority: Priority = Priority.MEDIUM
    source: Source = Source.MANUAL
    project_id: UUID | None = None

    def complete(self) -> None:
        self.status = Status.COMPLETED
        self.touch()
