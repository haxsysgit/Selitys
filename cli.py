"""selitys CLI - A developer onboarding tool that explains backend codebases."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from analyzer import Analyzer
from generator import MarkdownGenerator
from scanner import RepoScanner

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

    scanner = RepoScanner(repo_path)
    with console.status("[bold green]Scanning repository..."):
        structure = scanner.scan()

    console.print(f"[green]Scanned {structure.total_files} files, {structure.total_lines:,} lines of code[/green]")
    console.print()

    if structure.languages_detected:
        table = Table(title="Languages Detected")
        table.add_column("Language", style="cyan")
        table.add_column("Lines", justify="right", style="green")
        for lang, lines in list(structure.languages_detected.items())[:10]:
            table.add_row(lang, f"{lines:,}")
        console.print(table)
        console.print()

    root_dirs, root_files = structure.get_top_level_items()
    console.print(f"[bold]Top-level structure:[/bold] {len(root_dirs)} directories, {len(root_files)} files")
    for d in sorted(root_dirs, key=lambda x: x.relative_path):
        console.print(f"  [blue]{d.relative_path}/[/blue]")
    for f in sorted(root_files, key=lambda x: x.relative_path):
        console.print(f"  {f.relative_path}")

    # Run analysis
    with console.status("[bold green]Analyzing codebase..."):
        analyzer = Analyzer(structure)
        analysis = analyzer.analyze()

    # Generate markdown
    output_dir.mkdir(parents=True, exist_ok=True)
    generator = MarkdownGenerator(structure, analysis)

    overview_path = output_dir / "selitys-overview.md"
    generator.generate_overview(overview_path)
    console.print(f"[green]Generated:[/green] {overview_path}")

    architecture_path = output_dir / "selitys-architecture.md"
    generator.generate_architecture(architecture_path)
    console.print(f"[green]Generated:[/green] {architecture_path}")

    request_flow_path = output_dir / "selitys-request-flow.md"
    generator.generate_request_flow(request_flow_path)
    console.print(f"[green]Generated:[/green] {request_flow_path}")

    console.print()
    console.print("[bold green]Done.[/bold green]")


@app.command()
def version() -> None:
    """Show the current version of selitys."""
    console.print(f"selitys version {__version__}")


if __name__ == "__main__":
    app()
