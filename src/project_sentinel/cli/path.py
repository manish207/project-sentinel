import asyncio
from typing import Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.tree import Tree

from project_sentinel.domain.task.models import Task
from project_sentinel.services.task_graph_service import TaskGraphService
from project_sentinel.platform.database.repositories.task_repository import (
    SqlAlchemyTaskRepository,
)
from project_sentinel.cli.runtime import with_session
from sqlalchemy.ext.asyncio import AsyncSession

app = typer.Typer(help="Critical Path Analysis commands")
console = Console()


def _build_service(session: AsyncSession) -> TaskGraphService:
    task_repo = SqlAlchemyTaskRepository(session)
    return TaskGraphService(task_repo)


def _run_path_action(action):
    return asyncio.run(with_session(lambda session: action(_build_service(session))))


@app.callback(invoke_without_command=True)
def show(
    ctx: typer.Context,
    task_id: Optional[UUID] = typer.Option(
        None, "--task", "-t", help="Target task ID to analyze"
    ),
):
    """Show the critical path(s)."""
    if ctx.invoked_subcommand is not None:
        return

    async def _show(service: TaskGraphService):
        if task_id:
            path = await service.get_critical_path(task_id)
            if not path:
                console.print(
                    f"[yellow]No critical path found for task {task_id}[/yellow]"
                )
                return

            tree = Tree(f"[bold magenta]Critical Path for {task_id}[/bold magenta]")
            _build_rich_tree(tree, path)
            console.print(tree)
        else:
            paths = await service.get_longest_critical_paths()
            if not paths:
                console.print(
                    "[yellow]No tasks with dependencies found in the workspace.[/yellow]"
                )
                return

            console.print(
                f"[bold cyan]Found {len(paths)} longest critical path(s)[/bold cyan]"
            )
            for i, path in enumerate(paths, 1):
                tree = Tree(f"[bold magenta]Critical Path #{i}[/bold magenta]")
                _build_rich_tree(tree, path)
                console.print(tree)
                console.print()

    def _build_rich_tree(tree: Tree, path: list[Task]):
        current_node = tree
        for task in path:
            weight = (
                task.estimated_minutes if task.estimated_minutes is not None else 60
            )
            task_label = f"[bold]{task.title}[/bold] (ID: {task.id}) - [yellow]{weight} mins[/yellow]"
            current_node = current_node.add(task_label)

    _run_path_action(_show)
