from typing import Protocol
from uuid import UUID

from project_sentinel.domain.project.models import Project


class ProjectRepository(Protocol):
    async def add(self, project: Project) -> Project:
        """Persist a project."""

    async def list(self) -> list[Project]:
        """Return all projects."""

    async def get(self, project_id: UUID) -> Project | None:
        """Return one project by ID."""

    async def save(self, project: Project) -> Project:
        """Persist changes to a project."""

    async def delete(self, project_id: UUID) -> bool:
        """Delete one project by ID."""
