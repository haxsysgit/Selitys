"""Shared fact and evidence model for selitys analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Confidence(Enum):
    """Confidence level for inferred information."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FactKind(Enum):
    """Type of fact extracted from the repository."""

    ENTRY_POINT = "entry_point"
    FRAMEWORK = "framework"
    ROUTE = "route"
    DOMAIN_ENTITY = "domain_entity"
    CONFIG_FILE = "config_file"
    ENV_VAR = "env_var"
    SUBSYSTEM = "subsystem"
    PATTERN = "pattern"
    RISK = "risk"


@dataclass(frozen=True)
class Evidence:
    """Evidence supporting a derived fact."""

    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    symbol: str | None = None
    snippet: str | None = None


@dataclass
class Fact:
    """A single derived fact with evidence and confidence."""

    kind: FactKind
    summary: str
    confidence: Confidence = Confidence.MEDIUM
    evidence: list[Evidence] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class FactBundle:
    """Collection of facts extracted from a repository."""

    facts: list[Fact] = field(default_factory=list)

    def add(self, fact: Fact) -> None:
        self.facts.append(fact)

    def by_kind(self, kind: FactKind) -> list[Fact]:
        return [fact for fact in self.facts if fact.kind == kind]
