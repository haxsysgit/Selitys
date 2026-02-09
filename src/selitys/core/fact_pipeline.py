"""Orchestrates language-specific analyzers into a unified fact bundle."""

from __future__ import annotations

from dataclasses import dataclass

from selitys.analysis import JsTsAnalyzer, PythonAstAnalyzer
from selitys.analysis.model import FactBundle
from selitys.core.scanner import RepoStructure


@dataclass
class FactPipeline:
    """Run multiple analyzers and merge their facts."""

    def analyze(self, structure: RepoStructure) -> FactBundle:
        bundle = FactBundle()

        python_facts = PythonAstAnalyzer().analyze(structure)
        bundle.facts.extend(python_facts.facts)

        js_facts = JsTsAnalyzer().analyze(structure)
        bundle.facts.extend(js_facts.facts)

        return bundle
