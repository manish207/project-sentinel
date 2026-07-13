import asyncio
import builtins
from uuid import UUID
from datetime import date

import pytest
from collections.abc import Iterable

from project_sentinel.domain.common import Priority, Status
from project_sentinel.domain.task import Task, TaskFilters, TaskSort, TaskRepository
from project_sentinel.services import (
    InvalidTaskValueError,
    TaskCreate,
    TaskNotFoundError,
    TaskService,
    TaskUpdate,
    TaskGraphService,
)


class FakeTaskRepository(TaskRepository):
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

    async def get_many(
        self,
        task_ids: Iterable[UUID],
    ) -> builtins.list[Task]:
        return [self.tasks[task_id] for task_id in task_ids if task_id in self.tasks]

    async def save_many(
        self,
        tasks: Iterable[Task],
    ) -> builtins.list[Task]:
        saved: builtins.list[Task] = []

        for task in tasks:
            self.tasks[task.id] = task
            saved.append(task)

        return saved

    async def delete_many(
        self,
        task_ids: Iterable[UUID],
    ) -> int:
        deleted = 0

        for task_id in task_ids:
            if self.tasks.pop(task_id, None) is not None:
                deleted += 1

        return deleted

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

    async def add_dependency(
        self,
        task_id: UUID,
        dependency_id: UUID,
    ) -> None:
        task = self.tasks[task_id]

        if dependency_id not in task.depends_on:
            task.depends_on.append(dependency_id)

    async def remove_dependency(
        self,
        task_id: UUID,
        dependency_id: UUID,
    ) -> None:
        task = self.tasks[task_id]

        if dependency_id in task.depends_on:
            task.depends_on.remove(dependency_id)

    async def ready_tasks(
        self,
    ) -> builtins.list[Task]:
        ready: builtins.list[Task] = []
        for task in self.tasks.values():
            if task.status == Status.COMPLETED:
                continue
            dependencies = [
                self.tasks[dep_id] for dep_id in task.depends_on if dep_id in self.tasks
            ]
            if all(dep.status == Status.COMPLETED for dep in dependencies):
                ready.append(task)
        return ready


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
        graph = TaskGraphService(repository)

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

        tree = await graph.task_tree()

        assert len(tree) == 1
        assert tree[0].task.title == "Parent"
        assert len(tree[0].children) == 1
        assert tree[0].children[0].task.title == "Child 1"
        assert len(tree[0].children[0].children) == 1
        assert tree[0].children[0].children[0].task.title == "Grand Child"

    asyncio.run(run())


def test_recurring_task():
    async def run():
        repo = FakeTaskRepository()
        service = TaskService(repo)

        task = await service.create_task(
            "Backup",
            TaskCreate(
                title="Backup",
                recurring=True,
                repeat_every=1,
                repeat_unit="day",
            ),
        )

        assert task.recurring is True
        assert task.repeat_every == 1
        assert task.repeat_unit == "day"

    asyncio.run(run())


def test_complete_recurring_task_creates_next_occurrence():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task = await service.create_task(
            "Pay Electricity Bill",
            TaskCreate(
                title="Pay Electricity Bill",
                due_date=date(2026, 7, 10),
                recurring=True,
                repeat_every=1,
                repeat_unit="month",
            ),
        )
        # print("recurring =", task.recurring)
        # print("repeat_every =", task.repeat_every)
        # print("repeat_unit =", task.repeat_unit)

        await service.complete_task(task.id)

        tasks = await repository.list()

        assert len(tasks) == 2

        completed = next(t for t in tasks if t.status == Status.COMPLETED)
        next_task = next(t for t in tasks if t.status != Status.COMPLETED)

        assert completed.title == next_task.title
        assert next_task.due_date == date(2026, 8, 10)
        assert next_task.recurring is True

    asyncio.run(run())


def test_add_dependency():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task1 = await service.create_task("Frontend")
        task2 = await service.create_task("Backend")

        await service.add_dependency(
            task1.id,
            task2.id,
        )

        updated = await repository.get(task1.id)

        assert updated is not None
        assert updated.depends_on == [task2.id]

    asyncio.run(run())


def test_remove_dependency():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task1 = await service.create_task("Frontend")
        task2 = await service.create_task("Backend")

        await service.add_dependency(
            task1.id,
            task2.id,
        )

        await service.remove_dependency(
            task1.id,
            task2.id,
        )

        updated = await repository.get(task1.id)

        assert updated is not None
        assert updated.depends_on == []

    asyncio.run(run())


def test_self_dependency_fails():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task = await service.create_task("Backend")

        with pytest.raises(InvalidTaskValueError):
            await service.add_dependency(
                task.id,
                task.id,
            )

    asyncio.run(run())


def test_duplicate_dependency_is_ignored():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task1 = await service.create_task("Frontend")
        task2 = await service.create_task("Backend")

        await service.add_dependency(
            task1.id,
            task2.id,
        )

        await service.add_dependency(
            task1.id,
            task2.id,
        )

        updated = await repository.get(task1.id)

        assert updated is not None
        assert updated.depends_on == [task2.id]

    asyncio.run(run())


def test_ready_tasks_dependency_completed():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        backend = await service.create_task("Backend")
        frontend = await service.create_task("Frontend")

        await service.add_dependency(
            frontend.id,
            backend.id,
        )

        await service.complete_task(backend.id)

        ready = await service.ready_tasks()

        assert any(task.id == frontend.id for task in ready)

    asyncio.run(run())


def test_ready_tasks_dependency_not_completed():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        backend = await service.create_task("Backend")
        frontend = await service.create_task("Frontend")

        await service.add_dependency(
            frontend.id,
            backend.id,
        )

        ready = await service.ready_tasks()

        assert all(task.id != frontend.id for task in ready)

    asyncio.run(run())


def test_ready_tasks_multiple_dependencies():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        api = await service.create_task("API")
        database = await service.create_task("Database")
        auth = await service.create_task("Authentication")

        await service.add_dependency(
            auth.id,
            api.id,
        )

        await service.add_dependency(
            auth.id,
            database.id,
        )

        await service.complete_task(api.id)
        await service.complete_task(database.id)

        ready = await service.ready_tasks()

        assert any(task.id == auth.id for task in ready)

    asyncio.run(run())


def test_ready_tasks_one_dependency_incomplete():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        api = await service.create_task("API")
        database = await service.create_task("Database")
        auth = await service.create_task("Authentication")

        await service.add_dependency(
            auth.id,
            api.id,
        )

        await service.add_dependency(
            auth.id,
            database.id,
        )

        await service.complete_task(api.id)

        ready = await service.ready_tasks()

        assert all(task.id != auth.id for task in ready)

    asyncio.run(run())


def test_dependency_cycle_fails():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task_a = await service.create_task("A")
        task_b = await service.create_task("B")
        task_c = await service.create_task("C")

        await service.add_dependency(
            task_a.id,
            task_b.id,
        )

        await service.add_dependency(
            task_b.id,
            task_c.id,
        )

        with pytest.raises(InvalidTaskValueError):
            await service.add_dependency(
                task_c.id,
                task_a.id,
            )

    asyncio.run(run())


def test_two_task_cycle_fails():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task_a = await service.create_task("A")
        task_b = await service.create_task("B")

        await service.add_dependency(
            task_a.id,
            task_b.id,
        )

        with pytest.raises(InvalidTaskValueError):
            await service.add_dependency(
                task_b.id,
                task_a.id,
            )

    asyncio.run(run())


def test_ready_requires_all_dependencies_completed():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        task_a = await service.create_task("Backend")
        task_b = await service.create_task("Database")
        task_c = await service.create_task("API")

        await service.add_dependency(task_c.id, task_a.id)
        await service.add_dependency(task_c.id, task_b.id)

        ready = await service.ready_tasks()

        assert task_c.id not in {task.id for task in ready}

        await service.complete_task(task_a.id)

        ready = await service.ready_tasks()

        assert task_c.id not in {task.id for task in ready}

        await service.complete_task(task_b.id)

        ready = await service.ready_tasks()

        assert task_c.id in {task.id for task in ready}

    asyncio.run(run())


def test_remove_one_dependency_keeps_remaining_dependencies():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        a = await service.create_task("A")
        b = await service.create_task("B")
        c = await service.create_task("C")

        await service.add_dependency(c.id, a.id)
        await service.add_dependency(c.id, b.id)

        await service.remove_dependency(c.id, a.id)

        deps = await service.dependencies(c.id)

        ids = {task.id for task in deps}

        assert a.id not in ids
        assert b.id in ids

    asyncio.run(run())


def test_long_cycle_detection():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        a = await service.create_task("A")
        b = await service.create_task("B")
        c = await service.create_task("C")
        d = await service.create_task("D")

        await service.add_dependency(a.id, b.id)
        await service.add_dependency(b.id, c.id)
        await service.add_dependency(c.id, d.id)

        with pytest.raises(InvalidTaskValueError):
            await service.add_dependency(d.id, a.id)

    asyncio.run(run())


def test_dependency_persisted():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        a = await service.create_task("Backend")
        b = await service.create_task("Frontend")

        await service.add_dependency(b.id, a.id)

        deps = await service.dependencies(b.id)

        assert len(deps) == 1
        assert deps[0].title == "Backend"

    asyncio.run(run())


""" def test_ready_requires_all_dependencies_completed():
    async def run() -> None:
        repository = FakeTaskRepository()
        service = TaskService(repository)

        backend = await service.create_task("Backend")
        database = await service.create_task("Database")
        api = await service.create_task("API")

        await service.add_dependency(api.id, backend.id)
        await service.add_dependency(api.id, database.id)

        ready = await service.ready_tasks()
        ready_ids = {task.id for task in ready}

        assert api.id not in ready_ids

        await service.complete_task(backend.id)

        ready = await service.ready_tasks()
        ready_ids = {task.id for task in ready}

        assert api.id not in ready_ids

        await service.complete_task(database.id)

        ready = await service.ready_tasks()
        ready_ids = {task.id for task in ready}

        assert api.id in ready_ids

        asyncio.run(run()) """
