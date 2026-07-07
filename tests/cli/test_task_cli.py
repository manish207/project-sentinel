import re
from pathlib import Path

from typer.testing import CliRunner

from project_sentinel.cli.app import app

runner = CliRunner()


def _database_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


def _task_id(output: str) -> str:
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        output,
    )
    assert match is not None
    return match.group(0)


def test_task_cli_create_list_complete_and_delete(tmp_path: Path):
    env = {"SENTINEL_DATABASE_URL": _database_url(tmp_path / "sentinel.db")}

    create_result = runner.invoke(app, ["task", "create", "Buy milk"], env=env)
    assert create_result.exit_code == 0
    task_id = _task_id(create_result.output)

    list_result = runner.invoke(app, ["task", "list"], env=env)
    assert list_result.exit_code == 0
    assert task_id in list_result.output
    assert "Buy milk" in list_result.output
    assert "inbox" in list_result.output

    complete_result = runner.invoke(app, ["task", "complete", task_id], env=env)
    assert complete_result.exit_code == 0
    assert f"Completed task {task_id}: Buy milk" in complete_result.output

    completed_list_result = runner.invoke(app, ["task", "list"], env=env)
    assert completed_list_result.exit_code == 0
    assert "completed" in completed_list_result.output

    delete_result = runner.invoke(app, ["task", "delete", task_id], env=env)
    assert delete_result.exit_code == 0
    assert f"Deleted task {task_id}" in delete_result.output

    empty_list_result = runner.invoke(app, ["task", "list"], env=env)
    assert empty_list_result.exit_code == 0
    assert "No tasks found." in empty_list_result.output
