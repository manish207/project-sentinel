import asyncio
from typing import Union

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from project_sentinel.domain.common import Importance, Priority, Status
from project_sentinel.domain.task.models import Task
from project_sentinel.services.task_service import TaskService
from project_sentinel.platform.database.repositories.task_repository import (
    SqlAlchemyTaskRepository,
)
from project_sentinel.platform.database.repositories.workspace_repository import (
    SqlAlchemyWorkspaceRepository,
)
from project_sentinel.cli.runtime import with_session
from sqlalchemy.ext.asyncio import AsyncSession

app = typer.Typer(help="Eisenhower Matrix commands")
console = Console()


def _build_service(session: AsyncSession) -> TaskService:
    task_repo = SqlAlchemyTaskRepository(session)
    workspace_repo = SqlAlchemyWorkspaceRepository(session)
    return TaskService(task_repo, workspace_repo)


def _run_matrix_action(action):
    return asyncio.run(with_session(lambda session: action(_build_service(session))))


@app.callback(invoke_without_command=True)
def show(ctx: typer.Context):
    """Show the Eisenhower Matrix."""
    if ctx.invoked_subcommand is not None:
        return

    async def _show(service: TaskService):
        tasks = await service.list_tasks()

        q1: list[Task] = []
        q2: list[Task] = []
        q3: list[Task] = []
        q4: list[Task] = []

        urgent_priorities = {Priority.CRITICAL, Priority.HIGH}

        for task in tasks:
            if task.status in {Status.COMPLETED, Status.ARCHIVED, Status.CANCELLED}:
                continue

            is_important = task.importance == Importance.HIGH
            is_urgent = task.priority in urgent_priorities

            if is_important and is_urgent:
                q1.append(task)
            elif is_important and not is_urgent:
                q2.append(task)
            elif not is_important and is_urgent:
                q3.append(task)
            else:
                q4.append(task)

        table = Table(
            title="Eisenhower Matrix",
            show_header=True,
            header_style="bold magenta",
            expand=True,
            title_style="bold cyan",
        )

        table.add_column("Urgent", justify="left", ratio=1)
        table.add_column("Not Urgent", justify="left", ratio=1)

        def _build_group(task_list: list[Task], color: str) -> Union[Group, Text]:
            panels = []
            for task in task_list:
                title_text = Text(task.title, overflow="fold")
                panels.append(
                    Panel(
                        title_text,
                        title=f"[{task.priority.value[:1].upper()}]",
                        border_style=color,
                    )
                )
            if panels:
                return Group(*panels)
            return Text(" ", justify="center")

        table.add_row(
            Panel(
                _build_group(q1, "red"),
                title="[bold red]Q1: Do First (Important & Urgent)[/bold red]",
                expand=True,
                border_style="red",
            ),
            Panel(
                _build_group(q2, "blue"),
                title="[bold blue]Q2: Schedule (Important & Not Urgent)[/bold blue]",
                expand=True,
                border_style="blue",
            ),
        )

        table.add_row(
            Panel(
                _build_group(q3, "yellow"),
                title="[bold yellow]Q3: Delegate (Not Important & Urgent)[/bold yellow]",
                expand=True,
                border_style="yellow",
            ),
            Panel(
                _build_group(q4, "green"),
                title="[bold green]Q4: Don't Do (Not Important & Not Urgent)[/bold green]",
                expand=True,
                border_style="green",
            ),
        )

        console.print(table)

    _run_matrix_action(_show)
