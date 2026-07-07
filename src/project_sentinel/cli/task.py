import asyncio
from collections.abc import Awaitable, Callable
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.domain.task import Task
from project_sentinel.platform.database import get_sessionmaker, init_database
from project_sentinel.platform.database.repositories import SqlAlchemyTaskRepository
from project_sentinel.services import TaskNotFoundError, TaskService

task_app = typer.Typer(help="Manage tasks", no_args_is_help=True)
console = Console()


async def _with_service[T](
    action: Callable[[TaskService], Awaitable[T]],
) -> T:
    await init_database()
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        return await action(_build_service(session))


def _build_service(session: AsyncSession) -> TaskService:
    repository = SqlAlchemyTaskRepository(session)
    return TaskService(repository)


@task_app.command()
def create(title: str = typer.Argument(..., help="Task title")) -> None:
    """Create a task."""

    async def action(service: TaskService) -> Task:
        return await service.create_task(title)

    task = asyncio.run(_with_service(action))
    console.print(f"Created task {task.id}: {task.title}")


@task_app.command(name="list")
def list_tasks() -> None:
    """List tasks."""

    async def action(service: TaskService) -> list[Task]:
        return await service.list_tasks()

    tasks = asyncio.run(_with_service(action))
    if not tasks:
        console.print("No tasks found.")
        return

    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Title")

    for task in tasks:
        table.add_row(
            str(task.id),
            task.status.value,
            task.priority.value,
            task.title,
        )

    console.print(table)


@task_app.command()
def complete(task_id: UUID = typer.Argument(..., help="Task ID")) -> None:
    """Mark a task complete."""

    async def action(service: TaskService) -> Task:
        return await service.complete_task(task_id)

    try:
        task = asyncio.run(_with_service(action))
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
        asyncio.run(_with_service(action))
    except TaskNotFoundError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    console.print(f"Deleted task {task_id}")
