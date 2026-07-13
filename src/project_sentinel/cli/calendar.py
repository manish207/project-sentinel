import asyncio
from datetime import UTC, datetime, timedelta
from typing import Annotated
import typer
from rich.console import Console
from rich.table import Table

from project_sentinel.services.calendar_service import CalendarService
from project_sentinel.services.task_service import TaskService
from project_sentinel.services.task_scheduler import TaskScheduler
from project_sentinel.platform.database.repositories.task_repository import (
    SqlAlchemyTaskRepository,
)
from project_sentinel.platform.database.repositories.workspace_repository import (
    SqlAlchemyWorkspaceRepository,
)
from project_sentinel.cli.runtime import with_session
from sqlalchemy.ext.asyncio import AsyncSession

app = typer.Typer(help="Calendar and time-blocking commands")
console = Console()


def _build_service(session: AsyncSession) -> CalendarService:
    task_repo = SqlAlchemyTaskRepository(session)
    workspace_repo = SqlAlchemyWorkspaceRepository(session)
    task_service = TaskService(task_repo, workspace_repo)
    task_scheduler = TaskScheduler(task_service)
    return CalendarService(task_service, task_scheduler)


def _run_calendar_action(action):
    return asyncio.run(with_session(lambda session: action(_build_service(session))))


@app.command()
def today():
    """Show tasks for today."""

    async def _today(service: CalendarService):
        today_date = datetime.now(UTC).date()
        tasks = await service.get_tasks_for_date_range(today_date, today_date)

        table = Table(title=f"Calendar - Today ({today_date})")
        table.add_column("Time Block")
        table.add_column("Title")
        table.add_column("Status")

        for task in tasks:
            time_str = "Not Set"
            if task.start_time and task.end_time:
                time_str = f"{task.start_time.strftime('%H:%M')} - {task.end_time.strftime('%H:%M')}"
            table.add_row(
                time_str,
                task.title,
                task.status.value,
            )
        console.print(table)

    _run_calendar_action(_today)


@app.command()
def tomorrow():
    """Show tasks for tomorrow."""

    async def _tomorrow(service: CalendarService):
        tomorrow_date = datetime.now(UTC).date() + timedelta(days=1)
        tasks = await service.get_tasks_for_date_range(tomorrow_date, tomorrow_date)

        table = Table(title=f"Calendar - Tomorrow ({tomorrow_date})")
        table.add_column("Time Block")
        table.add_column("Title")
        table.add_column("Status")

        for task in tasks:
            time_str = "Not Set"
            if task.start_time and task.end_time:
                time_str = f"{task.start_time.strftime('%H:%M')} - {task.end_time.strftime('%H:%M')}"
            table.add_row(time_str, task.title, task.status.value)
        console.print(table)

    _run_calendar_action(_tomorrow)


@app.command()
def week():
    """Show tasks for the next 7 days."""

    async def _week(service: CalendarService):
        today_date = datetime.now(UTC).date()
        end_date = today_date + timedelta(days=7)
        tasks = await service.get_tasks_for_date_range(today_date, end_date)

        table = Table(title="Calendar - Next 7 Days")
        table.add_column("Date")
        table.add_column("Time Block")
        table.add_column("Title")

        for task in tasks:
            date_str = (
                task.start_time.strftime("%Y-%m-%d") if task.start_time else "Unknown"
            )
            time_str = "Not Set"
            if task.start_time and task.end_time:
                time_str = f"{task.start_time.strftime('%H:%M')} - {task.end_time.strftime('%H:%M')}"
            table.add_row(date_str, time_str, task.title)
        console.print(table)

    _run_calendar_action(_week)


@app.command()
def block(
    date_str: Annotated[
        str | None, typer.Option("--date", help="Date to block (YYYY-MM-DD)")
    ] = None,
    start_time: Annotated[
        str, typer.Option("--start", help="Work start time (HH:MM)")
    ] = "09:00",
    end_time: Annotated[
        str, typer.Option("--end", help="Work end time (HH:MM)")
    ] = "17:00",
):
    """Automatically time block tasks for a specific date."""

    async def _block(service: CalendarService):
        target_date = (
            datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_str
            else datetime.now(UTC).date()
        )
        w_start = datetime.strptime(start_time, "%H:%M").time()
        w_end = datetime.strptime(end_time, "%H:%M").time()

        blocked_tasks = await service.auto_time_block(target_date, w_start, w_end)

        if not blocked_tasks:
            console.print(
                "No tasks could be time-blocked (maybe nothing is ready or all slots are taken)."
            )
            return

        console.print(
            f"[green]Successfully time-blocked {len(blocked_tasks)} tasks for {target_date}![/green]"
        )
        for task in blocked_tasks:
            t_start = task.start_time.strftime("%H:%M") if task.start_time else "??"
            t_end = task.end_time.strftime("%H:%M") if task.end_time else "??"
            console.print(f"  {t_start} - {t_end}: {task.title}")

    _run_calendar_action(_block)
