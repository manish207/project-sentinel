from datetime import UTC, date, datetime
from uuid import UUID

from project_sentinel.domain.common import DomainError
from project_sentinel.domain.common import Priority, Status
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
            tags=data.tags or [],
            due_date=data.due_date,
            scheduled_date=data.scheduled_date,
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
        if update.tags is not None:
            task.tags = update.tags
        if update.due_date is not None:
            task.due_date = update.due_date
        if update.scheduled_date is not None:
            task.scheduled_date = update.scheduled_date
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
        return await self._repository.save(task)

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


def parse_priority(value: str) -> Priority:
    try:
        return Priority(value.lower())
    except ValueError as error:
        raise InvalidTaskValueError(f"Invalid priority: {value}") from error


def parse_status(value: str) -> Status:
    try:
        return Status(value.lower())
    except ValueError as error:
        raise InvalidTaskValueError(f"Invalid status: {value}") from error


def today() -> date:
    return datetime.now(UTC).date()
