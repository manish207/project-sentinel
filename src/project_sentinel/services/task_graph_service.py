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

    async def get_critical_path(self, target_task_id: UUID) -> list[Task]:
        target_task = await self._repository.get(target_task_id)
        if not target_task:
            return []
        all_tasks = await self._repository.list()
        task_map = {t.id: t for t in all_tasks}

        memo: dict[UUID, tuple[int, list[Task]]] = {}

        def dfs(task_id: UUID) -> tuple[int, list[Task]]:
            if task_id in memo:
                return memo[task_id]
            task = task_map.get(task_id)
            if not task:
                return (0, [])

            weight = (
                task.estimated_minutes if task.estimated_minutes is not None else 60
            )

            if not task.depends_on:
                res = (weight, [task])
                memo[task_id] = res
                return res

            max_val = -1
            best_path: list[Task] = []

            for dep_id in task.depends_on:
                if dep_id in task_map:
                    val, path = dfs(dep_id)
                    if val > max_val:
                        max_val = val
                        best_path = path

            res = (weight + max_val, best_path + [task])
            memo[task_id] = res
            return res

        _, path = dfs(target_task_id)
        return path

    async def get_longest_critical_paths(self) -> list[list[Task]]:
        all_tasks = await self._repository.list()
        task_map = {t.id: t for t in all_tasks}

        memo: dict[UUID, tuple[int, list[Task]]] = {}

        def dfs(task_id: UUID) -> tuple[int, list[Task]]:
            if task_id in memo:
                return memo[task_id]
            task = task_map.get(task_id)
            if not task:
                return (0, [])

            weight = (
                task.estimated_minutes if task.estimated_minutes is not None else 60
            )

            if not task.depends_on:
                res = (weight, [task])
                memo[task_id] = res
                return res

            max_val = -1
            best_path: list[Task] = []

            for dep_id in task.depends_on:
                if dep_id in task_map:
                    val, path = dfs(dep_id)
                    if val > max_val:
                        max_val = val
                        best_path = path

            res = (weight + max_val, best_path + [task])
            memo[task_id] = res
            return res

        max_overall = -1
        best_overall_paths = []

        for task in all_tasks:
            val, path = dfs(task.id)
            if val > max_overall:
                max_overall = val
                best_overall_paths = [path]
            elif val == max_overall and max_overall != -1:
                # Append if it's not the exact same path (could just check for unique paths)
                if path not in best_overall_paths:
                    best_overall_paths.append(path)

        return best_overall_paths
