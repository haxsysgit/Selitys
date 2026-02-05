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
