from uuid import UUID

from project_sentinel.domain.common import DomainError
from project_sentinel.domain.workspace import Workspace, WorkspaceRepository


class WorkspaceNotFoundError(DomainError):
    """Raised when a workspace cannot be found."""


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository) -> None:
        self._repository = repository

    async def create_workspace(
        self,
        name: str,
        description: str = "",
        is_default: bool = False,
    ) -> Workspace:
        workspace = Workspace(
            name=name,
            description=description,
            is_default=is_default,
        )
        return await self._repository.add(workspace)

    async def get_or_create_default_workspace(self) -> Workspace:
        workspace = await self._repository.get_default()
        if workspace is not None:
            return workspace
        return await self.create_workspace("Default", is_default=True)

    async def list_workspaces(self) -> list[Workspace]:
        return await self._repository.list()

    async def update_workspace(
        self,
        workspace_id: UUID,
        name: str | None = None,
        description: str | None = None,
        active: bool | None = None,
        is_default: bool | None = None,
    ) -> Workspace:
        workspace = await self._get_required(workspace_id)
        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        if active is not None:
            workspace.active = active
        if is_default is not None:
            workspace.is_default = is_default
            if is_default:
                workspace.active = True
        workspace.touch()
        return await self._repository.save(workspace)

    async def set_default_workspace(self, workspace_id: UUID) -> Workspace:
        workspace = await self._repository.set_default(workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(f"Workspace not found: {workspace_id}")
        return workspace

    async def delete_workspace(self, workspace_id: UUID) -> None:
        deleted = await self._repository.delete(workspace_id)
        if not deleted:
            raise WorkspaceNotFoundError(f"Workspace not found: {workspace_id}")

    async def _get_required(self, workspace_id: UUID) -> Workspace:
        workspace = await self._repository.get(workspace_id)
        if workspace is None:
            raise WorkspaceNotFoundError(f"Workspace not found: {workspace_id}")
        return workspace
