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
from project_sentinel.domain.workspace import Workspace
from project_sentinel.platform.database.repositories import (
    SqlAlchemyWorkspaceRepository,
)
from project_sentinel.services import WorkspaceService

workspace_app = typer.Typer(help="Manage workspaces", no_args_is_help=True)
console = Console()
T = TypeVar("T")


def _build_service(session: AsyncSession) -> WorkspaceService:
    return WorkspaceService(SqlAlchemyWorkspaceRepository(session))


@workspace_app.command()
def create(
    name: str = typer.Argument(..., help="Workspace name"),
    description: str = typer.Option("", "--description", "-d"),
    is_default: bool = typer.Option(False, "--default"),
) -> None:
    """Create a workspace."""

    async def action(service: WorkspaceService) -> Workspace:
        return await service.create_workspace(name, description, is_default)

    workspace: Workspace = _run_workspace_action(action)
    console.print(f"Created workspace {workspace.id}: {workspace.name}")


@workspace_app.command(name="list")
def list_workspaces() -> None:
    """List workspaces."""

    async def action(service: WorkspaceService) -> list[Workspace]:
        return await service.list_workspaces()

    workspaces: list[Workspace] = _run_workspace_action(action)
    if not workspaces:
        console.print("No workspaces found.")
        return

    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Default")
    table.add_column("Active")
    table.add_column("Name")
    for workspace in workspaces:
        table.add_row(
            str(workspace.id),
            "yes" if workspace.is_default else "",
            "yes" if workspace.active else "no",
            workspace.name,
        )
    console.print(table)


@workspace_app.command()
def update(
    workspace_id: UUID = typer.Argument(..., help="Workspace ID"),
    name: str | None = typer.Option(None, "--name"),
    description: str | None = typer.Option(None, "--description", "-d"),
    active: bool | None = typer.Option(None, "--active/--inactive"),
    is_default: bool | None = typer.Option(None, "--default/--not-default"),
) -> None:
    """Update a workspace."""

    async def action(service: WorkspaceService) -> Workspace:
        return await service.update_workspace(
            workspace_id,
            name=name,
            description=description,
            active=active,
            is_default=is_default,
        )

    workspace: Workspace = _run_workspace_action(action)
    console.print(f"Updated workspace {workspace.id}: {workspace.name}")


@workspace_app.command()
def delete(workspace_id: UUID = typer.Argument(..., help="Workspace ID")) -> None:
    """Delete a workspace."""

    async def action(service: WorkspaceService) -> None:
        await service.delete_workspace(workspace_id)

    _run_workspace_action(action)
    console.print(f"Deleted workspace {workspace_id}")


def _run_workspace_action(action: Callable[[WorkspaceService], Awaitable[T]]) -> T:
    try:
        return asyncio.run(
            with_session(lambda session: action(_build_service(session)))
        )
    except DomainError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error
