"""selitys CLI - A developer onboarding tool that explains backend codebases."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from selitys import __version__
from selitys.core.analyzer import Analyzer
from selitys.core.scanner import RepoScanner
from selitys.output.generator import MarkdownGenerator

app = typer.Typer(
    name="selitys",
    help="Explain a backend codebase to a new developer",
    add_completion=False,
)
console = Console()


def run_analysis(
    repo_path: Path,
    output_dir: Path,
    json_output: bool,
    *,
    quiet: bool = False,
    max_file_size_bytes: int | None = None,
    respect_gitignore: bool = True,
) -> None:
    """Run analysis and generate output files."""
    if not quiet:
        console.print(f"[bold]selitys[/bold] - Analyzing: {repo_path}")
        console.print()

    scanner = RepoScanner(
        repo_path,
        max_file_size_bytes=max_file_size_bytes,
        respect_gitignore=respect_gitignore,
    )
    if not quiet:
        with console.status("[bold green]Scanning repository..."):
            structure = scanner.scan()
    else:
        structure = scanner.scan()

    if not quiet:
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
    if not quiet:
        with console.status("[bold green]Analyzing codebase..."):
            analyzer = Analyzer(structure)
            analysis = analyzer.analyze()
    else:
        analyzer = Analyzer(structure)
        analysis = analyzer.analyze()

    # Generate markdown
    output_dir.mkdir(parents=True, exist_ok=True)
    generator = MarkdownGenerator(structure, analysis)

    generator.generate_overview(output_dir / "selitys-overview.md")
    generator.generate_architecture(output_dir / "selitys-architecture.md")
    generator.generate_request_flow(output_dir / "selitys-request-flow.md")
    generator.generate_first_read(output_dir / "selitys-first-read.md")
    generator.generate_config(output_dir / "selitys-config.md")

    if json_output:
        generator.generate_json(output_dir / "selitys-analysis.json")

    if not quiet:
        console.print(f"[green]Generated 5 files{' + JSON' if json_output else ''} in {output_dir}[/green]")
        console.print()
        console.print("[bold green]Done.[/bold green]")


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
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output analysis as JSON file in addition to markdown",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch for file changes and regenerate output automatically",
    ),
    max_file_size: int = typer.Option(
        2_000_000,
        "--max-file-size",
        help="Skip files larger than this size in bytes (0 to disable)",
    ),
    respect_gitignore: bool = typer.Option(
        True,
        "--respect-gitignore/--no-respect-gitignore",
        help="Respect .gitignore rules when scanning",
    ),
) -> None:
    """Analyze a repository and generate explanation documents."""
    if output_dir is None:
        output_dir = Path.cwd()

    # Initial run
    max_size = None if max_file_size <= 0 else max_file_size
    run_analysis(repo_path, output_dir, json_output, max_file_size_bytes=max_size, respect_gitignore=respect_gitignore)

    if watch:
        from watchfiles import watch as watchfiles_watch

        console.print()
        console.print("[yellow]Watching for changes... (Ctrl+C to stop)[/yellow]")

        try:
            for changes in watchfiles_watch(repo_path):
                changed_files = [str(c[1]) for c in changes]
                # Skip output directory changes
                if any(str(output_dir) in f for f in changed_files):
                    continue
                console.print(f"[dim]Changes detected in {len(changes)} file(s), regenerating...[/dim]")
                run_analysis(
                    repo_path,
                    output_dir,
                    json_output,
                    quiet=True,
                    max_file_size_bytes=max_size,
                    respect_gitignore=respect_gitignore,
                )
                console.print(f"[green]Regenerated at {Path(changed_files[0]).stat().st_mtime if changed_files else 'now'}[/green]")
        except KeyboardInterrupt:
            console.print()
            console.print("[yellow]Watch mode stopped.[/yellow]")


@app.command()
def version() -> None:
    """Show the current version of selitys."""
    console.print(f"selitys version {__version__}")


if __name__ == "__main__":
    app()
