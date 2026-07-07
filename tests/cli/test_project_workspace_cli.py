import re
from pathlib import Path

from typer.testing import CliRunner

from project_sentinel.cli.app import app

runner = CliRunner()


def _database_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


def _entity_id(output: str) -> str:
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        output,
    )
    assert match is not None
    return match.group(0)


def test_workspace_cli_crud(tmp_path: Path):
    env = {"SENTINEL_DATABASE_URL": _database_url(tmp_path / "sentinel.db")}

    create_result = runner.invoke(
        app,
        ["workspace", "create", "Personal", "--default"],
        env=env,
    )
    assert create_result.exit_code == 0
    workspace_id = _entity_id(create_result.output)

    list_result = runner.invoke(app, ["workspace", "list"], env=env)
    assert list_result.exit_code == 0
    assert "Personal" in list_result.output
    assert "yes" in list_result.output

    update_result = runner.invoke(
        app,
        ["workspace", "update", workspace_id, "--name", "Home"],
        env=env,
    )
    assert update_result.exit_code == 0
    assert "Home" in update_result.output

    delete_result = runner.invoke(app, ["workspace", "delete", workspace_id], env=env)
    assert delete_result.exit_code == 0


def test_project_cli_crud(tmp_path: Path):
    env = {"SENTINEL_DATABASE_URL": _database_url(tmp_path / "sentinel.db")}

    create_result = runner.invoke(app, ["project", "create", "Sentinel"], env=env)
    assert create_result.exit_code == 0
    project_id = _entity_id(create_result.output)

    list_result = runner.invoke(app, ["project", "list"], env=env)
    assert list_result.exit_code == 0
    assert "Sentinel" in list_result.output

    update_result = runner.invoke(
        app,
        ["project", "update", project_id, "--name", "Project Sentinel", "--archive"],
        env=env,
    )
    assert update_result.exit_code == 0
    assert "Project Sentinel" in update_result.output

    delete_result = runner.invoke(app, ["project", "delete", project_id], env=env)
    assert delete_result.exit_code == 0
