"""Schema definitions for selitys output structure."""

from dataclasses import dataclass, field
from enum import Enum


class Confidence(Enum):
    """Confidence level for inferred information."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SubsystemInfo:
    """Information about a detected subsystem."""
    name: str
    directory: str
    description: str
    key_files: list[str] = field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM


@dataclass
class RiskArea:
    """A risky or fragile area in the codebase."""
    location: str
    risk_type: str
    description: str
    severity: str = "medium"


@dataclass
class RequestFlowStep:
    """A single step in a request flow."""
    order: int
    location: str
    description: str
    file_path: str | None = None


@dataclass
class FileRecommendation:
    """A file recommendation for first-read guide."""
    path: str
    reason: str
    priority: int


OVERVIEW_SCHEMA = {
    "filename": "selitys-overview.md",
    "sections": [
        {
            "heading": "System Purpose",
            "required": True,
            "description": "What this system appears to do, in 2-3 sentences",
        },
        {
            "heading": "Technology Stack",
            "required": True,
            "description": "Languages, frameworks, databases detected",
        },
        {
            "heading": "Project Structure",
            "required": True,
            "description": "Top-level directory layout with brief explanations",
        },
        {
            "heading": "Entry Points",
            "required": True,
            "description": "Where the application starts (main.py, app.py, etc.)",
        },
        {
            "heading": "Configuration",
            "required": False,
            "description": "How configuration and environment variables are used",
        },
        {
            "heading": "Quick Stats",
            "required": True,
            "description": "File count, line count, language breakdown",
        },
    ],
}

ARCHITECTURE_SCHEMA = {
    "filename": "selitys-architecture.md",
    "sections": [
        {
            "heading": "Subsystems",
            "required": True,
            "description": "Major components of the system (API, auth, database, etc.)",
        },
        {
            "heading": "Patterns Detected",
            "required": True,
            "description": "Architectural patterns observed (layered, microservices, etc.)",
        },
        {
            "heading": "Coupling and Dependencies",
            "required": True,
            "description": "How components depend on each other",
        },
        {
            "heading": "Risk Areas",
            "required": True,
            "description": "Fragile, tightly-coupled, or complex areas",
        },
    ],
}

REQUEST_FLOW_SCHEMA = {
    "filename": "selitys-request-flow.md",
    "sections": [
        {
            "heading": "Overview",
            "required": True,
            "description": "Brief description of what a typical request does",
        },
        {
            "heading": "Step-by-Step Flow",
            "required": True,
            "description": "Ordered steps from entry to response",
        },
        {
            "heading": "Key Touchpoints",
            "required": True,
            "description": "Important files/functions touched during the flow",
        },
    ],
}

FIRST_READ_SCHEMA = {
    "filename": "selitys-first-read.md",
    "sections": [
        {
            "heading": "Start Here",
            "required": True,
            "description": "Files to read first, in order",
        },
        {
            "heading": "Core Logic",
            "required": True,
            "description": "Where the main business logic lives",
        },
        {
            "heading": "Can Skip Initially",
            "required": True,
            "description": "Files that are safe to ignore on first pass",
        },
        {
            "heading": "Reading Order Rationale",
            "required": True,
            "description": "Why this order is recommended",
        },
    ],
}

ALL_SCHEMAS = [
    OVERVIEW_SCHEMA,
    ARCHITECTURE_SCHEMA,
    REQUEST_FLOW_SCHEMA,
    FIRST_READ_SCHEMA,
]
