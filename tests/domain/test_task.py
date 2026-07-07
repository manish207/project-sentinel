import pytest

from pydantic import ValidationError

from project_sentinel.domain.common import Priority, Source, Status
from project_sentinel.domain.task import InvalidTaskTransitionError, Task


def test_task_creation_defaults():
    task = Task(title="Buy milk")

    assert task.title == "Buy milk"
    assert task.description == ""
    assert task.status == Status.INBOX
    assert task.priority == Priority.MEDIUM
    assert task.source == Source.MANUAL
    assert task.project_id is None


def test_task_complete_updates_status():
    task = Task(title="Buy milk")

    task.complete()

    assert task.status == Status.COMPLETED
    assert task.completed_at is not None


def test_task_normalizes_tags():
    task = Task(title="Buy milk", tags=["Home", " home ", "", "Errand"])

    assert task.tags == ["home", "errand"]


def test_task_rejects_scheduled_after_due_date():
    with pytest.raises(ValidationError):
        Task(
            title="Buy milk",
            scheduled_date="2026-07-08",
            due_date="2026-07-07",
        )


def test_task_rejects_invalid_status_transition():
    task = Task(title="Buy milk")
    task.complete()

    with pytest.raises(InvalidTaskTransitionError):
        task.change_status(Status.IN_PROGRESS)
