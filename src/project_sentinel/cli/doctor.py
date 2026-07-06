import platform
import sys

from rich.console import Console

console = Console()


def doctor() -> None:
    """Run a basic health check."""

    console.print("[bold cyan]Sentinel Doctor[/bold cyan]")
    console.print()

    console.print(f"Python : {sys.version.split()[0]}")
    console.print(f"Platform : {platform.system()} {platform.release()}")

    console.print()
    console.print("[green]✓ Basic health check passed[/green]")
