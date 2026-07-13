from datetime import UTC, date, datetime, time, timedelta
from typing import Sequence

from project_sentinel.domain.common import Status
from project_sentinel.domain.task import TaskFilters, TaskSort
from project_sentinel.domain.task.models import Task
from project_sentinel.services.task_service import TaskService
from project_sentinel.services.task_scheduler import TaskScheduler


class CalendarService:
    def __init__(self, task_service: TaskService, task_scheduler: TaskScheduler):
        self._service = task_service
        self._scheduler = task_scheduler

    async def get_tasks_for_date_range(
        self, start_date: date, end_date: date
    ) -> Sequence[Task]:
        start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_dt = datetime.combine(end_date, time.max, tzinfo=UTC)

        filters = TaskFilters(
            time_range_start=start_dt,
            time_range_end=end_dt,
            completed=False,
        )
        return await self._service.list_tasks(filters=filters, sort=TaskSort.DUE_DATE)

    async def auto_time_block(
        self,
        target_date: date,
        work_start: time = time(hour=9, minute=0),
        work_end: time = time(hour=17, minute=0),
    ) -> list[Task]:
        """
        Automatically schedules top tasks for the target date into available time blocks.
        """
        scheduled_tasks = await self._scheduler.next_tasks(limit=20)
        if not scheduled_tasks:
            return []

        current_time = datetime.combine(target_date, work_start, tzinfo=UTC)
        end_time = datetime.combine(target_date, work_end, tzinfo=UTC)

        updated_tasks: list[Task] = []

        for st in scheduled_tasks:
            task = st.task
            if task.start_time is not None or task.status == Status.COMPLETED:
                continue

            duration_mins = task.estimated_minutes or 30
            duration = timedelta(minutes=duration_mins)

            if current_time + duration > end_time:
                break

            task.start_time = current_time
            task.end_time = current_time + duration
            task.scheduled_date = target_date

            await self._service._repository.save(task)
            updated_tasks.append(task)

            current_time += duration

        return updated_tasks
