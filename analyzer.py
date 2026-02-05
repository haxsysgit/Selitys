"""Analyzer - infers high-level information from scanned repository."""

from dataclasses import dataclass, field
from pathlib import Path

from scanner import RepoStructure


@dataclass
class EntryPoint:
    """An application entry point."""
    path: str
    description: str


@dataclass
class ConfigInfo:
    """Configuration information."""
    config_files: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)


@dataclass
class FrameworkInfo:
    """Detected framework information."""
    name: str
    category: str
    confidence: str = "high"


@dataclass
class Subsystem:
    """A detected subsystem/component."""
    name: str
    directory: str
    description: str
    key_files: list[str] = field(default_factory=list)


@dataclass
class RiskArea:
    """A risky area in the codebase."""
    location: str
    risk_type: str
    description: str
    severity: str = "medium"


@dataclass
class RequestFlowStep:
    """A step in a request flow."""
    order: int
    location: str
    description: str
    file_path: str | None = None


@dataclass
class RequestFlow:
    """A traced request flow through the system."""
    name: str
    description: str
    steps: list[RequestFlowStep] = field(default_factory=list)
    touchpoints: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result for a repository."""
    repo_name: str
    likely_purpose: str
    frameworks: list[FrameworkInfo] = field(default_factory=list)
    entry_points: list[EntryPoint] = field(default_factory=list)
    config: ConfigInfo = field(default_factory=ConfigInfo)
    top_level_dirs: dict[str, str] = field(default_factory=dict)
    top_level_files: dict[str, str] = field(default_factory=dict)
    subsystems: list[Subsystem] = field(default_factory=list)
    risk_areas: list[RiskArea] = field(default_factory=list)
    patterns_detected: list[str] = field(default_factory=list)
    request_flow: RequestFlow | None = None
    first_read_files: list[tuple[str, str, int]] = field(default_factory=list)
    skip_files: list[tuple[str, str]] = field(default_factory=list)


class Analyzer:
    """Analyzes repository structure and infers high-level information."""

    def __init__(self, structure: RepoStructure):
        self.structure = structure
        self.root = structure.root_path

    def analyze(self) -> AnalysisResult:
        """Run full analysis on the repository."""
        result = AnalysisResult(
            repo_name=self.root.name,
            likely_purpose=self._infer_purpose(),
        )

        result.frameworks = self._detect_frameworks()
        result.entry_points = self._find_entry_points()
        result.config = self._analyze_config()
        result.top_level_dirs = self._describe_top_level_dirs()
        result.top_level_files = self._describe_top_level_files()

        return result

    def _infer_purpose(self) -> str:
        """Infer the likely purpose of this codebase."""
        indicators = []

        has_api = any("route" in str(f.relative_path).lower() or "api" in str(f.relative_path).lower()
                      for f in self.structure.files)
        has_models = any("model" in str(f.relative_path).lower() for f in self.structure.files)
        has_db = any("database" in str(f.relative_path).lower() or "db" in str(f.relative_path).lower()
                     for f in self.structure.files)
        has_auth = any("auth" in str(f.relative_path).lower() for f in self.structure.files)

        if has_api:
            indicators.append("API service")
        if has_models and has_db:
            indicators.append("with database persistence")
        if has_auth:
            indicators.append("with authentication")

        if not indicators:
            return "A Python application (purpose unclear from structure)"

        return "This appears to be " + " ".join(indicators) + "."

    def _detect_frameworks(self) -> list[FrameworkInfo]:
        """Detect frameworks used in the codebase."""
        frameworks = []

        for f in self.structure.files:
            if f.content is None:
                continue

            content_lower = f.content.lower()

            if "fastapi" in content_lower or "from fastapi" in content_lower:
                frameworks.append(FrameworkInfo("FastAPI", "Web Framework"))
            if "flask" in content_lower and "from flask" in content_lower:
                frameworks.append(FrameworkInfo("Flask", "Web Framework"))
            if "django" in content_lower:
                frameworks.append(FrameworkInfo("Django", "Web Framework"))
            if "sqlalchemy" in content_lower:
                frameworks.append(FrameworkInfo("SQLAlchemy", "ORM"))
            if "alembic" in content_lower or f.relative_path.name == "alembic.ini":
                frameworks.append(FrameworkInfo("Alembic", "Database Migrations"))
            if "pydantic" in content_lower:
                frameworks.append(FrameworkInfo("Pydantic", "Data Validation"))
            if "pytest" in content_lower:
                frameworks.append(FrameworkInfo("pytest", "Testing"))
            if "celery" in content_lower:
                frameworks.append(FrameworkInfo("Celery", "Task Queue"))
            if "redis" in content_lower:
                frameworks.append(FrameworkInfo("Redis", "Cache/Message Broker"))

        seen = set()
        unique = []
        for fw in frameworks:
            if fw.name not in seen:
                seen.add(fw.name)
                unique.append(fw)

        return unique

    def _find_entry_points(self) -> list[EntryPoint]:
        """Find application entry points."""
        entry_points = []

        for f in self.structure.files:
            name = f.relative_path.name

            if name == "main.py":
                desc = "Main application entry point"
                if f.content and "uvicorn" in f.content.lower():
                    desc = "ASGI server entry point (likely runs with uvicorn)"
                entry_points.append(EntryPoint(str(f.relative_path), desc))

            elif name == "app.py":
                entry_points.append(EntryPoint(str(f.relative_path), "Application factory or entry point"))

            elif name == "manage.py":
                entry_points.append(EntryPoint(str(f.relative_path), "Django management script"))

            elif name == "wsgi.py":
                entry_points.append(EntryPoint(str(f.relative_path), "WSGI application entry"))

            elif name == "asgi.py":
                entry_points.append(EntryPoint(str(f.relative_path), "ASGI application entry"))

        return entry_points

    def _analyze_config(self) -> ConfigInfo:
        """Analyze configuration files and environment variables."""
        config = ConfigInfo()

        config_patterns = [
            "config.py", "settings.py", "config.yaml", "config.yml",
            "config.json", ".env", ".env.example", "pyproject.toml",
        ]

        for f in self.structure.files:
            if f.relative_path.name in config_patterns:
                config.config_files.append(str(f.relative_path))

            if f.content and f.extension == ".py":
                import re
                env_matches = re.findall(r'os\.(?:environ|getenv)\s*[(\[]\s*["\']([^"\']+)["\']', f.content)
                for var in env_matches:
                    if var not in config.env_vars:
                        config.env_vars.append(var)

                settings_matches = re.findall(r'config\(["\']([^"\']+)["\']', f.content, re.IGNORECASE)
                for var in settings_matches:
                    if var not in config.env_vars:
                        config.env_vars.append(var)

        return config

    def _describe_top_level_dirs(self) -> dict[str, str]:
        """Generate descriptions for top-level directories."""
        descriptions = {}
        root_dirs, _ = self.structure.get_top_level_items()

        dir_purposes = {
            "app": "Main application code",
            "src": "Source code",
            "lib": "Library code",
            "api": "API routes and handlers",
            "routes": "HTTP route definitions",
            "models": "Data models and schemas",
            "services": "Business logic and services",
            "utils": "Utility functions",
            "helpers": "Helper functions",
            "core": "Core application logic",
            "config": "Configuration files",
            "tests": "Test files",
            "test": "Test files",
            "scripts": "Utility scripts",
            "migrations": "Database migrations",
            "alembic": "Alembic database migrations",
            "static": "Static assets",
            "templates": "Template files",
            "docs": "Documentation",
        }

        for d in root_dirs:
            name = d.relative_path.name.lower()
            if name in dir_purposes:
                descriptions[str(d.relative_path)] = dir_purposes[name]
            else:
                descriptions[str(d.relative_path)] = f"Contains {d.file_count} files"

        return descriptions

    def _describe_top_level_files(self) -> dict[str, str]:
        """Generate descriptions for top-level files."""
        descriptions = {}
        _, root_files = self.structure.get_top_level_items()

        file_purposes = {
            "main.py": "Application entry point",
            "app.py": "Application factory",
            "manage.py": "Django management script",
            "setup.py": "Package setup (legacy)",
            "pyproject.toml": "Project configuration and dependencies",
            "requirements.txt": "Python dependencies",
            "Pipfile": "Pipenv dependencies",
            "poetry.lock": "Poetry lock file",
            "uv.lock": "uv lock file",
            "Makefile": "Build and task automation",
            "Dockerfile": "Container definition",
            "docker-compose.yml": "Container orchestration",
            "docker-compose.yaml": "Container orchestration",
            ".env": "Environment variables (local)",
            ".env.example": "Environment variable template",
            "README.md": "Project documentation",
            "LICENSE": "License information",
            "alembic.ini": "Alembic configuration",
            ".gitignore": "Git ignore patterns",
            "conftest.py": "pytest configuration and fixtures",
        }

        for f in root_files:
            name = f.relative_path.name
            if name in file_purposes:
                descriptions[str(f.relative_path)] = file_purposes[name]
            else:
                descriptions[str(f.relative_path)] = f"{f.extension or 'unknown'} file ({f.line_count} lines)"

        return descriptions
