"""Keyword-based question answering for selitys analysis results."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from selitys.core.analyzer import AnalysisResult
from selitys.core.scanner import RepoStructure


@dataclass
class Answer:
    """A structured answer to a user question."""
    question: str
    summary: str
    details: list[str] = field(default_factory=list)
    related_files: list[str] = field(default_factory=list)
    confidence: str = "high"  # high, medium, low


# Topic keyword mappings - each topic maps to keywords that trigger it
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "purpose": ["purpose", "what does", "what is", "about", "do", "goal", "objective"],
    "frameworks": ["framework", "library", "stack", "technology", "tech", "built with", "using"],
    "entry_points": ["entry", "start", "run", "launch", "boot", "main"],
    "config": ["config", "configuration", "environment", "env", "settings", "setup"],
    "risks": ["risk", "security", "vulnerability", "danger", "issue", "problem", "warning"],
    "architecture": ["architecture", "structure", "design", "pattern", "layer", "subsystem", "component"],
    "request_flow": ["request", "flow", "api", "endpoint", "route", "http", "call"],
    "first_read": ["read", "start", "first", "onboard", "begin", "new developer", "where to start"],
    "languages": ["language", "python", "javascript", "typescript", "code", "lines"],
    "dependencies": ["dependency", "depend", "coupling", "import", "relationship"],
    "entities": ["entity", "model", "domain", "data", "table", "schema"],
    "files": ["file", "directory", "folder", "structure", "layout", "tree"],
}


class QuestionAnswerer:
    """Answers questions about a codebase using keyword matching against analysis results."""

    def __init__(self, structure: RepoStructure, analysis: AnalysisResult):
        self.structure = structure
        self.analysis = analysis

    def ask(self, question: str) -> Answer:
        """Answer a question about the codebase."""
        topics = self._match_topics(question)

        if not topics:
            return Answer(
                question=question,
                summary="I couldn't determine what you're asking about.",
                details=[
                    "Try asking about: purpose, frameworks, entry points, configuration, "
                    "risks, architecture, request flow, languages, or files.",
                ],
                confidence="low",
            )

        # Build answer from matched topics (use the best match)
        primary_topic = topics[0]
        handler = getattr(self, f"_answer_{primary_topic}", None)

        if handler:
            answer = handler(question)
            answer.question = question
            return answer

        return Answer(
            question=question,
            summary="I found a match but don't have a handler for this topic yet.",
            confidence="low",
        )

    def _match_topics(self, question: str) -> list[str]:
        """Match question to topics by keyword scoring."""
        q_lower = question.lower()
        scores: dict[str, int] = {}

        for topic, keywords in TOPIC_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in q_lower:
                    # Longer keywords get higher scores
                    score += len(kw)
            if score > 0:
                scores[topic] = score

        # Sort by score descending
        return sorted(scores, key=lambda t: scores[t], reverse=True)

    def _answer_purpose(self, question: str) -> Answer:
        """Answer questions about what the project does."""
        details = [self.analysis.likely_purpose]
        if self.analysis.detailed_purpose:
            details.append(self.analysis.detailed_purpose)

        related = [ep.path for ep in self.analysis.entry_points]

        return Answer(
            question=question,
            summary=self.analysis.likely_purpose,
            details=details,
            related_files=related,
            confidence="high",
        )

    def _answer_frameworks(self, question: str) -> Answer:
        """Answer questions about the tech stack."""
        if not self.analysis.frameworks:
            return Answer(
                question=question,
                summary="No specific frameworks were detected.",
                confidence="low",
            )

        fw_lines = [f"{fw.name} ({fw.category})" for fw in self.analysis.frameworks]
        return Answer(
            question=question,
            summary=f"This project uses {len(self.analysis.frameworks)} detected frameworks/libraries.",
            details=fw_lines,
            confidence="high",
        )

    def _answer_entry_points(self, question: str) -> Answer:
        """Answer questions about where the app starts."""
        if not self.analysis.entry_points:
            return Answer(
                question=question,
                summary="No clear entry points were detected.",
                confidence="low",
            )

        details = [f"{ep.path} — {ep.description}" for ep in self.analysis.entry_points]
        related = [ep.path for ep in self.analysis.entry_points]

        return Answer(
            question=question,
            summary=f"Found {len(self.analysis.entry_points)} entry point(s).",
            details=details,
            related_files=related,
            confidence="high",
        )

    def _answer_config(self, question: str) -> Answer:
        """Answer questions about configuration."""
        details = []

        if self.analysis.config.config_files:
            details.append(f"Config files: {', '.join(self.analysis.config.config_files)}")

        if self.analysis.config.env_vars:
            details.append(f"Environment variables ({len(self.analysis.config.env_vars)}):")
            for var in self.analysis.config.env_vars[:15]:
                details.append(f"  - {var}")
            if len(self.analysis.config.env_vars) > 15:
                details.append(f"  ... and {len(self.analysis.config.env_vars) - 15} more")

        if not details:
            return Answer(
                question=question,
                summary="No configuration files or environment variables detected.",
                confidence="low",
            )

        return Answer(
            question=question,
            summary=f"Found {len(self.analysis.config.config_files)} config file(s) and {len(self.analysis.config.env_vars)} environment variable(s).",
            details=details,
            related_files=self.analysis.config.config_files,
            confidence="high",
        )

    def _answer_risks(self, question: str) -> Answer:
        """Answer questions about security risks."""
        if not self.analysis.risk_areas:
            return Answer(
                question=question,
                summary="No significant risks were detected.",
                confidence="medium",
            )

        details = []
        by_severity: dict[str, list] = {}
        for risk in self.analysis.risk_areas:
            by_severity.setdefault(risk.severity, []).append(risk)

        for sev in ["high", "medium", "low"]:
            if sev in by_severity:
                details.append(f"{sev.upper()} severity ({len(by_severity[sev])}):")
                for r in by_severity[sev]:
                    details.append(f"  - [{r.risk_type}] {r.location}: {r.description}")

        related = list({r.location for r in self.analysis.risk_areas})

        return Answer(
            question=question,
            summary=f"Found {len(self.analysis.risk_areas)} risk area(s).",
            details=details,
            related_files=related,
            confidence="high",
        )

    def _answer_architecture(self, question: str) -> Answer:
        """Answer questions about architecture."""
        details = []

        if self.analysis.subsystems:
            details.append(f"Detected {len(self.analysis.subsystems)} subsystem(s):")
            for sub in self.analysis.subsystems:
                details.append(f"  - {sub.name}: {sub.description}")

        if self.analysis.patterns_detected:
            details.append(f"Architectural patterns: {', '.join(self.analysis.patterns_detected)}")

        if not details:
            return Answer(
                question=question,
                summary="No clear architectural patterns were detected.",
                confidence="low",
            )

        return Answer(
            question=question,
            summary=f"The codebase has {len(self.analysis.subsystems)} subsystems with {len(self.analysis.patterns_detected)} detected patterns.",
            details=details,
            confidence="high",
        )

    def _answer_request_flow(self, question: str) -> Answer:
        """Answer questions about request flow and APIs."""
        details = []

        if self.analysis.api_endpoints:
            details.append(f"API endpoints ({len(self.analysis.api_endpoints)}):")
            for method, path, desc in self.analysis.api_endpoints[:15]:
                details.append(f"  - {method} {path}: {desc}")
            if len(self.analysis.api_endpoints) > 15:
                details.append(f"  ... and {len(self.analysis.api_endpoints) - 15} more")

        if self.analysis.request_flow:
            flow = self.analysis.request_flow
            details.append(f"\nRequest flow: {flow.name}")
            details.append(flow.description)
            for step in flow.steps:
                details.append(f"  {step.order}. [{step.location}] {step.description}")

        if not details:
            return Answer(
                question=question,
                summary="No request flow or API endpoints were detected.",
                confidence="low",
            )

        return Answer(
            question=question,
            summary=f"Found {len(self.analysis.api_endpoints)} API endpoint(s) with a traced request flow.",
            details=details,
            confidence="high",
        )

    def _answer_first_read(self, question: str) -> Answer:
        """Answer questions about where to start reading."""
        if not self.analysis.first_read_files:
            return Answer(
                question=question,
                summary="No specific reading order recommendation available.",
                confidence="low",
            )

        details = ["Recommended reading order:"]
        for path, reason, priority in self.analysis.first_read_files:
            details.append(f"  {priority}. {path} — {reason}")

        if self.analysis.skip_files:
            details.append("\nCan skip initially:")
            for path, reason in self.analysis.skip_files[:5]:
                details.append(f"  - {path}: {reason}")

        related = [path for path, _, _ in self.analysis.first_read_files]

        return Answer(
            question=question,
            summary=f"Recommended {len(self.analysis.first_read_files)} files to read in order.",
            details=details,
            related_files=related,
            confidence="high",
        )

    def _answer_languages(self, question: str) -> Answer:
        """Answer questions about languages used."""
        langs = self.structure.languages_detected
        if not langs:
            return Answer(
                question=question,
                summary="No languages detected.",
                confidence="low",
            )

        details = [f"{lang}: {lines:,} lines" for lang, lines in langs.items()]

        return Answer(
            question=question,
            summary=f"Project uses {len(langs)} language(s), {self.structure.total_lines:,} total lines across {self.structure.total_files} files.",
            details=details,
            confidence="high",
        )

    def _answer_dependencies(self, question: str) -> Answer:
        """Answer questions about dependencies and coupling."""
        return self._answer_architecture(question)

    def _answer_entities(self, question: str) -> Answer:
        """Answer questions about domain entities."""
        if not self.analysis.domain_entities:
            return Answer(
                question=question,
                summary="No domain entities detected.",
                confidence="low",
            )

        details = [f"  - {entity}" for entity in self.analysis.domain_entities]

        return Answer(
            question=question,
            summary=f"Found {len(self.analysis.domain_entities)} domain entities.",
            details=details,
            confidence="high",
        )

    def _answer_files(self, question: str) -> Answer:
        """Answer questions about file structure."""
        details = []

        if self.analysis.top_level_dirs:
            details.append("Top-level directories:")
            for dirname, desc in self.analysis.top_level_dirs.items():
                details.append(f"  - {dirname}/: {desc}")

        if self.analysis.top_level_files:
            details.append("Top-level files:")
            for fname, desc in self.analysis.top_level_files.items():
                details.append(f"  - {fname}: {desc}")

        return Answer(
            question=question,
            summary=f"{self.structure.total_files} files across {len(self.analysis.top_level_dirs)} top-level directories.",
            details=details,
            confidence="high",
        )
