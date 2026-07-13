from typer import Typer

from project_sentinel.cli.doctor import doctor
from project_sentinel.cli.project import project_app
from project_sentinel.cli.task import task_app
from project_sentinel.cli.version import version
from project_sentinel.cli.workspace import workspace_app
from project_sentinel.cli.calendar import app as calendar_app
from project_sentinel.cli.board import app as board_app
from project_sentinel.cli.matrix import app as matrix_app

app = Typer(
    help="Sentinel AI",
    no_args_is_help=True,
)

app.command()(version)
app.command()(doctor)
app.add_typer(task_app, name="task")
app.add_typer(project_app, name="project")
app.add_typer(workspace_app, name="workspace")
app.add_typer(calendar_app, name="calendar")
app.add_typer(board_app, name="board")
app.add_typer(matrix_app, name="matrix")
