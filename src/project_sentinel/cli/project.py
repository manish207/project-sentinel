import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.cli.runtime import with_session
from project_sentinel.domain.common import DomainError
from project_sentinel.domain.project import Project
from project_sentinel.platform.database.repositories import (
    SqlAlchemyProjectRepository,
    SqlAlchemyWorkspaceRepository,
)
from project_sentinel.services import ProjectService

project_app = typer.Typer(help="Manage projects", no_args_is_help=True)
console = Console()
T = TypeVar("T")


def _build_service(session: AsyncSession) -> ProjectService:
    return ProjectService(
        SqlAlchemyProjectRepository(session),
        SqlAlchemyWorkspaceRepository(session),
    )


@project_app.command()
def create(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option("", "--description", "-d"),
    workspace_id: UUID | None = typer.Option(None, "--workspace"),
) -> None:
    """Create a project."""

    async def action(service: ProjectService) -> Project:
        return await service.create_project(name, workspace_id, description)

    project: Project = _run_project_action(action)
    console.print(f"Created project {project.id}: {project.name}")


@project_app.command(name="list")
def list_projects() -> None:
    """List projects."""

    async def action(service: ProjectService) -> list[Project]:
        return await service.list_projects()

    projects: list[Project] = _run_project_action(action)
    if not projects:
        console.print("No projects found.")
        return

    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Workspace")
    table.add_column("Archived")
    table.add_column("Name")
    for project in projects:
        table.add_row(
            str(project.id),
            str(project.workspace_id),
            "yes" if project.archived else "",
            project.name,
        )
    console.print(table)


@project_app.command()
def update(
    project_id: UUID = typer.Argument(..., help="Project ID"),
    name: str | None = typer.Option(None, "--name"),
    description: str | None = typer.Option(None, "--description", "-d"),
    workspace_id: UUID | None = typer.Option(None, "--workspace"),
    archive: bool = typer.Option(False, "--archive"),
    restore: bool = typer.Option(False, "--restore"),
) -> None:
    """Update a project."""

    archived = None
    if archive:
        archived = True
    if restore:
        archived = False

    async def action(service: ProjectService) -> Project:
        return await service.update_project(
            project_id,
            name=name,
            description=description,
            workspace_id=workspace_id,
            archived=archived,
        )

    project: Project = _run_project_action(action)
    console.print(f"Updated project {project.id}: {project.name}")


@project_app.command()
def delete(project_id: UUID = typer.Argument(..., help="Project ID")) -> None:
    """Delete a project."""

    async def action(service: ProjectService) -> None:
        await service.delete_project(project_id)

    _run_project_action(action)
    console.print(f"Deleted project {project_id}")


def _run_project_action(action: Callable[[ProjectService], Awaitable[T]]) -> T:
    try:
        return asyncio.run(
            with_session(lambda session: action(_build_service(session)))
        )
    except DomainError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error
