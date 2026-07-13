from typer.testing import CliRunner

from project_sentinel.cli.app import app

runner = CliRunner()


def test_path_show_command():
    result = runner.invoke(app, ["path"])
    assert result.exit_code == 0

    # We should either see the tree header or a fallback message
    assert (
        "No tasks with dependencies found in the workspace." in result.stdout
        or "Found" in result.stdout
        or "Critical Path" in result.stdout
    )
