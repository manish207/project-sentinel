from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.domain.common import AuditInfo, Priority, Source, Status
from project_sentinel.domain.task import Task
from project_sentinel.platform.database.models import TaskRecord


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: Task) -> Task:
        self._session.add(self._to_record(task))
        await self._session.commit()
        return task

    async def list(self) -> list[Task]:
        result = await self._session.execute(
            select(TaskRecord).order_by(TaskRecord.created_at, TaskRecord.title)
        )
        return [self._to_domain(record) for record in result.scalars()]

    async def get(self, task_id: UUID) -> Task | None:
        record = await self._session.get(TaskRecord, str(task_id))
        if record is None:
            return None
        return self._to_domain(record)

    async def save(self, task: Task) -> Task:
        record = await self._session.get(TaskRecord, str(task.id))
        if record is None:
            self._session.add(self._to_record(task))
        else:
            self._update_record(record, task)
        await self._session.commit()
        return task

    async def delete(self, task_id: UUID) -> bool:
        record = await self._session.get(TaskRecord, str(task_id))
        if record is None:
            return False
        await self._session.delete(record)
        await self._session.commit()
        return True

    def _to_record(self, task: Task) -> TaskRecord:
        return TaskRecord(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            source=task.source.value,
            project_id=str(task.project_id) if task.project_id else None,
            created_at=task.audit.created_at,
            updated_at=task.audit.updated_at,
        )

    def _update_record(self, record: TaskRecord, task: Task) -> None:
        record.title = task.title
        record.description = task.description
        record.status = task.status.value
        record.priority = task.priority.value
        record.source = task.source.value
        record.project_id = str(task.project_id) if task.project_id else None
        record.created_at = task.audit.created_at
        record.updated_at = task.audit.updated_at

    def _to_domain(self, record: TaskRecord) -> Task:
        return Task(
            id=UUID(record.id),
            title=record.title,
            description=record.description,
            status=Status(record.status),
            priority=Priority(record.priority),
            source=Source(record.source),
            project_id=UUID(record.project_id) if record.project_id else None,
            audit=AuditInfo(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
        )
