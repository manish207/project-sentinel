import asyncio
import builtins
from uuid import UUID

import pytest

from project_sentinel.domain.common import Priority, Status
from project_sentinel.domain.task import Task, TaskFilters, TaskSort
from project_sentinel.services import (
    InvalidTaskValueError,
    TaskCreate,
    TaskNotFoundError,
    TaskService,
    TaskUpdate,
)


class FakeTaskRepository:
    def __init__(self) -> None:
        self.tasks: dict[UUID, Task] = {}

    async def add(self, task: Task) -> Task:
        self.tasks[task.id] = task
        return task

    async def list(
        self,
        filters: TaskFilters | None = None,
        sort: TaskSort = TaskSort.CREATED,
    ) -> builtins.list[Task]:
        _ = filters, sort
        return list(self.tasks.values())

    async def search(self, text: str) -> builtins.list[Task]:
        return [
            task
            for task in self.tasks.values()
            if text.lower() in task.title.lower()
            or text.lower() in task.description.lower()
        ]

    async def get(self, task_id: UUID) -> Task | None:
        return self.tasks.get(task_id)

    async def children(
        self,
        parent_task_id: UUID,
    ) -> builtins.list[Task]:
        return [
            task
            for task in self.tasks.values()
            if task.parent_task_id == parent_task_id
        ]

    async def root_tasks(self) -> builtins.list[Task]:
        return [task for task in self.tasks.values() if task.parent_task_id is None]

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
        assert completed.status == Status.COMPLETED

    asyncio.run(run())


def test_task_service_raises_for_missing_task():
    async def run() -> None:
        service = TaskService(FakeTaskRepository())
        missing_id = UUID("00000000-0000-0000-0000-000000000001")

        with pytest.raises(TaskNotFoundError):
            await service.complete_task(missing_id)

    asyncio.run(run())


def test_task_service_updates_and_searches_task():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task = await service.create_task(
            "Buy milk",
            TaskCreate(
                title="Buy milk",
                description="From the corner shop",
                priority=Priority.HIGH,
                tags=["Errand"],
            ),
        )

        updated = await service.update_task(
            task.id,
            TaskUpdate(
                status=Status.PLANNED,
                actual_minutes=5,
            ),
        )

        results = await service.search_tasks("corner")

        assert updated.status == Status.PLANNED
        assert updated.actual_minutes == 5
        assert results == [updated]

    asyncio.run(run())


def test_parse_priority_rejects_invalid_value():
    from project_sentinel.services import parse_priority

    with pytest.raises(InvalidTaskValueError):
        parse_priority("urgent")


def test_task_tree():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        parent = await service.create_task("Parent")

        child1 = await service.create_task(
            "Child 1",
            TaskCreate(
                title="Child 1",
                parent_task_id=parent.id,
            ),
        )

        await service.create_task(
            "Grand Child",
            TaskCreate(
                title="Grand Child",
                parent_task_id=child1.id,
            ),
        )

        tree = await service.task_tree()

        assert len(tree) == 1
        assert tree[0].task.title == "Parent"
        assert len(tree[0].children) == 1
        assert tree[0].children[0].task.title == "Child 1"
        assert len(tree[0].children[0].children) == 1
        assert tree[0].children[0].children[0].task.title == "Grand Child"

    asyncio.run(run())
