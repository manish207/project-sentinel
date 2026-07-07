import asyncio
from uuid import UUID

import pytest

from project_sentinel.domain.task import Task
from project_sentinel.services import TaskNotFoundError, TaskService


class FakeTaskRepository:
    def __init__(self) -> None:
        self.tasks: dict[UUID, Task] = {}

    async def add(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    async def list(self) -> list[Task]:
        return list(self.tasks.values())

    async def get(self, task_id: UUID) -> Task | None:
        return self.tasks.get(task_id)

    async def save(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    async def delete(self, task_id: UUID) -> bool:
        return self.tasks.pop(task_id, None) is not None


def test_task_service_creates_and_completes_task():
    async def run() -> None:
        service = TaskService(FakeTaskRepository())

        task = await service.create_task("Buy milk")
        completed = await service.complete_task(task.id)

        assert completed.id == task.id
        assert completed.status == "completed"

    asyncio.run(run())


def test_task_service_raises_for_missing_task():
    async def run() -> None:
        service = TaskService(FakeTaskRepository())
        missing_id = UUID("00000000-0000-0000-0000-000000000001")

        with pytest.raises(TaskNotFoundError):
            await service.complete_task(missing_id)

    asyncio.run(run())
