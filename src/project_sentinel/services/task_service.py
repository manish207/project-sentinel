from uuid import UUID

from project_sentinel.domain.common import DomainError
from project_sentinel.domain.task import Task, TaskRepository


class TaskNotFoundError(DomainError):
    """Raised when a task cannot be found."""


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def create_task(self, title: str) -> Task:
        task = Task(title=title)
        return await self._repository.add(task)

    async def list_tasks(self) -> list[Task]:
        return await self._repository.list()

    async def complete_task(self, task_id: UUID) -> Task:
        task = await self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        task.complete()
        return await self._repository.save(task)

    async def delete_task(self, task_id: UUID) -> None:
        deleted = await self._repository.delete(task_id)
        if not deleted:
            raise TaskNotFoundError(f"Task not found: {task_id}")
