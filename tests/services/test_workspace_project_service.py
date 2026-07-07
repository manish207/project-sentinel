import asyncio

from project_sentinel.domain.project import Project
from project_sentinel.domain.workspace import Workspace
from project_sentinel.services import ProjectService, WorkspaceService


class FakeWorkspaceRepository:
    def __init__(self) -> None:
        self.workspaces: dict[object, Workspace] = {}

    async def add(self, workspace: Workspace) -> Workspace:
        if workspace.is_default:
            for existing in self.workspaces.values():
                existing.is_default = False
        self.workspaces[workspace.id] = workspace
        return workspace

    async def list(self) -> list[Workspace]:
        return list(self.workspaces.values())

    async def get(self, workspace_id) -> Workspace | None:
        return self.workspaces.get(workspace_id)

    async def get_default(self) -> Workspace | None:
        for workspace in self.workspaces.values():
            if workspace.is_default:
                return workspace
        return None

    async def save(self, workspace: Workspace) -> Workspace:
        if workspace.is_default:
            for existing in self.workspaces.values():
                if existing.id != workspace.id:
                    existing.is_default = False
        self.workspaces[workspace.id] = workspace
        return workspace

    async def set_default(self, workspace_id) -> Workspace | None:
        workspace = self.workspaces.get(workspace_id)
        if workspace is None:
            return None
        for existing in self.workspaces.values():
            existing.is_default = False
        workspace.is_default = True
        workspace.active = True
        return workspace

    async def delete(self, workspace_id) -> bool:
        return self.workspaces.pop(workspace_id, None) is not None


class FakeProjectRepository:
    def __init__(self) -> None:
        self.projects: dict[object, Project] = {}

    async def add(self, project: Project) -> Project:
        self.projects[project.id] = project
        return project

    async def list(self) -> list[Project]:
        return list(self.projects.values())

    async def get(self, project_id) -> Project | None:
        return self.projects.get(project_id)

    async def save(self, project: Project) -> Project:
        self.projects[project.id] = project
        return project

    async def delete(self, project_id) -> bool:
        return self.projects.pop(project_id, None) is not None


def test_workspace_service_manages_default_workspace():
    async def run() -> None:
        service = WorkspaceService(FakeWorkspaceRepository())

        first = await service.create_workspace("Personal", is_default=True)
        second = await service.create_workspace("Work", is_default=True)
        workspaces = await service.list_workspaces()

        assert first.is_default is False
        assert second.is_default is True
        assert len(workspaces) == 2

    asyncio.run(run())


def test_project_service_uses_default_workspace():
    async def run() -> None:
        workspace_repository = FakeWorkspaceRepository()
        service = ProjectService(FakeProjectRepository(), workspace_repository)

        project = await service.create_project("Sentinel")
        updated = await service.update_project(project.id, name="Project Sentinel")

        assert project.workspace_id is not None
        assert updated.name == "Project Sentinel"
        assert (await workspace_repository.get_default()) is not None

    asyncio.run(run())
