import asyncio
import pytest
from datetime import UTC, date, datetime, time

from project_sentinel.domain.common import Priority
from project_sentinel.services.task_service import TaskService
from project_sentinel.services.task_scheduler import TaskScheduler
from project_sentinel.services.calendar_service import CalendarService
from tests.services.test_task_service import FakeTaskRepository


class FakeWorkspaceRepository:
    async def get_default(self):
        return None

    async def add(self, ws):
        return ws


@pytest.fixture
def fake_task_repository():
    return FakeTaskRepository()


@pytest.fixture
def fake_workspace_repository():
    return FakeWorkspaceRepository()


@pytest.fixture
def calendar_service(fake_task_repository, fake_workspace_repository):
    task_service = TaskService(fake_task_repository, fake_workspace_repository)
    task_scheduler = TaskScheduler(task_service)
    return CalendarService(task_service, task_scheduler)


def test_get_tasks_for_date_range():
    async def run():
        task_repo = FakeTaskRepository()
        ws_repo = FakeWorkspaceRepository()
        task_service = TaskService(task_repo, ws_repo)
        task_scheduler = TaskScheduler(task_service)
        calendar_service = CalendarService(task_service, task_scheduler)

        task1 = await task_service.create_task("T1")
        task1.start_time = datetime(2026, 7, 13, 10, 0, tzinfo=UTC)
        task1.end_time = datetime(2026, 7, 13, 11, 0, tzinfo=UTC)
        await task_repo.save(task1)

        task2 = await task_service.create_task("T2")
        task2.start_time = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
        task2.end_time = datetime(2026, 7, 14, 11, 0, tzinfo=UTC)
        await task_repo.save(task2)

        tasks = await calendar_service.get_tasks_for_date_range(
            date(2026, 7, 13), date(2026, 7, 13)
        )
        assert len(tasks) == 1
        assert tasks[0].title == "T1"

    asyncio.run(run())


def test_auto_time_block():
    async def run():
        task_repo = FakeTaskRepository()
        ws_repo = FakeWorkspaceRepository()
        task_service = TaskService(task_repo, ws_repo)
        task_scheduler = TaskScheduler(task_service)
        calendar_service = CalendarService(task_service, task_scheduler)

        task1 = await task_service.create_task("T1")
        task1.priority = Priority.CRITICAL
        task1.estimated_minutes = 60
        await task_repo.save(task1)

        task2 = await task_service.create_task("T2")
        task2.priority = Priority.HIGH
        task2.estimated_minutes = 90
        await task_repo.save(task2)

        target_date = date(2026, 7, 13)
        blocked_tasks = await calendar_service.auto_time_block(
            target_date, work_start=time(9, 0), work_end=time(17, 0)
        )

        assert len(blocked_tasks) == 2

        t1 = next(t for t in blocked_tasks if t.title == "T1")
        t2 = next(t for t in blocked_tasks if t.title == "T2")

        assert t1.start_time == datetime(2026, 7, 13, 9, 0, tzinfo=UTC)
        assert t1.end_time == datetime(2026, 7, 13, 10, 0, tzinfo=UTC)

        assert t2.start_time == datetime(2026, 7, 13, 10, 0, tzinfo=UTC)
        assert t2.end_time == datetime(2026, 7, 13, 11, 30, tzinfo=UTC)

    asyncio.run(run())
