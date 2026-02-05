"""Markdown generator for selitys output files."""

from pathlib import Path
from typing import TextIO

from analyzer import AnalysisResult
from scanner import RepoStructure


class MarkdownGenerator:
    """Generates markdown explanation files."""

    def __init__(self, structure: RepoStructure, analysis: AnalysisResult):
        self.structure = structure
        self.analysis = analysis

    def _write_header(self, f: TextIO, title: str) -> None:
        """Write standard header for a markdown file."""
        f.write(f"# {title}\n\n")
        f.write(f"Repository: `{self.analysis.repo_name}`\n\n")
        f.write("---\n\n")

    def generate_overview(self, output_path: Path) -> None:
        """Generate selitys-overview.md."""
        with open(output_path, "w") as f:
            self._write_header(f, "Codebase Overview")

            self._write_purpose_section(f)
            self._write_tech_stack_section(f)
            self._write_structure_section(f)
            self._write_entry_points_section(f)
            self._write_config_section(f)
            self._write_stats_section(f)

    def _write_purpose_section(self, f: TextIO) -> None:
        """Write System Purpose section."""
        f.write("## System Purpose\n\n")
        f.write(f"{self.analysis.likely_purpose}\n\n")

    def _write_tech_stack_section(self, f: TextIO) -> None:
        """Write Technology Stack section."""
        f.write("## Technology Stack\n\n")

        if self.structure.languages_detected:
            f.write("**Languages:**\n")
            for lang, lines in list(self.structure.languages_detected.items())[:5]:
                f.write(f"- {lang}: {lines:,} lines\n")
            f.write("\n")

        if self.analysis.frameworks:
            f.write("**Frameworks and Libraries:**\n")
            for fw in self.analysis.frameworks:
                f.write(f"- {fw.name} ({fw.category})\n")
            f.write("\n")

    def _write_structure_section(self, f: TextIO) -> None:
        """Write Project Structure section."""
        f.write("## Project Structure\n\n")

        if self.analysis.top_level_dirs:
            f.write("**Directories:**\n")
            for dir_path, desc in self.analysis.top_level_dirs.items():
                f.write(f"- `{dir_path}/` - {desc}\n")
            f.write("\n")

        if self.analysis.top_level_files:
            f.write("**Key Files:**\n")
            for file_path, desc in self.analysis.top_level_files.items():
                f.write(f"- `{file_path}` - {desc}\n")
            f.write("\n")

    def _write_entry_points_section(self, f: TextIO) -> None:
        """Write Entry Points section."""
        f.write("## Entry Points\n\n")

        if self.analysis.entry_points:
            for ep in self.analysis.entry_points:
                f.write(f"- `{ep.path}` - {ep.description}\n")
            f.write("\n")
        else:
            f.write("No clear entry points detected.\n\n")

    def _write_config_section(self, f: TextIO) -> None:
        """Write Configuration section."""
        f.write("## Configuration\n\n")

        if self.analysis.config.config_files:
            f.write("**Configuration Files:**\n")
            for cf in self.analysis.config.config_files:
                f.write(f"- `{cf}`\n")
            f.write("\n")

        if self.analysis.config.env_vars:
            f.write("**Environment Variables:**\n")
            for var in self.analysis.config.env_vars[:15]:
                f.write(f"- `{var}`\n")
            if len(self.analysis.config.env_vars) > 15:
                f.write(f"- ... and {len(self.analysis.config.env_vars) - 15} more\n")
            f.write("\n")

    def _write_stats_section(self, f: TextIO) -> None:
        """Write Quick Stats section."""
        f.write("## Quick Stats\n\n")
        f.write(f"- **Total Files:** {self.structure.total_files}\n")
        f.write(f"- **Total Lines:** {self.structure.total_lines:,}\n")
        f.write(f"- **Languages:** {len(self.structure.languages_detected)}\n")
        if self.structure.languages_detected:
            primary = list(self.structure.languages_detected.keys())[0]
            f.write(f"- **Primary Language:** {primary}\n")
        f.write("\n")

    def generate_architecture(self, output_path: Path) -> None:
        """Generate selitys-architecture.md."""
        with open(output_path, "w") as f:
            self._write_header(f, "Architecture")

            self._write_subsystems_section(f)
            self._write_patterns_section(f)
            self._write_coupling_section(f)
            self._write_risk_section(f)

    def _write_subsystems_section(self, f: TextIO) -> None:
        """Write Subsystems section."""
        f.write("## Subsystems\n\n")

        if self.analysis.subsystems:
            for sub in self.analysis.subsystems:
                f.write(f"### {sub.name}\n\n")
                f.write(f"**Directory:** `{sub.directory}/`\n\n")
                f.write(f"{sub.description}\n\n")
                if sub.key_files:
                    f.write("**Key files:**\n")
                    for kf in sub.key_files:
                        f.write(f"- `{kf}`\n")
                    f.write("\n")
        else:
            f.write("No clear subsystems detected. The codebase may be relatively flat.\n\n")

    def _write_patterns_section(self, f: TextIO) -> None:
        """Write Patterns Detected section."""
        f.write("## Patterns Detected\n\n")

        if self.analysis.patterns_detected:
            for pattern in self.analysis.patterns_detected:
                f.write(f"- {pattern}\n")
            f.write("\n")
        else:
            f.write("No specific architectural patterns detected.\n\n")

    def _write_coupling_section(self, f: TextIO) -> None:
        """Write Coupling and Dependencies section."""
        f.write("## Coupling and Dependencies\n\n")

        if self.analysis.subsystems:
            f.write("Based on the detected subsystems, the likely dependency flow is:\n\n")
            f.write("```\n")
            subsystem_names = [s.name for s in self.analysis.subsystems]
            if "Routing" in subsystem_names or "API Layer" in subsystem_names:
                f.write("API/Routes -> Services -> Models -> Database\n")
            else:
                f.write(" -> ".join(subsystem_names[:4]) + "\n")
            f.write("```\n\n")
        else:
            f.write("Unable to determine coupling without clear subsystems.\n\n")

    def _write_risk_section(self, f: TextIO) -> None:
        """Write Risk Areas section."""
        f.write("## Risk Areas\n\n")

        if self.analysis.risk_areas:
            by_severity = {"high": [], "medium": [], "low": []}
            for risk in self.analysis.risk_areas:
                by_severity[risk.severity].append(risk)

            for severity in ["high", "medium", "low"]:
                risks = by_severity[severity]
                if risks:
                    f.write(f"### {severity.capitalize()} Severity\n\n")
                    for risk in risks:
                        f.write(f"**{risk.risk_type}** - `{risk.location}`\n\n")
                        f.write(f"{risk.description}\n\n")
        else:
            f.write("No significant risk areas detected.\n\n")

    def generate_request_flow(self, output_path: Path) -> None:
        """Generate selitys-request-flow.md."""
        with open(output_path, "w") as f:
            self._write_header(f, "Request Flow")

            if not self.analysis.request_flow:
                f.write("## Overview\n\n")
                f.write("Unable to trace a clear request flow. This may be a non-API codebase ")
                f.write("or uses patterns not recognized by selitys.\n\n")
                return

            flow = self.analysis.request_flow

            f.write("## Overview\n\n")
            f.write(f"**{flow.name}**\n\n")
            f.write(f"{flow.description}\n\n")

            f.write("## Step-by-Step Flow\n\n")
            for step in flow.steps:
                f.write(f"### {step.order}. {step.location}\n\n")
                f.write(f"{step.description}\n\n")
                if step.file_path:
                    f.write(f"*See:* `{step.file_path}`\n\n")

            f.write("## Key Touchpoints\n\n")
            if flow.touchpoints:
                for tp in flow.touchpoints:
                    f.write(f"- {tp}\n")
                f.write("\n")
            else:
                f.write("No additional touchpoints identified beyond the main flow.\n\n")

    def generate_first_read(self, output_path: Path) -> None:
        """Generate selitys-first-read.md."""
        with open(output_path, "w") as f:
            self._write_header(f, "First Read Guide")

            f.write("## Start Here\n\n")
            f.write("Read these files first, in order. They will give you the fastest path ")
            f.write("to understanding how this system works.\n\n")

            if self.analysis.first_read_files:
                for path, why, priority in self.analysis.first_read_files:
                    f.write(f"### {priority}. `{path}`\n\n")
                    f.write(f"{why}\n\n")
            else:
                f.write("No clear reading order could be determined. Start with any `main.py` ")
                f.write("or entry point file you can find.\n\n")

            f.write("## Core Logic\n\n")
            f.write("After reading the files above, the core business logic likely lives in:\n\n")

            service_dirs = [
                sub for sub in self.analysis.subsystems
                if "service" in sub.name.lower() or "core" in sub.name.lower()
            ]
            if service_dirs:
                for sub in service_dirs[:3]:
                    f.write(f"- `{sub.directory}/` - {sub.description}\n")
                f.write("\n")
            else:
                f.write("The core logic location is not clearly separated. Look for files ")
                f.write("with substantial business rules, likely in the main `app/` directory.\n\n")

            f.write("## Can Skip Initially\n\n")
            f.write("These files are safe to ignore on your first pass:\n\n")

            if self.analysis.skip_files:
                by_reason: dict[str, list[str]] = {}
                for path, reason in self.analysis.skip_files:
                    if reason not in by_reason:
                        by_reason[reason] = []
                    by_reason[reason].append(path)

                for reason, paths in by_reason.items():
                    f.write(f"**{reason}:**\n")
                    for path in paths[:5]:
                        f.write(f"- `{path}`\n")
                    if len(paths) > 5:
                        f.write(f"- ... and {len(paths) - 5} more\n")
                    f.write("\n")
            else:
                f.write("No files identified as skippable. Everything appears relevant.\n\n")

            f.write("## Reading Order Rationale\n\n")
            f.write("This order is recommended because:\n\n")
            f.write("1. **Entry point first** - Understand how the application boots\n")
            f.write("2. **Configuration second** - Know what environment variables and settings exist\n")
            f.write("3. **Data models third** - Understand the domain entities\n")
            f.write("4. **API routes fourth** - See the public interface\n")
            f.write("5. **Services last** - Dive into business logic once you have context\n\n")
            f.write("This mirrors how a request flows through the system.\n")
