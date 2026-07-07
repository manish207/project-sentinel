import asyncio
from datetime import date
from pathlib import Path

from project_sentinel.domain.common import Priority, Status
from project_sentinel.domain.task import Task, TaskFilters, TaskSort
from project_sentinel.platform.database import get_sessionmaker, init_database
from project_sentinel.platform.database.repositories import SqlAlchemyTaskRepository


def _database_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


def test_sqlalchemy_task_repository_persists_tasks(tmp_path: Path):
    async def run() -> None:
        database_url = _database_url(tmp_path / "sentinel.db")
        await init_database(database_url)
        sessionmaker = get_sessionmaker(database_url)

        async with sessionmaker() as session:
            repository = SqlAlchemyTaskRepository(session)
            created = await repository.add(Task(title="Buy milk"))

        async with sessionmaker() as session:
            repository = SqlAlchemyTaskRepository(session)
            tasks = await repository.list()
            loaded = await repository.get(created.id)

        assert [task.title for task in tasks] == ["Buy milk"]
        assert loaded is not None
        assert loaded.id == created.id

    asyncio.run(run())


def test_sqlalchemy_task_repository_filters_sorts_and_searches(tmp_path: Path):
    async def run() -> None:
        database_url = _database_url(tmp_path / "sentinel.db")
        await init_database(database_url)
        sessionmaker = get_sessionmaker(database_url)

        async with sessionmaker() as session:
            repository = SqlAlchemyTaskRepository(session)
            await repository.add(
                Task(
                    title="Buy milk",
                    description="From the market",
                    priority=Priority.LOW,
                    due_date=date(2026, 7, 7),
                )
            )
            await repository.add(
                Task(
                    title="File taxes",
                    priority=Priority.CRITICAL,
                    due_date=date(2026, 7, 6),
                )
            )

        async with sessionmaker() as session:
            repository = SqlAlchemyTaskRepository(session)
            critical = await repository.list(
                TaskFilters(priority=Priority.CRITICAL),
                TaskSort.PRIORITY,
            )
            overdue = await repository.list(
                TaskFilters(overdue_before=date(2026, 7, 7)),
            )
            search = await repository.search("market")

        assert [task.title for task in critical] == ["File taxes"]
        assert [task.title for task in overdue] == ["File taxes"]
        assert [task.title for task in search] == ["Buy milk"]

    asyncio.run(run())


def test_sqlalchemy_task_repository_updates_and_deletes_tasks(tmp_path: Path):
    async def run() -> None:
        database_url = _database_url(tmp_path / "sentinel.db")
        await init_database(database_url)
        sessionmaker = get_sessionmaker(database_url)

        async with sessionmaker() as session:
            repository = SqlAlchemyTaskRepository(session)
            task = await repository.add(Task(title="Buy milk"))
            task.complete()
            await repository.save(task)

        async with sessionmaker() as session:
            repository = SqlAlchemyTaskRepository(session)
            completed = await repository.get(task.id)
            deleted = await repository.delete(task.id)
            missing = await repository.get(task.id)

        assert completed is not None
        assert completed.status == Status.COMPLETED
        assert deleted is True
        assert missing is None

    asyncio.run(run())
