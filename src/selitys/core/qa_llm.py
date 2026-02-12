"""LLM-powered question answering using raw httpx calls to OpenAI-compatible APIs."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from selitys.core.analyzer import AnalysisResult
from selitys.core.scanner import RepoStructure


# Default configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MAX_TOKENS = 1024


def _check_httpx() -> None:
    """Check that httpx is installed, raise a helpful error if not."""
    try:
        import httpx  # noqa: F401
    except ImportError:
        print(
            "Error: httpx is required for LLM-powered Q&A.\n"
            "Install it with: pip install httpx\n"
            "Or: uv pip install httpx",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _build_context(structure: RepoStructure, analysis: AnalysisResult) -> str:
    """Build a concise context string from analysis results for the LLM."""
    parts = []

    parts.append(f"Repository: {analysis.repo_name}")
    parts.append(f"Purpose: {analysis.likely_purpose}")
    if analysis.detailed_purpose:
        parts.append(f"Details: {analysis.detailed_purpose}")

    # Languages
    if structure.languages_detected:
        lang_str = ", ".join(f"{k} ({v} lines)" for k, v in structure.languages_detected.items())
        parts.append(f"Languages: {lang_str}")
    parts.append(f"Total: {structure.total_files} files, {structure.total_lines:,} lines")

    # Frameworks
    if analysis.frameworks:
        fw_str = ", ".join(f"{fw.name} ({fw.category})" for fw in analysis.frameworks)
        parts.append(f"Frameworks: {fw_str}")

    # Entry points
    if analysis.entry_points:
        ep_str = ", ".join(f"{ep.path} ({ep.description})" for ep in analysis.entry_points)
        parts.append(f"Entry points: {ep_str}")

    # Subsystems
    if analysis.subsystems:
        parts.append("Subsystems:")
        for sub in analysis.subsystems:
            files_str = ", ".join(sub.key_files[:5]) if sub.key_files else "n/a"
            parts.append(f"  - {sub.name} ({sub.directory}): {sub.description} [files: {files_str}]")

    # Architecture patterns
    if analysis.patterns_detected:
        parts.append(f"Patterns: {', '.join(analysis.patterns_detected)}")

    # Risk areas
    if analysis.risk_areas:
        parts.append("Risk areas:")
        for r in analysis.risk_areas[:10]:
            parts.append(f"  - [{r.severity}] {r.risk_type} in {r.location}: {r.description}")

    # Config
    if analysis.config.env_vars:
        parts.append(f"Environment variables ({len(analysis.config.env_vars)}): {', '.join(analysis.config.env_vars[:20])}")
    if analysis.config.config_files:
        parts.append(f"Config files: {', '.join(analysis.config.config_files)}")

    # Domain entities
    if analysis.domain_entities:
        parts.append(f"Domain entities: {', '.join(analysis.domain_entities[:20])}")

    # API endpoints
    if analysis.api_endpoints:
        parts.append(f"API endpoints ({len(analysis.api_endpoints)}):")
        for method, path, desc in analysis.api_endpoints[:20]:
            parts.append(f"  - {method} {path}: {desc}")

    # Request flow
    if analysis.request_flow:
        flow = analysis.request_flow
        parts.append(f"Request flow ({flow.name}): {flow.description}")
        for step in flow.steps:
            parts.append(f"  {step.order}. [{step.location}] {step.description}")

    # Top-level structure
    if analysis.top_level_dirs:
        dirs_str = ", ".join(f"{k}/ ({v})" for k, v in analysis.top_level_dirs.items())
        parts.append(f"Directories: {dirs_str}")

    # First read recommendations
    if analysis.first_read_files:
        parts.append("Recommended reading order:")
        for path, reason, priority in analysis.first_read_files:
            parts.append(f"  {priority}. {path}: {reason}")

    return "\n".join(parts)


SYSTEM_PROMPT = """You are a senior software engineer answering questions about a codebase.
You have been given a structured analysis of the repository. Answer the developer's question
concisely and accurately based ONLY on the provided analysis data. If the analysis doesn't
contain enough information to answer, say so honestly.

Keep answers focused, practical, and under 300 words. Use bullet points for lists.
Do not make up information that isn't in the analysis."""


def ask_llm(
    structure: RepoStructure,
    analysis: AnalysisResult,
    question: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> str:
    """Send a question to an OpenAI-compatible LLM API and return the response.

    Args:
        structure: The scanned repository structure.
        analysis: The analysis result.
        question: The user's question.
        api_key: API key. Falls back to SELITYS_API_KEY or OPENAI_API_KEY env vars.
        base_url: API base URL. Falls back to SELITYS_BASE_URL env var or OpenAI default.
        model: Model name. Falls back to SELITYS_MODEL env var or gpt-4o-mini.

    Returns:
        The LLM's response as a string.
    """
    _check_httpx()
    import httpx

    # Resolve config from args -> env -> defaults
    key = api_key or os.environ.get("SELITYS_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        print(
            "Error: No API key found.\n"
            "Set SELITYS_API_KEY or OPENAI_API_KEY environment variable,\n"
            "or pass --api-key on the command line.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    url = base_url or os.environ.get("SELITYS_BASE_URL") or DEFAULT_BASE_URL
    mdl = model or os.environ.get("SELITYS_MODEL") or DEFAULT_MODEL

    context = _build_context(structure, analysis)

    payload = {
        "model": mdl,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"## Codebase Analysis\n\n{context}\n\n## Question\n\n{question}"},
        ],
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": 0.3,
    }

    endpoint = f"{url.rstrip('/')}/chat/completions"

    response = httpx.post(
        endpoint,
        json=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )

    if response.status_code != 200:
        error_detail = response.text[:200]
        print(f"Error: API returned status {response.status_code}: {error_detail}", file=sys.stderr)
        raise SystemExit(1)

    data = response.json()
    return data["choices"][0]["message"]["content"]
