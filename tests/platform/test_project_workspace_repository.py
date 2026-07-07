import asyncio
from pathlib import Path

from project_sentinel.domain.project import Project
from project_sentinel.domain.workspace import Workspace
from project_sentinel.platform.database import get_sessionmaker, init_database
from project_sentinel.platform.database.repositories import (
    SqlAlchemyProjectRepository,
    SqlAlchemyWorkspaceRepository,
)


def _database_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


def test_workspace_repository_crud_and_default(tmp_path: Path):
    async def run() -> None:
        database_url = _database_url(tmp_path / "sentinel.db")
        await init_database(database_url)
        sessionmaker = get_sessionmaker(database_url)

        async with sessionmaker() as session:
            repository = SqlAlchemyWorkspaceRepository(session)
            personal = await repository.add(Workspace(name="Personal", is_default=True))
            work = await repository.add(Workspace(name="Work", is_default=True))
            default = await repository.get_default()
            workspaces = await repository.list()
            deleted = await repository.delete(personal.id)

        assert default is not None
        assert default.id == work.id
        assert [workspace.name for workspace in workspaces] == ["Work", "Personal"]
        assert deleted is True

    asyncio.run(run())


def test_project_repository_crud(tmp_path: Path):
    async def run() -> None:
        database_url = _database_url(tmp_path / "sentinel.db")
        await init_database(database_url)
        sessionmaker = get_sessionmaker(database_url)

        async with sessionmaker() as session:
            workspace_repository = SqlAlchemyWorkspaceRepository(session)
            workspace = await workspace_repository.add(Workspace(name="Personal"))
            repository = SqlAlchemyProjectRepository(session)
            project = await repository.add(
                Project(workspace_id=workspace.id, name="Sentinel")
            )
            project.name = "Project Sentinel"
            await repository.save(project)
            projects = await repository.list()
            deleted = await repository.delete(project.id)

        assert [stored.name for stored in projects] == ["Project Sentinel"]
        assert deleted is True

    asyncio.run(run())
