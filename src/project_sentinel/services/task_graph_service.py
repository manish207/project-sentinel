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

    async def dependency_tree(self, task_id: UUID) -> TaskNode | None:
        all_tasks = await self._repository.list()
        task_map = {t.id: t for t in all_tasks}

        def build(curr_id: UUID, visited: set[UUID]) -> TaskNode | None:
            if curr_id in visited:
                return None  # Cycle detected
            task = task_map.get(curr_id)
            if not task:
                return None

            new_visited = visited | {curr_id}
            children_nodes = []
            for dep_id in task.depends_on:
                child = build(dep_id, new_visited)
                if child:
                    children_nodes.append(child)

            return TaskNode(task=task, children=children_nodes)

        return build(task_id, set())

    async def blocked_by_tree(self, task_id: UUID) -> TaskNode | None:
        all_tasks = await self._repository.list()
        task_map = {t.id: t for t in all_tasks}

        # Build reverse index for blockers
        blocked_by_map: dict[UUID, list[UUID]] = {t.id: [] for t in all_tasks}
        for t in all_tasks:
            for dep_id in t.depends_on:
                if dep_id in blocked_by_map:
                    blocked_by_map[dep_id].append(t.id)

        def build(curr_id: UUID, visited: set[UUID]) -> TaskNode | None:
            if curr_id in visited:
                return None
            task = task_map.get(curr_id)
            if not task:
                return None

            new_visited = visited | {curr_id}
            children_nodes = []
            for blocker_id in blocked_by_map.get(curr_id, []):
                child = build(blocker_id, new_visited)
                if child:
                    children_nodes.append(child)

            return TaskNode(task=task, children=children_nodes)

        return build(task_id, set())

    async def workspace_dependency_trees(self) -> list[TaskNode]:
        all_tasks = await self._repository.list()

        # Find tasks that no other task depends on (roots of dependency trees)
        depended_upon = set()
        for t in all_tasks:
            depended_upon.update(t.depends_on)

        roots = [t.id for t in all_tasks if t.id not in depended_upon and t.depends_on]

        trees = []
        for root_id in roots:
            tree = await self.dependency_tree(root_id)
            if tree:
                trees.append(tree)
        return trees

    async def workspace_blocked_by_trees(self) -> list[TaskNode]:
        all_tasks = await self._repository.list()

        # Find tasks that don't depend on anything, but are depended upon by something
        depended_upon = set()
        for t in all_tasks:
            depended_upon.update(t.depends_on)

        roots = [t.id for t in all_tasks if not t.depends_on and t.id in depended_upon]

        trees = []
        for root_id in roots:
            tree = await self.blocked_by_tree(root_id)
            if tree:
                trees.append(tree)
        return trees
