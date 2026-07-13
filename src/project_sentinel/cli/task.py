import asyncio
from collections.abc import Awaitable, Callable
from datetime import date
from typing import TypeVar
from uuid import UUID
from typing import Literal, cast

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.ext.asyncio import AsyncSession
from rich.tree import Tree

from project_sentinel.cli.runtime import with_session
from project_sentinel.domain.common import DomainError, Status
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
    TaskNode,
    TaskGraphService,
    parse_priority,
    parse_status,
    today,
    parse_importance,
)

task_app = typer.Typer(help="Manage tasks", no_args_is_help=True)
console = Console(width=160)
T = TypeVar("T")

depends_app = typer.Typer(help="Manage task dependencies")

task_app.add_typer(
    depends_app,
    name="depends",
)


def _build_service(session: AsyncSession) -> TaskService:
    repository = SqlAlchemyTaskRepository(session)
    workspace_repository = SqlAlchemyWorkspaceRepository(session)
    return TaskService(repository, workspace_repository)


def _build_graph_service(session: AsyncSession) -> TaskGraphService:
    repository = SqlAlchemyTaskRepository(session)
    return TaskGraphService(repository)


@task_app.command()
def create(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "--description", "-d"),
    priority: str = typer.Option("medium", "--priority", "-p"),
    importance: str = typer.Option("high", "--importance"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t"),
    due_date: str | None = typer.Option(None, "--due-date"),
    scheduled_date: str | None = typer.Option(None, "--scheduled-date"),
    recurring: bool = typer.Option(False, "--recurring"),
    repeat_every: int | None = typer.Option(None, "--repeat-every"),
    repeat_unit: str | None = typer.Option(None, "--repeat-unit"),
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
                importance=parse_importance(importance),
                tags=tag,
                due_date=_parse_date(due_date),
                scheduled_date=_parse_date(scheduled_date),
                recurring=recurring,
                repeat_every=repeat_every,
                repeat_unit=_parse_repeat_unit(repeat_unit),
                estimated_minutes=estimated_minutes,
                parent_task_id=parent_task_id,
                project_id=project_id,
                workspace_id=workspace_id,
            ),
        )

    task = _run_task_action(action)
    console.print(f"Created task {task.id}: {task.title}")


@task_app.command(name="add-subtask")
def add_subtask(
    parent_id: UUID = typer.Argument(..., help="Parent task ID"),
    title: str = typer.Argument(..., help="Subtask title"),
    description: str = typer.Option("", "--description", "-d"),
    priority: str = typer.Option("medium", "--priority", "-p"),
    importance: str = typer.Option("high", "--importance"),
) -> None:
    """Create a subtask."""

    async def action(service: TaskService) -> Task:
        return await service.create_task(
            title,
            TaskCreate(
                title=title,
                description=description,
                priority=parse_priority(priority),
                importance=parse_importance(importance),
                parent_task_id=parent_id,
            ),
        )

    task = _run_task_action(action)

    console.print(f"Created subtask {task.id} under {parent_id}")


@task_app.command(name="list")
def list_tasks(
    status: str | None = typer.Option(None, "--status"),
    priority: str | None = typer.Option(None, "--priority"),
    importance: str | None = typer.Option(None, "--importance"),
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
                importance=(parse_importance(importance) if importance else None),
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
def ready() -> None:
    """List ready-to-work tasks."""

    async def action(service: TaskService) -> list[Task]:
        return await service.ready_tasks()

    tasks = _run_task_action(action)

    _print_tasks(tasks)


@task_app.command()
def tree() -> None:
    """Display tasks as a hierarchy."""

    async def action(graph: TaskGraphService) -> list[TaskNode]:
        return await graph.task_tree()

    roots = _run_graph_action(action)

    if not roots:
        console.print("No tasks found.")
        return

    tree = Tree("📂 Tasks")

    for node in roots:
        _build_tree(tree, node)

    console.print(tree)


@task_app.command()
def children(
    task_id: UUID = typer.Argument(..., help="Parent task ID"),
) -> None:
    """List direct subtasks."""

    async def action(graph: TaskGraphService) -> list[Task]:
        return await graph.children(task_id)

    tasks = _run_graph_action(action)
    _print_tasks(tasks)


@task_app.command()
def update(
    task_id: UUID = typer.Argument(..., help="Task ID"),
    title: str | None = typer.Option(None, "--title"),
    description: str | None = typer.Option(None, "--description", "-d"),
    priority: str | None = typer.Option(None, "--priority", "-p"),
    importance: str | None = typer.Option(None, "--importance"),
    status: str | None = typer.Option(None, "--status"),
    tag: list[str] | None = typer.Option(None, "--tag", "-t"),
    due_date: str | None = typer.Option(None, "--due-date"),
    scheduled_date: str | None = typer.Option(None, "--scheduled-date"),
    recurring: bool = typer.Option(False, "--recurring"),
    repeat_every: int | None = typer.Option(None, "--repeat-every"),
    repeat_unit: str | None = typer.Option(None, "--repeat-unit"),
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
                importance=(parse_importance(importance) if importance else None),
                status=parse_status(status) if status else None,
                tags=tag,
                due_date=_parse_date(due_date),
                scheduled_date=_parse_date(scheduled_date),
                recurring=recurring,
                repeat_every=repeat_every,
                repeat_unit=_parse_repeat_unit(repeat_unit),
                estimated_minutes=estimated_minutes,
                actual_minutes=actual_minutes,
                parent_task_id=parent_task_id,
                project_id=project_id,
                workspace_id=workspace_id,
            ),
        )

    task = _run_task_action(action)
    console.print(f"Updated task {task.id}: {task.title}")


async def dependencies(
    self,
    task_id: UUID,
) -> list[Task]:
    task = await self._get_required(task_id)

    return await self._repository.get_many(
        task.depends_on,
    )


@depends_app.command("add")
def add_dependency(
    task_id: UUID,
    dependency_id: UUID,
) -> None:
    """Add a dependency."""

    async def action(service: TaskService) -> None:
        await service.add_dependency(
            task_id,
            dependency_id,
        )

    _run_task_action(action)

    console.print(f"Added dependency {dependency_id} -> {task_id}")


@depends_app.command("remove")
def remove_dependency(
    task_id: UUID,
    dependency_id: UUID,
) -> None:
    """Remove a dependency."""

    async def action(service: TaskService) -> None:
        await service.remove_dependency(
            task_id,
            dependency_id,
        )

    _run_task_action(action)

    console.print(f"Removed dependency {dependency_id} from {task_id}")


@depends_app.command("list")
def list_dependencies(
    task_id: UUID,
) -> None:
    """List task dependencies."""

    async def action(
        service: TaskService,
    ) -> list[Task]:
        return await service.dependencies(task_id)

    tasks = _run_task_action(action)

    _print_tasks(tasks)


def _build_tree(branch: Tree, node: TaskNode) -> None:
    icons = {
        Status.INBOX: "📥",
        Status.PLANNED: "📌",
        Status.READY: "🟢",
        Status.IN_PROGRESS: "🚧",
        Status.WAITING: "⏳",
        Status.BLOCKED: "🚫",
        Status.COMPLETED: "✅",
        Status.CANCELLED: "❌",
        Status.ARCHIVED: "📦",
    }

    icon = icons.get(node.task.status, "📄")

    due = (
        f" [dim]({node.task.due_date.isoformat()})[/dim]" if node.task.due_date else ""
    )

    child = branch.add(
        f"{icon} "
        f"[bold]{node.task.title}[/bold] "
        f"[cyan]{node.task.priority.value}[/cyan]"
        f"{due}"
    )

    for child_node in node.children:
        _build_tree(child, child_node)


def _print_tasks(tasks: list[Task]) -> None:
    if not tasks:
        console.print("No tasks found.")
        return

    table = Table(show_header=True)
    table.add_column("ID", no_wrap=True, overflow="ignore")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Importance")
    table.add_column("Due")
    table.add_column("Title")

    for task in tasks:
        table.add_row(
            str(task.id),
            task.status.value,
            task.priority.value,
            task.importance.value,
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


def _run_graph_action(
    action: Callable[[TaskGraphService], Awaitable[T]],
) -> T:
    try:
        return asyncio.run(
            with_session(lambda session: action(_build_graph_service(session)))
        )
    except DomainError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error


def _parse_repeat_unit(
    value: str | None,
) -> Literal["day", "week", "month", "year"] | None:
    if value is None:
        return None

    value = value.lower()

    allowed = {"day", "week", "month", "year"}

    if value not in allowed:
        raise ValueError("repeat-unit must be one of: day, week, month, year")

    return cast(
        Literal["day", "week", "month", "year"],
        value,
    )


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)
