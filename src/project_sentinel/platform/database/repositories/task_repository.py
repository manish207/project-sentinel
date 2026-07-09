from __future__ import annotations

import builtins
import json
from datetime import UTC, date, datetime
from uuid import UUID
from collections.abc import Iterable

from sqlalchemy import Select, and_, case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from project_sentinel.domain.common import AuditInfo, Priority, Source, Status
from project_sentinel.domain.task import Task, TaskFilters, TaskSort
from project_sentinel.platform.database.models import TaskRecord


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: Task) -> Task:
        self._session.add(self._to_record(task))
        await self._session.commit()
        return task

    async def list(
        self,
        filters: TaskFilters | None = None,
        sort: TaskSort = TaskSort.CREATED,
    ) -> builtins.list[Task]:
        statement = self._apply_sort(
            self._apply_filters(select(TaskRecord), filters), sort
        )
        result = await self._session.execute(statement)
        return [self._to_domain(record) for record in result.scalars()]

    async def search(self, text: str) -> builtins.list[Task]:
        query = f"%{text.lower()}%"
        result = await self._session.execute(
            select(TaskRecord)
            .where(
                or_(
                    TaskRecord.title.ilike(query),
                    TaskRecord.description.ilike(query),
                )
            )
            .order_by(TaskRecord.created_at, TaskRecord.title)
        )
        return [self._to_domain(record) for record in result.scalars()]

    async def get(self, task_id: UUID) -> Task | None:
        record = await self._session.get(TaskRecord, str(task_id))
        if record is None:
            return None
        return self._to_domain(record)

    async def children(
        self,
        parent_task_id: UUID,
    ) -> builtins.list[Task]:
        result = await self._session.execute(
            select(TaskRecord)
            .where(TaskRecord.parent_task_id == str(parent_task_id))
            .order_by(TaskRecord.created_at, TaskRecord.title)
        )

        return [self._to_domain(record) for record in result.scalars()]

    async def root_tasks(self) -> builtins.list[Task]:
        result = await self._session.execute(
            select(TaskRecord)
            .where(TaskRecord.parent_task_id.is_(None))
            .order_by(TaskRecord.created_at, TaskRecord.title)
        )

        return [self._to_domain(record) for record in result.scalars()]

    async def get_many(
        self,
        task_ids: Iterable[UUID],
    ) -> builtins.list[Task]:
        ids = {str(task_id) for task_id in task_ids}

        if not ids:
            return []

        result = await self._session.execute(
            select(TaskRecord).where(TaskRecord.id.in_(ids))
        )

        return [self._to_domain(record) for record in result.scalars()]

    async def save_many(
        self,
        tasks: Iterable[Task],
    ) -> builtins.list[Task]:
        persisted: builtins.list[Task] = []

        for task in tasks:
            record = await self._session.get(TaskRecord, str(task.id))

            if record is None:
                self._session.add(self._to_record(task))
            else:
                self._update_record(record, task)

            persisted.append(task)

        await self._session.commit()

        return persisted

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

    async def delete_many(
        self,
        task_ids: Iterable[UUID],
    ) -> int:
        deleted = 0

        for task_id in set(task_ids):
            record = await self._session.get(TaskRecord, str(task_id))

            if record is None:
                continue

            await self._session.delete(record)
            deleted += 1

        await self._session.commit()

        return deleted

    def _to_record(self, task: Task) -> TaskRecord:
        return TaskRecord(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            source=task.source.value,
            tags=json.dumps(task.tags),
            due_date=task.due_date,
            scheduled_date=task.scheduled_date,
            completed_at=task.completed_at,
            estimated_minutes=task.estimated_minutes,
            actual_minutes=task.actual_minutes,
            parent_task_id=str(task.parent_task_id) if task.parent_task_id else None,
            project_id=str(task.project_id) if task.project_id else None,
            workspace_id=str(task.workspace_id) if task.workspace_id else None,
            created_at=task.audit.created_at,
            updated_at=task.audit.updated_at,
        )

    def _update_record(self, record: TaskRecord, task: Task) -> None:
        record.title = task.title
        record.description = task.description
        record.status = task.status.value
        record.priority = task.priority.value
        record.source = task.source.value
        record.tags = json.dumps(task.tags)
        record.due_date = task.due_date
        record.scheduled_date = task.scheduled_date
        record.completed_at = task.completed_at
        record.estimated_minutes = task.estimated_minutes
        record.actual_minutes = task.actual_minutes
        record.parent_task_id = (
            str(task.parent_task_id) if task.parent_task_id else None
        )
        record.project_id = str(task.project_id) if task.project_id else None
        record.workspace_id = str(task.workspace_id) if task.workspace_id else None
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
            tags=json.loads(record.tags or "[]"),
            due_date=_coerce_date(record.due_date),
            scheduled_date=_coerce_date(record.scheduled_date),
            completed_at=_coerce_optional_datetime(record.completed_at),
            estimated_minutes=record.estimated_minutes,
            actual_minutes=record.actual_minutes,
            parent_task_id=(
                UUID(record.parent_task_id) if record.parent_task_id else None
            ),
            project_id=UUID(record.project_id) if record.project_id else None,
            workspace_id=UUID(record.workspace_id) if record.workspace_id else None,
            audit=AuditInfo(
                created_at=_coerce_datetime(record.created_at),
                updated_at=_coerce_datetime(record.updated_at),
            ),
        )

    def _apply_filters(
        self,
        statement: Select[tuple[TaskRecord]],
        filters: TaskFilters | None,
    ) -> Select[tuple[TaskRecord]]:
        if filters is None:
            return statement

        conditions = []
        if filters.status is not None:
            conditions.append(TaskRecord.status == filters.status.value)
        if filters.priority is not None:
            conditions.append(TaskRecord.priority == filters.priority.value)
        if filters.project_id is not None:
            conditions.append(TaskRecord.project_id == str(filters.project_id))
        if filters.workspace_id is not None:
            conditions.append(TaskRecord.workspace_id == str(filters.workspace_id))
        if filters.due_today is not None:
            conditions.append(TaskRecord.due_date == filters.due_today)
        if filters.overdue_before is not None:
            conditions.append(
                and_(
                    TaskRecord.due_date < filters.overdue_before,
                    TaskRecord.status != Status.COMPLETED.value,
                )
            )
        if filters.completed is not None:
            operator = (
                TaskRecord.status == Status.COMPLETED.value
                if filters.completed
                else TaskRecord.status != Status.COMPLETED.value
            )
            conditions.append(operator)

        if conditions:
            return statement.where(and_(*conditions))
        return statement

    def _apply_sort(
        self,
        statement: Select[tuple[TaskRecord]],
        sort: TaskSort,
    ) -> Select[tuple[TaskRecord]]:
        priority_order = case(
            (TaskRecord.priority == Priority.CRITICAL.value, 0),
            (TaskRecord.priority == Priority.HIGH.value, 1),
            (TaskRecord.priority == Priority.MEDIUM.value, 2),
            (TaskRecord.priority == Priority.LOW.value, 3),
            (TaskRecord.priority == Priority.SOMEDAY.value, 4),
            else_=5,
        )
        match sort:
            case TaskSort.PRIORITY:
                return statement.order_by(priority_order, TaskRecord.created_at)
            case TaskSort.DUE_DATE:
                return statement.order_by(
                    TaskRecord.due_date.is_(None), TaskRecord.due_date
                )
            case TaskSort.ALPHABETICAL:
                return statement.order_by(TaskRecord.title)
            case TaskSort.CREATED:
                return statement.order_by(TaskRecord.created_at, TaskRecord.title)


def _coerce_date(value: date | str | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _coerce_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _coerce_optional_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)
