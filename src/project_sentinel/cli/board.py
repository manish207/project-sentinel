import asyncio

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from project_sentinel.domain.common import Status
from project_sentinel.services.task_service import TaskService
from project_sentinel.platform.database.repositories.task_repository import (
    SqlAlchemyTaskRepository,
)
from project_sentinel.platform.database.repositories.workspace_repository import (
    SqlAlchemyWorkspaceRepository,
)
from project_sentinel.cli.runtime import with_session
from sqlalchemy.ext.asyncio import AsyncSession

app = typer.Typer(help="Kanban Board commands")
console = Console()


def _build_service(session: AsyncSession) -> TaskService:
    task_repo = SqlAlchemyTaskRepository(session)
    workspace_repo = SqlAlchemyWorkspaceRepository(session)
    return TaskService(task_repo, workspace_repo)


def _run_board_action(action):
    return asyncio.run(with_session(lambda session: action(_build_service(session))))


@app.callback(invoke_without_command=True)
def show(ctx: typer.Context):
    """Show the Kanban board."""
    if ctx.invoked_subcommand is not None:
        return

    async def _show(service: TaskService):
        from project_sentinel.domain.task.models import Task

        tasks = await service.list_tasks()

        # Group tasks by status
        columns_data: dict[Status, list[Task]] = {
            Status.INBOX: [],
            Status.PLANNED: [],
            Status.READY: [],
            Status.IN_PROGRESS: [],
            Status.WAITING: [],
            Status.COMPLETED: [],
        }

        for task in tasks:
            if task.status in columns_data:
                columns_data[task.status].append(task)

        table = Table(
            title="Kanban Board",
            show_header=True,
            header_style="bold magenta",
            expand=True,
            title_style="bold cyan",
        )

        # Define Columns
        status_order = [
            Status.INBOX,
            Status.PLANNED,
            Status.READY,
            Status.IN_PROGRESS,
            Status.WAITING,
            Status.COMPLETED,
        ]

        for status in status_order:
            table.add_column(status.value.replace("_", " ").title(), justify="left")

        # Build Panels for each status column
        row_renderables = []
        for status in status_order:
            status_tasks = columns_data[status]
            panels = []
            for task in status_tasks:
                # Use Text with fold overflow to ensure long titles wrap and don't truncate
                title_text = Text(task.title, overflow="fold")
                panels.append(
                    Panel(
                        title_text,
                        title=f"[{task.priority.value[:1].upper()}]",
                        expand=True,
                    )
                )

            if panels:
                row_renderables.append(Group(*panels))
            else:
                row_renderables.append(Text(" ", justify="center"))

        table.add_row(*row_renderables)
        console.print(table)

    _run_board_action(_show)
