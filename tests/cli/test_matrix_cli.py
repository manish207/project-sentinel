from typer.testing import CliRunner

from project_sentinel.cli.app import app

runner = CliRunner()


def test_matrix_show_command():
    result = runner.invoke(app, ["matrix"])
    assert result.exit_code == 0

    # We should see the headers and quadrants of the Eisenhower Matrix
    assert "Eisenhower Matrix" in result.stdout
    assert "Q1: Do First" in result.stdout
    assert "Q2: Schedule" in result.stdout
    assert "Q3: Delegate" in result.stdout
    assert "Q4: Don't Do" in result.stdout
