"""selitys CLI - A developer onboarding tool that explains backend codebases."""

from pathlib import Path

import typer
from rich.console import Console

__version__ = "0.1.0"

app = typer.Typer(
    name="selitys",
    help="Explain a backend codebase to a new developer",
    add_completion=False,
)
console = Console()


@app.command()
def explain(
    repo_path: Path = typer.Argument(
        ...,
        help="Path to the repository to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_dir: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for generated files (default: current directory)",
    ),
) -> None:
    """Analyze a repository and generate explanation documents."""
    if output_dir is None:
        output_dir = Path.cwd()

    console.print(f"[bold]selitys[/bold] - Analyzing: {repo_path}")
    console.print()
    console.print("[yellow]Scanner not yet implemented[/yellow]")


@app.command()
def version() -> None:
    """Show the current version of selitys."""
    console.print(f"selitys version {__version__}")


if __name__ == "__main__":
    app()
