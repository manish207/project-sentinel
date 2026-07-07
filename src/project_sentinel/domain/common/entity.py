from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .value_objects import AuditInfo


class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    audit: AuditInfo = Field(default_factory=AuditInfo)

    def touch(self) -> None:
        self.audit.touch()
