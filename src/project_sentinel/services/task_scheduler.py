from dataclasses import dataclass
from datetime import UTC, datetime
from project_sentinel.domain.common import Priority, Status, Importance
from project_sentinel.domain.task import Task
from project_sentinel.services.task_service import TaskService


@dataclass(slots=True)
class ScheduledTask:
    task: Task
    score: float
    reason: str


class TaskScheduler:
    def __init__(self, service: TaskService):
        self._service = service

    async def next_tasks(
        self,
        limit: int = 10,
    ) -> list[ScheduledTask]:
        # 1. Fetch ready tasks
        tasks = await self._service.ready_tasks()

        # 2. Filter out completed/cancelled/archived tasks
        active_statuses = {
            Status.INBOX,
            Status.PLANNED,
            Status.READY,
            Status.IN_PROGRESS,
            Status.WAITING,
            Status.BLOCKED,
        }
        active_tasks = [t for t in tasks if t.status in active_statuses]

        today_val = datetime.now(UTC).date()
        scheduled_list: list[ScheduledTask] = []

        for task in active_tasks:
            score = 0.0
            reasons = []

            # Priority Score
            if task.priority == Priority.CRITICAL:
                score += 100.0
                reasons.append("Critical priority (+100)")
            elif task.priority == Priority.HIGH:
                score += 50.0
                reasons.append("High priority (+50)")
            elif task.priority == Priority.MEDIUM:
                score += 20.0
                reasons.append("Medium priority (+20)")
            elif task.priority == Priority.LOW:
                score += 5.0
                reasons.append("Low priority (+5)")
            elif task.priority == Priority.SOMEDAY:
                score += 1.0
                reasons.append("Someday priority (+1)")

            # Importance Score
            if task.importance == Importance.HIGH:
                score += 50.0
                reasons.append("High importance (+50)")
            elif task.importance == Importance.LOW:
                score += 10.0
                reasons.append("Low importance (+10)")

            # Due Date Score
            if task.due_date is not None:
                if task.due_date < today_val:
                    days_overdue = (today_val - task.due_date).days
                    overdue_bonus = min(100.0, 80.0 + (days_overdue * 10.0))
                    score += overdue_bonus
                    reasons.append(
                        f"Overdue by {days_overdue} days (+{overdue_bonus:.0f})"
                    )
                elif task.due_date == today_val:
                    score += 70.0
                    reasons.append("Due today (+70)")
                else:
                    days_until = (task.due_date - today_val).days
                    if days_until == 1:
                        score += 40.0
                        reasons.append("Due tomorrow (+40)")
                    elif days_until <= 7:
                        score += 20.0
                        reasons.append(f"Due in {days_until} days (+20)")
                    elif days_until <= 30:
                        score += 10.0
                        reasons.append(f"Due in {days_until} days (+10)")

            # Scheduled Date Score
            if task.scheduled_date is not None:
                if task.scheduled_date <= today_val:
                    score += 30.0
                    reasons.append("Scheduled for today or earlier (+30)")

            reason_str = (
                ", ".join(reasons) if reasons else "No specific scoring triggers"
            )
            scheduled_list.append(
                ScheduledTask(
                    task=task,
                    score=score,
                    reason=reason_str,
                )
            )

        # Sort by score descending, then by due date ascending (earliest first), then alphabetically
        def sort_key(st: ScheduledTask) -> tuple[float, float, str]:
            # due date sorting: None due dates last
            due_val = (
                (st.task.due_date - today_val).days if st.task.due_date else 999999
            )
            return (-st.score, due_val, st.task.title.lower())

        scheduled_list.sort(key=sort_key)
        return scheduled_list[:limit]
