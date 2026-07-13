import asyncio
from datetime import UTC, datetime, timedelta

from project_sentinel.domain.common import Priority, Status, Importance
from project_sentinel.domain.task import Task
from project_sentinel.services.task_service import TaskService
from project_sentinel.services.task_scheduler import TaskScheduler
from tests.services.test_task_service import FakeTaskRepository


def test_scheduler_scoring() -> None:
    async def run() -> None:
        repo = FakeTaskRepository()
        service = TaskService(repo)
        scheduler = TaskScheduler(service)

        # 1. Blocked task (depends on uncompleted task)
        dep_task = Task(
            title="Dependency Task",
            status=Status.INBOX,
        )
        await repo.add(dep_task)

        blocked_task = Task(
            title="Blocked Task",
            status=Status.INBOX,
            priority=Priority.CRITICAL,
            importance=Importance.HIGH,
            depends_on=[dep_task.id],
        )
        await repo.add(blocked_task)

        # 2. Critical priority + High importance task
        critical_task = Task(
            title="Critical Task",
            status=Status.INBOX,
            priority=Priority.CRITICAL,
            importance=Importance.HIGH,
        )
        await repo.add(critical_task)

        # 3. Medium priority + Low importance task
        medium_task = Task(
            title="Medium Task",
            status=Status.INBOX,
            priority=Priority.MEDIUM,
            importance=Importance.LOW,
        )
        await repo.add(medium_task)

        # 4. Overdue task
        overdue_task = Task(
            title="Overdue Task",
            status=Status.INBOX,
            priority=Priority.LOW,
            importance=Importance.LOW,
            due_date=datetime.now(UTC).date() - timedelta(days=2),
        )
        await repo.add(overdue_task)

        # Get next tasks
        next_tasks = await scheduler.next_tasks()

        # The blocked task should not be in the list of ready tasks (or its dependency is inbox, i.e., not completed)
        titles = [st.task.title for st in next_tasks]
        assert "Blocked Task" not in titles
        assert "Dependency Task" in titles

        # Critical task should be first because priority=CRITICAL (+100) and importance=HIGH (+50) = 150
        assert next_tasks[0].task.title == "Critical Task"
        assert next_tasks[0].score == 150.0

        # Overdue task should have overdue bonus (80 + 2*10 = 100) + low priority (5) + low importance (10) = 115
        overdue_st = next(st for st in next_tasks if st.task.title == "Overdue Task")
        assert overdue_st.score == 115.0
        assert "Overdue by 2 days" in overdue_st.reason

    asyncio.run(run())
