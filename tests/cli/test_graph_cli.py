from typer.testing import CliRunner

from project_sentinel.cli.app import app

runner = CliRunner()


def test_graph_show_command():
    result = runner.invoke(app, ["graph"])
    assert result.exit_code == 0
    assert (
        "Workspace Dependency Trees" in result.stdout
        or "No tasks with dependencies found" in result.stdout
    )


def test_graph_reverse_show_command():
    result = runner.invoke(app, ["graph", "--reverse"])
    assert result.exit_code == 0
    assert (
        "Workspace Blocked-By Trees" in result.stdout
        or "No blocking tasks found" in result.stdout
    )
