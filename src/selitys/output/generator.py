"""Markdown generator for selitys output files."""

import json
from pathlib import Path
from typing import Any, TextIO

from selitys import __version__
from selitys.analysis.model import Evidence, Fact, FactKind
from selitys.core.analyzer import AnalysisResult
from selitys.core.scanner import RepoStructure


class MarkdownGenerator:
    """Generates markdown explanation files."""

    def __init__(self, structure: RepoStructure, analysis: AnalysisResult):
        self.structure = structure
        self.analysis = analysis

    def _facts_by_kind(self, kind: FactKind) -> list[Fact]:
        facts = [fact for fact in self.analysis.fact_bundle.facts if fact.kind == kind]
        return sorted(facts, key=self._fact_sort_key)

    def _fact_sort_key(self, fact: Fact) -> tuple:
        file_path = ""
        line = 0
        if fact.evidence:
            file_path = fact.evidence[0].file_path or ""
            line = fact.evidence[0].line_start or 0
        return (fact.summary.lower(), file_path, line)

    def _route_sort_key(self, fact: Fact) -> tuple:
        method = fact.attributes.get("method") or ""
        path = fact.attributes.get("path") or ""
        file_path = ""
        line = 0
        if fact.evidence:
            file_path = fact.evidence[0].file_path or ""
            line = fact.evidence[0].line_start or 0
        return (method, path, file_path, line)

    def _format_evidence(self, evidence_list: list[Evidence], *, limit: int = 2) -> str:
        entries: list[str] = []
        for evidence in evidence_list[:limit]:
            if not evidence.file_path:
                continue
            if evidence.line_start:
                entries.append(f"`{evidence.file_path}:{evidence.line_start}`")
            else:
                entries.append(f"`{evidence.file_path}`")
        return ", ".join(entries)

    def _evidence_note(self, fact: Fact, *, limit: int = 2) -> str:
        formatted = self._format_evidence(fact.evidence, limit=limit)
        if not formatted:
            return ""
        return f" Evidence: {formatted}"

    def _format_evidence_for_facts(self, facts: list[Fact], *, limit: int = 3) -> str:
        entries: list[str] = []
        for fact in facts:
            for evidence in fact.evidence:
                if not evidence.file_path:
                    continue
                if evidence.line_start:
                    entry = f"`{evidence.file_path}:{evidence.line_start}`"
                else:
                    entry = f"`{evidence.file_path}`"
                if entry not in entries:
                    entries.append(entry)
                if len(entries) >= limit:
                    break
            if len(entries) >= limit:
                break
        return ", ".join(entries)

    def _uncertain_line(self, reason: str) -> str:
        return f"Uncertain inference. {reason}\n\n"

    def _evidence_to_dict(self, evidence: Evidence) -> dict[str, Any]:
        return {
            "file": evidence.file_path,
            "line_start": evidence.line_start,
            "line_end": evidence.line_end,
            "symbol": evidence.symbol,
            "snippet": evidence.snippet,
        }

    def _fact_to_dict(self, fact: Fact) -> dict[str, Any]:
        return {
            "kind": fact.kind.value,
            "summary": fact.summary,
            "confidence": fact.confidence.value,
            "evidence": [self._evidence_to_dict(ev) for ev in fact.evidence],
            "attributes": dict(fact.attributes),
        }

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
        f.write(self._uncertain_line("Derived from file names, framework detection, and structure heuristics."))

        entity_facts = self._facts_by_kind(FactKind.DOMAIN_ENTITY)
        route_facts = sorted(self._facts_by_kind(FactKind.ROUTE), key=self._route_sort_key)

        if entity_facts or route_facts:
            f.write("### What This System Does\n\n")
            if entity_facts:
                names = [fact.attributes.get("class") or fact.summary for fact in entity_facts[:5]]
                f.write(f"This system manages {', '.join(n.lower() for n in names)} data.\n")
                evidence = self._format_evidence_for_facts(entity_facts)
                if evidence:
                    f.write(f"Evidence: {evidence}\n")
                f.write("\n")
            if route_facts:
                f.write(f"It exposes a REST API with {len(route_facts)} endpoint(s).\n")
                evidence = self._format_evidence_for_facts(route_facts)
                if evidence:
                    f.write(f"Evidence: {evidence}\n")
                f.write("\n")
        elif self.analysis.detailed_purpose:
            f.write("### What This System Does\n\n")
            f.write(f"{self.analysis.detailed_purpose}\n\n")
            f.write(self._uncertain_line("Derived from heuristic signals across the codebase."))

        if entity_facts:
            f.write("### Domain Entities\n\n")
            f.write("The system manages these core data types:\n\n")
            for fact in entity_facts[:10]:
                label = fact.attributes.get("class") or fact.summary
                f.write(f"- **{label}**{self._evidence_note(fact)}\n")
            f.write("\n")
        elif self.analysis.domain_entities:
            f.write("### Domain Entities\n\n")
            f.write("The system manages these core data types:\n\n")
            for entity in self.analysis.domain_entities[:10]:
                f.write(f"- **{entity}**\n")
            f.write("\n")
            f.write(self._uncertain_line("Entities derived from filename and class name heuristics."))

        if route_facts:
            f.write("### API Surface\n\n")
            f.write(f"The API exposes {len(route_facts)} endpoint(s):\n\n")
            f.write("| Method | Path | Source |\n")
            f.write("|--------|------|--------|\n")
            for fact in route_facts[:15]:
                method = fact.attributes.get("method") or "UNKNOWN"
                path = fact.attributes.get("path") or "<path>"
                source = self._format_evidence(fact.evidence, limit=1) or fact.attributes.get("file", "")
                if source:
                    source = source
                else:
                    source = "Unknown"
                f.write(f"| `{method}` | `{path}` | {source} |\n")
            if len(route_facts) > 15:
                f.write(f"\n*... and {len(route_facts) - 15} more endpoints*\n")
            f.write("\n")
        elif self.analysis.api_endpoints:
            f.write("### API Surface\n\n")
            f.write(f"The API exposes {len(self.analysis.api_endpoints)} endpoint(s):\n\n")
            f.write("| Method | Path | Source |\n")
            f.write("|--------|------|--------|\n")
            for method, path, desc in self.analysis.api_endpoints[:15]:
                f.write(f"| `{method}` | `{path}` | {desc} |\n")
            if len(self.analysis.api_endpoints) > 15:
                f.write(f"\n*... and {len(self.analysis.api_endpoints) - 15} more endpoints*\n")
            f.write("\n")
            f.write(self._uncertain_line("Endpoints derived from decorator pattern heuristics."))

    def _write_tech_stack_section(self, f: TextIO) -> None:
        """Write Technology Stack section."""
        f.write("## Technology Stack\n\n")

        if self.structure.languages_detected:
            f.write("**Languages:**\n")
            for lang, lines in list(self.structure.languages_detected.items())[:5]:
                f.write(f"- {lang}: {lines:,} lines\n")
            f.write("\n")

        framework_facts = self._facts_by_kind(FactKind.FRAMEWORK)
        if framework_facts:
            f.write("**Frameworks and Libraries:**\n")
            seen: set[str] = set()
            for fact in framework_facts:
                name = fact.attributes.get("name") or fact.summary
                category = fact.attributes.get("category")
                label = f"{name} ({category})" if category else fact.summary
                if label in seen:
                    continue
                seen.add(label)
                f.write(f"- {label}{self._evidence_note(fact)}\n")
            f.write("\n")
        elif self.analysis.frameworks:
            f.write("**Frameworks and Libraries:**\n")
            for fw in self.analysis.frameworks:
                f.write(f"- {fw.name} ({fw.category})\n")
            f.write("\n")
            f.write(self._uncertain_line("Frameworks inferred from string matching in source files."))

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

        entry_facts = self._facts_by_kind(FactKind.ENTRY_POINT)
        if entry_facts:
            for fact in entry_facts:
                path = fact.attributes.get("file") or "Unknown"
                f.write(f"- `{path}` - {fact.summary}{self._evidence_note(fact)}\n")
            f.write("\n")
        elif self.analysis.entry_points:
            for ep in self.analysis.entry_points:
                f.write(f"- `{ep.path}` - {ep.description}\n")
            f.write("\n")
            f.write(self._uncertain_line("Entry points inferred from filename heuristics."))
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
            f.write(self._uncertain_line("Subsystems inferred from directory names and file placement."))
        else:
            f.write("No clear subsystems detected. The codebase may be relatively flat.\n\n")

    def _write_patterns_section(self, f: TextIO) -> None:
        """Write Patterns Detected section."""
        f.write("## Patterns Detected\n\n")

        if self.analysis.patterns_detected:
            for pattern in self.analysis.patterns_detected:
                f.write(f"- {pattern}\n")
            f.write("\n")
            f.write(self._uncertain_line("Patterns inferred from naming conventions and dependency hints."))
        else:
            f.write("No specific architectural patterns detected.\n\n")

    def _write_coupling_section(self, f: TextIO) -> None:
        """Write Coupling and Dependencies section."""
        f.write("## Coupling and Dependencies\n\n")

        if self.analysis.subsystems:
            f.write("Based on the detected subsystems, the likely dependency flow is:\n\n")
            subsystem_names = [s.name for s in self.analysis.subsystems]
            f.write("**Simplified flow:**\n")
            f.write("```\n")
            if "Routing" in subsystem_names or "API Layer" in subsystem_names:
                f.write("API/Routes -> Services -> Models -> Database\n")
            else:
                f.write(" -> ".join(subsystem_names[:4]) + "\n")
            f.write("```\n\n")
            f.write(self._uncertain_line("Dependency flow inferred from subsystem roles."))
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
            f.write(self._uncertain_line("Request flow inferred from common framework patterns."))

            f.write("## Step-by-Step Flow\n\n")
            for step in flow.steps:
                f.write(f"### {step.order}. {step.location}\n\n")
                f.write(f"{step.description}\n\n")

                if step.code_insight:
                    f.write(f"**Code insight:** {step.code_insight}\n\n")

                if step.what_happens:
                    f.write(f"**What happens here:** {step.what_happens}\n\n")

                if step.key_functions:
                    f.write("**Key functions:** ")
                    f.write(", ".join(f"`{fn}()`" for fn in step.key_functions))
                    f.write("\n\n")

                if step.file_path:
                    f.write(f"**File:** `{step.file_path}`\n\n")

                f.write("---\n\n")

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
                f.write(self._uncertain_line("Reading order inferred from file names and common conventions."))
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

    def generate_config(self, output_path: Path) -> None:
        """Generate selitys-config.md."""
        with open(output_path, "w") as f:
            self._write_header(f, "Configuration Guide")

            f.write("## Overview\n\n")
            f.write("This document explains all configuration files and environment variables ")
            f.write("used by this application.\n\n")

            # Config files section
            f.write("## Configuration Files\n\n")
            if self.analysis.config.config_file_details:
                f.write("| File | Type | Description | Settings |\n")
                f.write("|------|------|-------------|----------|\n")
                for cf in self.analysis.config.config_file_details:
                    settings_str = str(cf.settings_count) if cf.settings_count > 0 else "-"
                    f.write(f"| `{cf.path}` | {cf.file_type} | {cf.description} | {settings_str} |\n")
                f.write("\n")
            else:
                f.write("No configuration files detected.\n\n")

            # Environment variables section
            f.write("## Environment Variables\n\n")
            if self.analysis.config.env_var_details:
                # Group by required vs optional
                required = [v for v in self.analysis.config.env_var_details if not v.has_default]
                optional = [v for v in self.analysis.config.env_var_details if v.has_default]

                if required:
                    f.write("### Required Variables\n\n")
                    f.write("These variables must be set for the application to run:\n\n")
                    f.write("| Variable | Source | Notes |\n")
                    f.write("|----------|--------|-------|\n")
                    for var in required:
                        notes = var.description or "No default provided"
                        f.write(f"| `{var.name}` | `{var.source_file}` | {notes} |\n")
                    f.write("\n")

                if optional:
                    f.write("### Optional Variables\n\n")
                    f.write("These variables have defaults and are optional:\n\n")
                    f.write("| Variable | Default | Source |\n")
                    f.write("|----------|---------|--------|\n")
                    for var in optional:
                        default = var.default_value if var.default_value else "(has default)"
                        # Truncate long defaults
                        if len(default) > 30:
                            default = default[:27] + "..."
                        f.write(f"| `{var.name}` | `{default}` | `{var.source_file}` |\n")
                    f.write("\n")

            elif self.analysis.config.env_vars:
                f.write("The following environment variables are used:\n\n")
                for var in self.analysis.config.env_vars:
                    f.write(f"- `{var}`\n")
                f.write("\n")
            else:
                f.write("No environment variables detected.\n\n")

            # Setup instructions
            f.write("## Local Setup\n\n")
            f.write("To configure this application locally:\n\n")
            f.write("1. Copy the example environment file (if available):\n")
            f.write("   ```bash\n")
            f.write("   cp .env.example .env\n")
            f.write("   ```\n\n")
            f.write("2. Edit `.env` and fill in the required values\n\n")
            f.write("3. For sensitive values (API keys, secrets), ensure they are:\n")
            f.write("   - Never committed to version control\n")
            f.write("   - Rotated regularly in production\n")
            f.write("   - Stored securely (e.g., secrets manager)\n\n")

            # Warnings
            if self.analysis.config.env_var_details:
                secret_vars = [v for v in self.analysis.config.env_var_details
                              if any(s in v.name.lower() for s in ["secret", "key", "password", "token"])]
                if secret_vars:
                    f.write("## Security Notes\n\n")
                    f.write("The following variables appear to contain sensitive data:\n\n")
                    for var in secret_vars:
                        f.write(f"- `{var.name}`\n")
                    f.write("\n")
                    f.write("Ensure these are properly secured and never exposed in logs or error messages.\n")

    def generate_json(self, output_path: Path) -> None:
        """Generate selitys-analysis.json with machine-readable analysis."""
        framework_facts = self._facts_by_kind(FactKind.FRAMEWORK)
        entry_facts = self._facts_by_kind(FactKind.ENTRY_POINT)
        entity_facts = self._facts_by_kind(FactKind.DOMAIN_ENTITY)
        route_facts = sorted(self._facts_by_kind(FactKind.ROUTE), key=self._route_sort_key)

        data: dict[str, Any] = {
            "version": __version__,
            "repository": self.analysis.repo_name,
            "summary": {
                "purpose": self.analysis.likely_purpose,
                "detailed_purpose": self.analysis.detailed_purpose,
                "total_files": self.structure.total_files,
                "total_lines": self.structure.total_lines,
                "languages": dict(self.structure.languages_detected),
            },
            "frameworks": [],
            "entry_points": [],
            "domain_entities": [],
            "api_endpoints": [],
            "subsystems": [
                {
                    "name": sub.name,
                    "directory": sub.directory,
                    "description": sub.description,
                    "key_files": sub.key_files,
                }
                for sub in self.analysis.subsystems
            ],
            "patterns": self.analysis.patterns_detected,
            "risk_areas": [
                {
                    "location": risk.location,
                    "type": risk.risk_type,
                    "description": risk.description,
                    "severity": risk.severity,
                }
                for risk in self.analysis.risk_areas
            ],
            "configuration": {
                "files": [
                    {
                        "path": cf.path,
                        "type": cf.file_type,
                        "description": cf.description,
                        "settings_count": cf.settings_count,
                    }
                    for cf in self.analysis.config.config_file_details
                ],
                "environment_variables": [
                    {
                        "name": var.name,
                        "source": var.source_file,
                        "has_default": var.has_default,
                        "default": var.default_value if var.has_default else None,
                    }
                    for var in self.analysis.config.env_var_details
                ],
            },
            "request_flow": None,
            "first_read": {
                "recommended": [
                    {"path": path, "reason": reason, "priority": priority}
                    for path, reason, priority in self.analysis.first_read_files
                ],
                "skip": [
                    {"path": path, "reason": reason}
                    for path, reason in self.analysis.skip_files
                ],
            },
            "facts": [self._fact_to_dict(fact) for fact in self.analysis.fact_bundle.facts],
        }

        if framework_facts:
            seen = set()
            for fact in framework_facts:
                name = fact.attributes.get("name") or fact.summary
                if name in seen:
                    continue
                seen.add(name)
                data["frameworks"].append(
                    {
                        "name": name,
                        "category": fact.attributes.get("category"),
                        "confidence": fact.confidence.value,
                        "evidence": [self._evidence_to_dict(ev) for ev in fact.evidence],
                    }
                )
        else:
            data["frameworks"] = [
                {"name": fw.name, "category": fw.category, "confidence": fw.confidence}
                for fw in self.analysis.frameworks
            ]

        if entry_facts:
            for fact in entry_facts:
                data["entry_points"].append(
                    {
                        "path": fact.attributes.get("file") or "Unknown",
                        "description": fact.summary,
                        "confidence": fact.confidence.value,
                        "evidence": [self._evidence_to_dict(ev) for ev in fact.evidence],
                    }
                )
        else:
            data["entry_points"] = [
                {"path": ep.path, "description": ep.description}
                for ep in self.analysis.entry_points
            ]

        if entity_facts:
            data["domain_entities"] = [
                {
                    "name": fact.attributes.get("class") or fact.summary,
                    "table": fact.attributes.get("table"),
                    "confidence": fact.confidence.value,
                    "evidence": [self._evidence_to_dict(ev) for ev in fact.evidence],
                }
                for fact in entity_facts
            ]
        else:
            data["domain_entities"] = self.analysis.domain_entities

        if route_facts:
            data["api_endpoints"] = [
                {
                    "method": fact.attributes.get("method"),
                    "path": fact.attributes.get("path"),
                    "handler": fact.attributes.get("handler"),
                    "file": fact.attributes.get("file"),
                    "confidence": fact.confidence.value,
                    "evidence": [self._evidence_to_dict(ev) for ev in fact.evidence],
                }
                for fact in route_facts
            ]
        else:
            data["api_endpoints"] = [
                {"method": method, "path": path, "source": desc}
                for method, path, desc in self.analysis.api_endpoints
            ]

        # Add request flow if available
        if self.analysis.request_flow:
            flow = self.analysis.request_flow
            data["request_flow"] = {
                "name": flow.name,
                "description": flow.description,
                "steps": [
                    {
                        "order": step.order,
                        "location": step.location,
                        "description": step.description,
                        "file": step.file_path,
                        "code_insight": step.code_insight,
                        "what_happens": step.what_happens,
                        "key_functions": step.key_functions,
                    }
                    for step in flow.steps
                ],
                "touchpoints": flow.touchpoints,
            }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
