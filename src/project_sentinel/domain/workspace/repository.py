from typing import Protocol
from uuid import UUID

from project_sentinel.domain.workspace.models import Workspace


class WorkspaceRepository(Protocol):
    async def add(self, workspace: Workspace) -> Workspace:
        """Persist a workspace."""

    async def list(self) -> list[Workspace]:
        """Return all workspaces."""

    async def get(self, workspace_id: UUID) -> Workspace | None:
        """Return one workspace by ID."""

    async def get_default(self) -> Workspace | None:
        """Return the default workspace."""

    async def save(self, workspace: Workspace) -> Workspace:
        """Persist changes to a workspace."""

    async def set_default(self, workspace_id: UUID) -> Workspace | None:
        """Mark one workspace as the default."""

    async def delete(self, workspace_id: UUID) -> bool:
        """Delete one workspace by ID."""
