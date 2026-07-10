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


def test_task_cli_update_filter_sort_and_search(tmp_path: Path):
    env = {"SENTINEL_DATABASE_URL": _database_url(tmp_path / "sentinel.db")}

    create_result = runner.invoke(
        app,
        [
            "task",
            "create",
            "Buy milk",
            "--description",
            "From the market",
            "--priority",
            "high",
            "--tag",
            "errand",
            "--due-date",
            "2026-07-07",
        ],
        env=env,
    )
    assert create_result.exit_code == 0
    task_id = _task_id(create_result.output)

    update_result = runner.invoke(
        app,
        [
            "task",
            "update",
            task_id,
            "--status",
            "planned",
            "--actual-minutes",
            "5",
        ],
        env=env,
    )
    assert update_result.exit_code == 0

    filtered_result = runner.invoke(
        app,
        ["task", "list", "--priority", "high", "--sort", "due_date"],
        env=env,
    )
    assert filtered_result.exit_code == 0
    assert task_id in filtered_result.output
    assert "2026-07-07" in filtered_result.output

    search_result = runner.invoke(app, ["task", "search", "market"], env=env)
    assert search_result.exit_code == 0
    assert "Buy milk" in search_result.output


def test_tree_command(tmp_path: Path):
    env = {"SENTINEL_DATABASE_URL": _database_url(tmp_path / "sentinel.db")}

    create_result = runner.invoke(
        app,
        ["task", "create", "Parent"],
        env=env,
    )
    assert create_result.exit_code == 0

    parent_id = _task_id(create_result.output)

    create_child = runner.invoke(
        app,
        [
            "task",
            "create",
            "Child",
            "--parent-task-id",
            parent_id,
        ],
        env=env,
    )
    assert create_child.exit_code == 0

    tree_result = runner.invoke(
        app,
        ["task", "tree"],
        env=env,
    )

    assert tree_result.exit_code == 0
    assert "Parent" in tree_result.output
    assert "Child" in tree_result.output
