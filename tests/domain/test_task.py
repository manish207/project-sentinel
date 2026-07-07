from project_sentinel.domain.common import Priority, Source, Status
from project_sentinel.domain.task import Task


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
