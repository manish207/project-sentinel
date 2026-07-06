from rich.console import Console

from project_sentinel import __version__

console = Console()


def version() -> None:
    """Display Sentinel version."""
    console.print(f"[bold green]Sentinel AI[/bold green] v{__version__}")
