from typer import Typer

from project_sentinel.cli.version import version
from project_sentinel.cli.doctor import doctor

app = Typer(
    help="Sentinel AI",
    no_args_is_help=True,
)

app.command()(version)
app.command()(doctor)
