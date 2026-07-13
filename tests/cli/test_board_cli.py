from typer.testing import CliRunner

from project_sentinel.cli.app import app

runner = CliRunner()


def test_board_show_command():
    result = runner.invoke(app, ["board"])
    assert result.exit_code == 0

    # We should see the headers of the Kanban board
    assert "Kanban Board" in result.stdout
    assert "Inbox" in result.stdout
    assert "Planned" in result.stdout
    assert "Ready" in result.stdout
    assert "In Progress" in result.stdout
    assert "Waiting" in result.stdout
    assert "Completed" in result.stdout
