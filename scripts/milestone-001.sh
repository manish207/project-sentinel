#!/usr/bin/env bash
set -e

echo "Creating Domain Common..."

mkdir -p src/project_sentinel/domain/common

cat > src/project_sentinel/domain/common/__init__.py <<'EOF'
from .entity import Entity
from .enums import Priority, Source, Status
from .exceptions import DomainError
from .value_objects import AuditInfo

__all__ = [
    "Entity",
    "Priority",
    "Source",
    "Status",
    "DomainError",
    "AuditInfo",
]
EOF

cat > src/project_sentinel/domain/common/enums.py <<'EOF'
from enum import StrEnum


class Status(StrEnum):
    INBOX = "inbox"
    PLANNED = "planned"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SOMEDAY = "someday"


class Source(StrEnum):
    MANUAL = "manual"
    GITHUB = "github"
    TICKTICK = "ticktick"
    GOOGLE = "google"
    EMAIL = "email"
    CALENDAR = "calendar"
    WAZUH = "wazuh"
    AI = "ai"
EOF

cat > src/project_sentinel/domain/common/exceptions.py <<'EOF'
class DomainError(Exception):
    """Base exception for all domain errors."""
EOF

cat > src/project_sentinel/domain/common/value_objects.py <<'EOF'
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class AuditInfo(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)
EOF

cat > src/project_sentinel/domain/common/entity.py <<'EOF'
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .value_objects import AuditInfo


class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    audit: AuditInfo = Field(default_factory=AuditInfo)

    def touch(self) -> None:
        self.audit.touch()
EOF

mkdir -p tests/domain

cat > tests/domain/test_entity.py <<'EOF'
from project_sentinel.domain.common import Entity


def test_entity_has_id():
    entity = Entity()
    assert entity.id is not None


def test_entity_touch():
    entity = Entity()

    before = entity.audit.updated_at

    entity.touch()

    assert entity.audit.updated_at >= before
EOF

echo
echo "Running tests..."
uv run pytest

echo
echo "Milestone 001 completed."
