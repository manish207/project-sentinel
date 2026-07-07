import asyncio
from collections.abc import Awaitable, Callable
from datetime import date
from typing import TypeVar
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.cli.runtime import with_session
from project_sentinel.domain.common import DomainError
from project_sentinel.domain.task import Task, TaskFilters, TaskSort
from project_sentinel.platform.database.repositories import (
    SqlAlchemyTaskRepository,
    SqlAlchemyWorkspaceRepository,
)
from project_sentinel.services import (
    TaskCreate,
    TaskNotFoundError,
    TaskService,
    TaskUpdate,
    parse_priority,
    parse_status,
    today,
)

task_app = typer.Typer(help="Manage tasks", no_args_is_help=True)
console = Console(width=160)
T = TypeVar("T")


def _build_service(session: AsyncSession) -> TaskService:
    repository = SqlAlchemyTaskRepository(session)
    workspace_repository = SqlAlchemyWorkspaceRepository(session)
    return TaskService(repository, workspace_repository)


@task_app.command()
def create(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "--description", "-d"),
    priority: str = typer.Option("medium", "--priority", "-p"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t"),
    due_date: str | None = typer.Option(None, "--due-date"),
    scheduled_date: str | None = typer.Option(None, "--scheduled-date"),
    estimated_minutes: int | None = typer.Option(None, "--estimated-minutes"),
    parent_task_id: UUID | None = typer.Option(None, "--parent-task-id"),
    project_id: UUID | None = typer.Option(None, "--project"),
    workspace_id: UUID | None = typer.Option(None, "--workspace"),
) -> None:
    """Create a task."""

    async def action(service: TaskService) -> Task:
        return await service.create_task(
            title,
            TaskCreate(
                title=title,
                description=description,
                priority=parse_priority(priority),
                tags=tag,
                due_date=_parse_date(due_date),
                scheduled_date=_parse_date(scheduled_date),
                estimated_minutes=estimated_minutes,
                parent_task_id=parent_task_id,
                project_id=project_id,
                workspace_id=workspace_id,
            ),
        )

    task = _run_task_action(action)
    console.print(f"Created task {task.id}: {task.title}")


@task_app.command(name="list")
def list_tasks(
    status: str | None = typer.Option(None, "--status"),
    priority: str | None = typer.Option(None, "--priority"),
    project_id: UUID | None = typer.Option(None, "--project"),
    workspace_id: UUID | None = typer.Option(None, "--workspace"),
    due_today: bool = typer.Option(False, "--today"),
    overdue: bool = typer.Option(False, "--overdue"),
    completed: bool = typer.Option(False, "--completed"),
    sort: str = typer.Option("creation", "--sort"),
) -> None:
    """List tasks."""

    async def action(service: TaskService) -> list[Task]:
        return await service.list_tasks(
            TaskFilters(
                status=parse_status(status) if status else None,
                priority=parse_priority(priority) if priority else None,
                project_id=project_id,
                workspace_id=workspace_id,
                due_today=today() if due_today else None,
                overdue_before=today() if overdue else None,
                completed=True if completed else None,
            ),
            TaskSort(sort),
        )

    tasks = _run_task_action(action)
    _print_tasks(tasks)


@task_app.command()
def search(text: str = typer.Argument(..., help="Search text")) -> None:
    """Search tasks."""

    async def action(service: TaskService) -> list[Task]:
        return await service.search_tasks(text)

    tasks = _run_task_action(action)
    _print_tasks(tasks)


@task_app.command()
def update(
    task_id: UUID = typer.Argument(..., help="Task ID"),
    title: str | None = typer.Option(None, "--title"),
    description: str | None = typer.Option(None, "--description", "-d"),
    priority: str | None = typer.Option(None, "--priority", "-p"),
    status: str | None = typer.Option(None, "--status"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t"),
    due_date: str | None = typer.Option(None, "--due-date"),
    scheduled_date: str | None = typer.Option(None, "--scheduled-date"),
    estimated_minutes: int | None = typer.Option(None, "--estimated-minutes"),
    actual_minutes: int | None = typer.Option(None, "--actual-minutes"),
    parent_task_id: UUID | None = typer.Option(None, "--parent-task-id"),
    project_id: UUID | None = typer.Option(None, "--project"),
    workspace_id: UUID | None = typer.Option(None, "--workspace"),
) -> None:
    """Update a task."""

    async def action(service: TaskService) -> Task:
        return await service.update_task(
            task_id,
            TaskUpdate(
                title=title,
                description=description,
                priority=parse_priority(priority) if priority else None,
                status=parse_status(status) if status else None,
                tags=tag,
                due_date=_parse_date(due_date),
                scheduled_date=_parse_date(scheduled_date),
                estimated_minutes=estimated_minutes,
                actual_minutes=actual_minutes,
                parent_task_id=parent_task_id,
                project_id=project_id,
                workspace_id=workspace_id,
            ),
        )

    task = _run_task_action(action)
    console.print(f"Updated task {task.id}: {task.title}")


def _print_tasks(tasks: list[Task]) -> None:
    if not tasks:
        console.print("No tasks found.")
        return

    table = Table(show_header=True)
    table.add_column("ID", no_wrap=True, overflow="ignore")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Due")
    table.add_column("Title")

    for task in tasks:
        table.add_row(
            str(task.id),
            task.status.value,
            task.priority.value,
            task.due_date.isoformat() if task.due_date else "",
            task.title,
        )

    console.print(table)


@task_app.command()
def complete(task_id: UUID = typer.Argument(..., help="Task ID")) -> None:
    """Mark a task complete."""

    async def action(service: TaskService) -> Task:
        return await service.complete_task(task_id)

    try:
        task = _run_task_action(action)
    except TaskNotFoundError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    console.print(f"Completed task {task.id}: {task.title}")


@task_app.command()
def delete(task_id: UUID = typer.Argument(..., help="Task ID")) -> None:
    """Delete a task."""

    async def action(service: TaskService) -> None:
        await service.delete_task(task_id)

    try:
        _run_task_action(action)
    except TaskNotFoundError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    console.print(f"Deleted task {task_id}")


def _run_task_action(action: Callable[[TaskService], Awaitable[T]]) -> T:
    try:
        return asyncio.run(
            with_session(lambda session: action(_build_service(session)))
        )
    except DomainError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)
