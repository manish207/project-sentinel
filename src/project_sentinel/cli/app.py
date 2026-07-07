from typer import Typer

from project_sentinel.cli.doctor import doctor
from project_sentinel.cli.task import task_app
from project_sentinel.cli.version import version

app = Typer(
    help="Sentinel AI",
    no_args_is_help=True,
)

app.command()(version)
app.command()(doctor)
app.add_typer(task_app, name="task")
