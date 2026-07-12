from dataclasses import dataclass
from uuid import UUID

from project_sentinel.domain.task import Task, TaskRepository


@dataclass(slots=True)
class TaskNode:
    task: Task
    children: list["TaskNode"]


class TaskGraphService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def task_tree(self) -> list[TaskNode]:
        roots = await self._repository.root_tasks()
        return [await self._build_tree(task) for task in roots]

    async def _build_tree(self, task: Task) -> TaskNode:
        children = await self._repository.children(task.id)
        return TaskNode(
            task=task,
            children=[await self._build_tree(child) for child in children],
        )

    async def children(
        self,
        parent_id: UUID,
    ) -> list[Task]:
        return await self._repository.children(parent_id)
