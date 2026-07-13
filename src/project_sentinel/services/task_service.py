from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from calendar import monthrange

from project_sentinel.domain.common import DomainError
from project_sentinel.domain.common import Priority, Status, Importance
from project_sentinel.domain.task import Task, TaskFilters, TaskRepository, TaskSort
from project_sentinel.domain.workspace import Workspace, WorkspaceRepository
from project_sentinel.services.task_inputs import TaskCreate, TaskUpdate


class TaskNotFoundError(DomainError):
    """Raised when a task cannot be found."""


class InvalidTaskValueError(DomainError):
    """Raised when task input is invalid."""


class TaskService:
    def __init__(
        self,
        repository: TaskRepository,
        workspace_repository: WorkspaceRepository | None = None,
    ) -> None:
        self._repository = repository
        self._workspace_repository = workspace_repository

    async def create_task(self, title: str, data: TaskCreate | None = None) -> Task:
        data = data or TaskCreate(title=title)
        workspace_id = data.workspace_id or await self._default_workspace_id()
        task = Task(
            title=title,
            description=data.description,
            priority=data.priority,
            importance=data.importance,
            tags=data.tags or [],
            due_date=data.due_date,
            scheduled_date=data.scheduled_date,
            recurring=data.recurring,
            repeat_every=data.repeat_every,
            repeat_unit=data.repeat_unit,
            estimated_minutes=data.estimated_minutes,
            parent_task_id=data.parent_task_id,
            project_id=data.project_id,
            workspace_id=workspace_id,
        )
        return await self._repository.add(task)

    async def list_tasks(
        self,
        filters: TaskFilters | None = None,
        sort: TaskSort = TaskSort.CREATED,
    ) -> list[Task]:
        return await self._repository.list(filters, sort)

    async def search_tasks(self, text: str) -> list[Task]:
        return await self._repository.search(text)

    async def update_task(self, task_id: UUID, update: TaskUpdate) -> Task:
        task = await self._get_required(task_id)

        if update.title is not None:
            task.title = update.title
        if update.description is not None:
            task.description = update.description
        if update.priority is not None:
            task.priority = update.priority
        if update.importance is not None:
            task.importance = update.importance
        if update.tags is not None:
            task.tags = update.tags
        if update.due_date is not None:
            task.due_date = update.due_date
        if update.scheduled_date is not None:
            task.scheduled_date = update.scheduled_date
        if update.recurring is not None:
            task.recurring = update.recurring
        if update.repeat_every is not None:
            task.repeat_every = update.repeat_every
        if update.repeat_unit is not None:
            task.repeat_unit = update.repeat_unit
        if update.estimated_minutes is not None:
            task.estimated_minutes = update.estimated_minutes
        if update.actual_minutes is not None:
            task.actual_minutes = update.actual_minutes
        if update.parent_task_id is not None:
            task.parent_task_id = update.parent_task_id
        if update.project_id is not None:
            task.project_id = update.project_id
        if update.workspace_id is not None:
            task.workspace_id = update.workspace_id
        if update.status is not None:
            task.change_status(update.status)
        else:
            task.touch()

        if (
            task.due_date is not None
            and task.scheduled_date is not None
            and task.scheduled_date > task.due_date
        ):
            raise InvalidTaskValueError("scheduled_date cannot be after due_date")

        return await self._repository.save(task)

    async def complete_task(self, task_id: UUID) -> Task:
        task = await self._get_required(task_id)

        task.complete()
        await self._repository.save(task)

        # print("1:", task.recurring, task.repeat_every, task.repeat_unit, task.due_date)

        if (
            task.recurring
            and task.repeat_every is not None
            and task.repeat_unit is not None
            and task.due_date is not None
        ):
            # print("2: inside recurring block")

            next_due = _advance_date(
                task.due_date,
                task.repeat_unit,
                task.repeat_every,
            )

            # print("3: next due =", next_due)

            next_task = Task(
                title=task.title,
                description=task.description,
                priority=task.priority,
                tags=list(task.tags),
                due_date=next_due,
                scheduled_date=task.scheduled_date,
                recurring=True,
                repeat_every=task.repeat_every,
                repeat_unit=task.repeat_unit,
                estimated_minutes=task.estimated_minutes,
                parent_task_id=task.parent_task_id,
                project_id=task.project_id,
                workspace_id=task.workspace_id,
            )

            # print("4: adding", next_task.id)

            await self._repository.add(next_task)

            # print("5: added")

        return task

    async def delete_task(self, task_id: UUID) -> None:
        deleted = await self._repository.delete(task_id)
        if not deleted:
            raise TaskNotFoundError(f"Task not found: {task_id}")

    async def _get_required(self, task_id: UUID) -> Task:
        task = await self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return task

    async def _default_workspace_id(self) -> UUID | None:
        if self._workspace_repository is None:
            return None
        workspace = await self._workspace_repository.get_default()
        if workspace is None:
            workspace = await self._workspace_repository.add(
                Workspace(name="Default", is_default=True)
            )
        return workspace.id

    async def create_subtask(
        self,
        parent_task_id: UUID,
        title: str,
    ) -> Task:
        parent = await self._get_required(parent_task_id)

        subtask = Task(
            title=title,
            parent_task_id=parent.id,
            workspace_id=parent.workspace_id,
            project_id=parent.project_id,
            priority=parent.priority,
        )

        return await self._repository.add(subtask)

    async def list_subtasks(
        self,
        parent_task_id: UUID,
    ) -> list[Task]:
        await self._get_required(parent_task_id)
        return await self._repository.children(parent_task_id)

    async def add_dependency(
        self,
        task_id: UUID,
        dependency_id: UUID,
    ) -> None:
        task = await self._get_required(task_id)
        dependency = await self._get_required(dependency_id)

        if task.id == dependency.id:
            raise InvalidTaskValueError("A task cannot depend on itself")

        if dependency.id in task.depends_on:
            return

        await self._repository.add_dependency(
            task.id,
            dependency.id,
        )

    async def remove_dependency(
        self,
        task_id: UUID,
        dependency_id: UUID,
    ) -> None:
        await self._get_required(task_id)
        await self._get_required(dependency_id)

        await self._repository.remove_dependency(
            task_id,
            dependency_id,
        )

    async def ready_tasks(self) -> list[Task]:
        return await self._repository.ready_tasks()

    async def dependencies(
        self,
        task_id: UUID,
    ) -> list[Task]:
        task = await self._get_required(task_id)

        return await self._repository.get_many(
            task.depends_on,
        )


def parse_priority(value: str) -> Priority:
    try:
        return Priority(value.lower())
    except ValueError as error:
        raise InvalidTaskValueError(f"Invalid priority: {value}") from error


def parse_importance(value: str) -> Importance:
    try:
        return Importance(value.lower())
    except ValueError as error:
        raise InvalidTaskValueError(f"Invalid importance: {value}") from error


def parse_status(value: str) -> Status:
    try:
        return Status(value.lower())
    except ValueError as error:
        raise InvalidTaskValueError(f"Invalid status: {value}") from error


def today() -> date:
    return datetime.now(UTC).date()


def _advance_date(
    due_date: date,
    repeat_unit: str,
    interval: int,
) -> date:
    if repeat_unit == "day":
        return due_date + timedelta(days=interval)

    if repeat_unit == "week":
        return due_date + timedelta(weeks=interval)

    if repeat_unit == "month":
        month = due_date.month - 1 + interval
        year = due_date.year + month // 12
        month = month % 12 + 1

        day = min(
            due_date.day,
            monthrange(year, month)[1],
        )

        return date(year, month, day)

    year = due_date.year + interval

    try:
        return due_date.replace(year=year)
    except ValueError:
        return due_date.replace(
            year=year,
            month=2,
            day=28,
        )
