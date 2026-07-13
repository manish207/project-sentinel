import asyncio
from typing import Optional
from uuid import UUID

import typer
from rich.console import Console
from rich.tree import Tree

from project_sentinel.services.task_graph_service import TaskGraphService, TaskNode
from project_sentinel.platform.database.repositories.task_repository import (
    SqlAlchemyTaskRepository,
)
from project_sentinel.cli.runtime import with_session
from sqlalchemy.ext.asyncio import AsyncSession

app = typer.Typer(help="Task Graph Visualization commands")
console = Console()


def _build_service(session: AsyncSession) -> TaskGraphService:
    task_repo = SqlAlchemyTaskRepository(session)
    return TaskGraphService(task_repo)


def _run_graph_action(action):
    return asyncio.run(with_session(lambda session: action(_build_service(session))))


@app.callback(invoke_without_command=True)
def show(
    ctx: typer.Context,
    task_id: Optional[UUID] = typer.Option(
        None, "--task", "-t", help="Target task ID to build the graph for"
    ),
    reverse: bool = typer.Option(
        False,
        "--reverse",
        "-r",
        help="Show tasks blocked by this task (instead of what it depends on)",
    ),
    both: bool = typer.Option(
        False, "--both", "-b", help="Show both dependency and blocked-by graphs"
    ),
):
    """Show the interactive dependency graph."""
    if ctx.invoked_subcommand is not None:
        return

    async def _show(service: TaskGraphService):
        def _build_rich_tree(node: TaskNode, parent_tree: Tree):
            for child in node.children:
                status_color = "green" if child.task.status == "completed" else "white"
                child_tree = parent_tree.add(
                    f"[{status_color}]{child.task.title}[/{status_color}] (ID: {child.task.id})"
                )
                _build_rich_tree(child, child_tree)

        def _print_tree(root_node: TaskNode, title: str):
            status_color = (
                "green" if root_node.task.status == "completed" else "bold white"
            )
            tree = Tree(
                f"[bold magenta]{title}[/bold magenta]\n"
                f"[{status_color}]{root_node.task.title}[/{status_color}] (ID: {root_node.task.id})"
            )
            _build_rich_tree(root_node, tree)
            console.print(tree)
            console.print()

        if task_id:
            if not reverse or both:
                dep_tree = await service.dependency_tree(task_id)
                if dep_tree:
                    _print_tree(dep_tree, f"Dependencies for Task {task_id}")
                else:
                    console.print(
                        f"[yellow]No dependencies found for task {task_id}[/yellow]"
                    )

            if reverse or both:
                blocked_tree = await service.blocked_by_tree(task_id)
                if blocked_tree:
                    _print_tree(blocked_tree, f"Tasks Blocked By Task {task_id}")
                else:
                    console.print(
                        f"[yellow]No tasks are blocked by task {task_id}[/yellow]"
                    )
        else:
            if not reverse or both:
                trees = await service.workspace_dependency_trees()
                if trees:
                    console.print("[bold cyan]Workspace Dependency Trees[/bold cyan]")
                    for tree in trees:
                        _print_tree(tree, "Dependency Tree")
                else:
                    console.print(
                        "[yellow]No tasks with dependencies found in the workspace.[/yellow]"
                    )

            if reverse or both:
                blocked_trees = await service.workspace_blocked_by_trees()
                if blocked_trees:
                    console.print("[bold cyan]Workspace Blocked-By Trees[/bold cyan]")
                    for tree in blocked_trees:
                        _print_tree(tree, "Blocked-By Tree")
                elif not both:
                    console.print(
                        "[yellow]No blocking tasks found in the workspace.[/yellow]"
                    )

    _run_graph_action(_show)
