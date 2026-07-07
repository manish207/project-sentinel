from uuid import UUID

from project_sentinel.domain.common import DomainError
from project_sentinel.domain.project import Project, ProjectRepository
from project_sentinel.domain.workspace import WorkspaceRepository
from project_sentinel.services.workspace_service import WorkspaceService


class ProjectNotFoundError(DomainError):
    """Raised when a project cannot be found."""


class ProjectService:
    def __init__(
        self,
        repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
    ) -> None:
        self._repository = repository
        self._workspace_service = WorkspaceService(workspace_repository)

    async def create_project(
        self,
        name: str,
        workspace_id: UUID | None = None,
        description: str = "",
    ) -> Project:
        if workspace_id is None:
            workspace = await self._workspace_service.get_or_create_default_workspace()
            workspace_id = workspace.id
        project = Project(
            workspace_id=workspace_id,
            name=name,
            description=description,
        )
        return await self._repository.add(project)

    async def list_projects(self) -> list[Project]:
        return await self._repository.list()

    async def update_project(
        self,
        project_id: UUID,
        name: str | None = None,
        description: str | None = None,
        workspace_id: UUID | None = None,
        archived: bool | None = None,
    ) -> Project:
        project = await self._get_required(project_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if workspace_id is not None:
            project.workspace_id = workspace_id
        if archived is not None:
            project.archived = archived
        project.touch()
        return await self._repository.save(project)

    async def delete_project(self, project_id: UUID) -> None:
        deleted = await self._repository.delete(project_id)
        if not deleted:
            raise ProjectNotFoundError(f"Project not found: {project_id}")

    async def _get_required(self, project_id: UUID) -> Project:
        project = await self._repository.get(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project not found: {project_id}")
        return project
