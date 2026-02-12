"""selitys CLI - A developer onboarding tool that explains backend codebases."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from selitys import __version__
from selitys.core.analyzer import Analyzer
from selitys.core.qa import QuestionAnswerer
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
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> None:
    """Run analysis and generate output files."""
    if not quiet:
        console.print(f"[bold]selitys[/bold] - Analyzing: {repo_path}")
        console.print()

    scanner = RepoScanner(
        repo_path,
        max_file_size_bytes=max_file_size_bytes,
        respect_gitignore=respect_gitignore,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
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
    repo_path: Annotated[Path, typer.Argument(
        help="Path to the repository to analyze",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    )],
    output_dir: Annotated[Optional[Path], typer.Option(
        "--output", "-o",
        help="Output directory for generated files (default: current directory)",
    )] = None,
    json_output: Annotated[bool, typer.Option(
        "--json", "-j",
        help="Output analysis as JSON file in addition to markdown",
    )] = False,
    watch: Annotated[bool, typer.Option(
        "--watch", "-w",
        help="Watch for file changes and regenerate output automatically",
    )] = False,
    max_file_size: Annotated[int, typer.Option(
        "--max-file-size",
        help="Skip files larger than this size in bytes (0 to disable)",
    )] = 2_000_000,
    respect_gitignore: Annotated[bool, typer.Option(
        "--respect-gitignore/--no-respect-gitignore",
        help="Respect .gitignore rules when scanning",
    )] = True,
    include: Annotated[Optional[list[str]], typer.Option(
        "--include", "-i",
        help="Glob patterns to include (can be repeated)",
    )] = None,
    exclude: Annotated[Optional[list[str]], typer.Option(
        "--exclude", "-x",
        help="Glob patterns to exclude (can be repeated)",
    )] = None,
) -> None:
    """Analyze a repository and generate explanation documents."""
    if output_dir is None:
        output_dir = Path.cwd()

    # Initial run
    max_size = None if max_file_size <= 0 else max_file_size
    run_analysis(
        repo_path,
        output_dir,
        json_output,
        max_file_size_bytes=max_size,
        respect_gitignore=respect_gitignore,
        include_patterns=include,
        exclude_patterns=exclude,
    )

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
                    include_patterns=include,
                    exclude_patterns=exclude,
                )
                console.print(f"[green]Regenerated at {Path(changed_files[0]).stat().st_mtime if changed_files else 'now'}[/green]")
        except KeyboardInterrupt:
            console.print()
            console.print("[yellow]Watch mode stopped.[/yellow]")


@app.command()
def ask(
    repo_path: Annotated[Path, typer.Argument(
        help="Path to the repository to query",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    )],
    question: Annotated[str, typer.Argument(
        help="Question about the codebase (e.g. 'what frameworks are used?')",
    )],
    llm: Annotated[bool, typer.Option(
        "--llm",
        help="Use an LLM for richer answers (requires httpx and an API key)",
    )] = False,
    api_key: Annotated[Optional[str], typer.Option(
        "--api-key",
        envvar="SELITYS_API_KEY",
        help="API key for the LLM provider (or set SELITYS_API_KEY / OPENAI_API_KEY)",
    )] = None,
    base_url: Annotated[Optional[str], typer.Option(
        "--base-url",
        envvar="SELITYS_BASE_URL",
        help="Base URL for an OpenAI-compatible API (default: OpenAI)",
    )] = None,
    model: Annotated[Optional[str], typer.Option(
        "--model",
        envvar="SELITYS_MODEL",
        help="Model name to use (default: gpt-4o-mini)",
    )] = None,
    max_file_size: Annotated[int, typer.Option(
        "--max-file-size",
        help="Skip files larger than this size in bytes (0 to disable)",
    )] = 2_000_000,
    respect_gitignore: Annotated[bool, typer.Option(
        "--respect-gitignore/--no-respect-gitignore",
        help="Respect .gitignore rules when scanning",
    )] = True,
) -> None:
    """Ask a question about a codebase and get an instant answer."""
    max_size = None if max_file_size <= 0 else max_file_size

    scanner = RepoScanner(
        repo_path,
        max_file_size_bytes=max_size,
        respect_gitignore=respect_gitignore,
    )
    with console.status("[bold green]Scanning repository..."):
        structure = scanner.scan()

    with console.status("[bold green]Analyzing codebase..."):
        analyzer = Analyzer(structure)
        analysis = analyzer.analyze()

    console.print()
    console.print(f"[bold cyan]Q:[/bold cyan] {question}")
    console.print()

    if llm:
        from selitys.core.qa_llm import ask_llm

        with console.status("[bold green]Thinking..."):
            response = ask_llm(
                structure,
                analysis,
                question,
                api_key=api_key,
                base_url=base_url,
                model=model,
            )

        console.print(response)
        console.print()
        return

    # Keyword-based fallback
    qa = QuestionAnswerer(structure, analysis)
    answer = qa.ask(question)

    if answer.confidence == "low":
        console.print(f"[yellow]{answer.summary}[/yellow]")
    else:
        console.print(f"[bold green]{answer.summary}[/bold green]")

    if answer.details:
        console.print()
        for line in answer.details:
            console.print(f"  {line}")

    if answer.related_files:
        console.print()
        console.print("[dim]Related files:[/dim]")
        for f in answer.related_files[:10]:
            console.print(f"  [dim]{f}[/dim]")

    console.print()
    console.print("[dim]Tip: use --llm for richer AI-powered answers[/dim]")
    console.print()


@app.command()
def tree(
    repo_path: Annotated[Path, typer.Argument(
        help="Path to the repository to visualize",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    )],
    max_file_size: Annotated[int, typer.Option(
        "--max-file-size",
        help="Skip files larger than this size in bytes (0 to disable)",
    )] = 2_000_000,
    respect_gitignore: Annotated[bool, typer.Option(
        "--respect-gitignore/--no-respect-gitignore",
        help="Respect .gitignore rules when scanning",
    )] = True,
) -> None:
    """Show dependency tree and architectural layers of a codebase."""
    from rich.panel import Panel
    from rich.tree import Tree as RichTree

    max_size = None if max_file_size <= 0 else max_file_size
    scanner = RepoScanner(repo_path, max_file_size_bytes=max_size, respect_gitignore=respect_gitignore)

    with console.status("[bold green]Scanning repository..."):
        structure = scanner.scan()

    with console.status("[bold green]Analyzing codebase..."):
        analyzer = Analyzer(structure)
        analysis = analyzer.analyze()

    graph = analysis.dependency_graph

    if not graph.nodes:
        console.print("[yellow]No internal dependencies detected.[/yellow]")
        return

    # Summary
    console.print()
    console.print(f"[bold]selitys tree[/bold] — {analysis.repo_name}")
    console.print(f"[dim]{len(graph.nodes)} modules, {len(graph.edges)} dependencies[/dim]")
    console.print()

    # Architectural layers
    layer_colors = {
        "entry_point": "bold green",
        "route": "bold cyan",
        "service": "bold yellow",
        "model": "bold magenta",
        "config": "bold blue",
        "module": "dim",
        "test": "dim red",
    }

    root = RichTree(f"[bold]{analysis.repo_name}[/bold]")
    for layer in graph.layers:
        color = layer_colors.get(layer["type"], "dim")
        branch = root.add(f"[{color}]{layer['name']}[/{color}] ({len(layer['files'])})")
        for fpath in layer["files"]:
            # Find node to show import counts
            node = next((n for n in graph.nodes if n.path == fpath), None)
            suffix = ""
            if node:
                parts = []
                if node.imports_count:
                    parts.append(f"→{node.imports_count}")
                if node.imported_by_count:
                    parts.append(f"←{node.imported_by_count}")
                if parts:
                    suffix = f" [dim]({', '.join(parts)})[/dim]"
            branch.add(f"{fpath}{suffix}")

    console.print(root)
    console.print()

    # Top dependencies (most imported)
    top_imported = sorted(graph.nodes, key=lambda n: n.imported_by_count, reverse=True)[:8]
    if top_imported and top_imported[0].imported_by_count > 0:
        table = Table(title="Most Depended-On Modules")
        table.add_column("Module", style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Imported By", justify="right", style="green")
        table.add_column("Imports", justify="right", style="yellow")
        for n in top_imported:
            if n.imported_by_count == 0:
                break
            table.add_row(n.path, n.node_type, str(n.imported_by_count), str(n.imports_count))
        console.print(table)
        console.print()

    # Dependency edges sample
    console.print("[bold]Dependency Flow:[/bold]")
    shown = set()
    for layer in graph.layers:
        for fpath in layer["files"][:3]:
            deps = [e for e in graph.edges if e.source == fpath]
            if deps and fpath not in shown:
                shown.add(fpath)
                targets = ", ".join(e.target.split("/")[-1] for e in deps[:4])
                extra = f" +{len(deps) - 4} more" if len(deps) > 4 else ""
                console.print(f"  [cyan]{fpath}[/cyan] → {targets}{extra}")
    console.print()


@app.command()
def version() -> None:
    """Show the current version of selitys."""
    console.print(f"selitys version {__version__}")


if __name__ == "__main__":
    app()
