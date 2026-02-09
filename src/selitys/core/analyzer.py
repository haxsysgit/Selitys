"""Analyzer - infers high-level information from scanned repository."""

from dataclasses import dataclass, field
from pathlib import Path

from selitys.analysis.model import FactBundle
from selitys.core.fact_pipeline import FactPipeline
from selitys.core.scanner import RepoStructure


@dataclass
class EntryPoint:
    """An application entry point."""
    path: str
    description: str


@dataclass
class EnvVarInfo:
    """Detailed environment variable information."""
    name: str
    source_file: str
    has_default: bool = False
    default_value: str = ""
    description: str = ""


@dataclass
class ConfigFileInfo:
    """Detailed configuration file information."""
    path: str
    file_type: str
    description: str
    settings_count: int = 0


@dataclass
class ConfigInfo:
    """Configuration information."""
    config_files: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    env_var_details: list[EnvVarInfo] = field(default_factory=list)
    config_file_details: list[ConfigFileInfo] = field(default_factory=list)


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
    code_insight: str = ""
    what_happens: str = ""
    key_functions: list[str] = field(default_factory=list)


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
    detailed_purpose: str = ""
    domain_entities: list[str] = field(default_factory=list)
    api_endpoints: list[tuple[str, str, str]] = field(default_factory=list)  # (method, path, description)
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
    fact_bundle: FactBundle = field(default_factory=FactBundle)


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
        result.subsystems = self._detect_subsystems()
        result.risk_areas = self._detect_risk_areas()
        result.patterns_detected = self._detect_patterns()
        result.domain_entities = self._extract_domain_entities()
        result.api_endpoints = self._extract_api_endpoints()
        result.detailed_purpose = self._build_detailed_purpose(result)
        result.request_flow = self._trace_request_flow()
        result.first_read_files, result.skip_files = self._recommend_reading_order()
        result.fact_bundle = FactPipeline().analyze(self.structure)

        return result

    def _infer_purpose(self) -> str:
        """Infer the likely purpose of this codebase."""
        indicators = []

        # Detect primary language
        langs = self.structure.languages_detected
        primary_lang = list(langs.keys())[0] if langs else "Unknown"
        is_js_ts = primary_lang in ["JavaScript", "TypeScript", "JavaScript (React)", "TypeScript (React)"]

        has_api = any("route" in str(f.relative_path).lower() or "api" in str(f.relative_path).lower()
                      for f in self.structure.files)
        has_models = any("model" in str(f.relative_path).lower() for f in self.structure.files)
        has_db = any("database" in str(f.relative_path).lower() or "db" in str(f.relative_path).lower()
                     for f in self.structure.files)
        has_auth = any("auth" in str(f.relative_path).lower() for f in self.structure.files)

        # JS/TS specific indicators
        has_components = any("component" in str(f.relative_path).lower() for f in self.structure.files)
        has_pages = any(f.relative_path.parent.name in ["pages", "app"] and f.extension in [".tsx", ".jsx", ".js", ".ts"]
                       for f in self.structure.files)
        has_package_json = any(f.relative_path.name == "package.json" for f in self.structure.files)

        if has_components or has_pages:
            if is_js_ts:
                indicators.append("frontend web application")
        elif has_api:
            indicators.append("API service")

        if has_models and has_db:
            indicators.append("with database persistence")
        if has_auth:
            indicators.append("with authentication")

        if not indicators:
            if is_js_ts and has_package_json:
                return f"A {primary_lang} application (purpose unclear from structure)"
            return f"A {primary_lang} application (purpose unclear from structure)"

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

            # JavaScript/TypeScript frameworks
            if f.extension in [".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"]:
                if "express" in content_lower and ("require('express')" in f.content or "from 'express'" in f.content or 'from "express"' in f.content):
                    frameworks.append(FrameworkInfo("Express", "Web Framework (Node.js)"))
                if "next" in content_lower and ("next/app" in f.content or "next/router" in f.content or "next/image" in f.content):
                    frameworks.append(FrameworkInfo("Next.js", "React Framework"))
                if "react" in content_lower and ("from 'react'" in f.content or 'from "react"' in f.content):
                    frameworks.append(FrameworkInfo("React", "UI Library"))
                if "vue" in content_lower and ("from 'vue'" in f.content or 'from "vue"' in f.content):
                    frameworks.append(FrameworkInfo("Vue.js", "UI Framework"))
                if "angular" in content_lower and "@angular" in f.content:
                    frameworks.append(FrameworkInfo("Angular", "UI Framework"))
                if "nestjs" in content_lower or "@nestjs" in f.content:
                    frameworks.append(FrameworkInfo("NestJS", "Web Framework (Node.js)"))
                if "prisma" in content_lower and ("@prisma/client" in f.content or "PrismaClient" in f.content):
                    frameworks.append(FrameworkInfo("Prisma", "ORM (Node.js)"))
                if "typeorm" in content_lower:
                    frameworks.append(FrameworkInfo("TypeORM", "ORM (Node.js)"))
                if "sequelize" in content_lower:
                    frameworks.append(FrameworkInfo("Sequelize", "ORM (Node.js)"))
                if "mongoose" in content_lower:
                    frameworks.append(FrameworkInfo("Mongoose", "MongoDB ODM"))
                if "jest" in content_lower and ("from 'jest'" in f.content or "describe(" in f.content):
                    frameworks.append(FrameworkInfo("Jest", "Testing"))
                if "mocha" in content_lower:
                    frameworks.append(FrameworkInfo("Mocha", "Testing"))
                if "vitest" in content_lower:
                    frameworks.append(FrameworkInfo("Vitest", "Testing"))
                if "tailwind" in content_lower:
                    frameworks.append(FrameworkInfo("Tailwind CSS", "CSS Framework"))
                if "graphql" in content_lower:
                    frameworks.append(FrameworkInfo("GraphQL", "API Query Language"))
                if "trpc" in content_lower or "@trpc" in f.content:
                    frameworks.append(FrameworkInfo("tRPC", "Type-safe API"))

            # Check package.json for dependencies
            if f.relative_path.name == "package.json":
                if '"express"' in f.content:
                    frameworks.append(FrameworkInfo("Express", "Web Framework (Node.js)"))
                if '"next"' in f.content:
                    frameworks.append(FrameworkInfo("Next.js", "React Framework"))
                if '"react"' in f.content:
                    frameworks.append(FrameworkInfo("React", "UI Library"))
                if '"vue"' in f.content:
                    frameworks.append(FrameworkInfo("Vue.js", "UI Framework"))
                if '"@nestjs/core"' in f.content:
                    frameworks.append(FrameworkInfo("NestJS", "Web Framework (Node.js)"))
                if '"typescript"' in f.content:
                    frameworks.append(FrameworkInfo("TypeScript", "Language"))

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

            # Python entry points
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

            # JavaScript/TypeScript entry points
            elif name in ["index.js", "index.ts", "main.js", "main.ts"]:
                if len(f.relative_path.parts) <= 2:  # Root or src level
                    desc = "Application entry point"
                    if f.content:
                        if "express" in f.content.lower():
                            desc = "Express server entry point"
                        elif "createServer" in f.content:
                            desc = "HTTP server entry point"
                    entry_points.append(EntryPoint(str(f.relative_path), desc))

            elif name == "server.js" or name == "server.ts":
                entry_points.append(EntryPoint(str(f.relative_path), "Server entry point"))

            elif name in ["app.js", "app.ts", "app.tsx"]:
                if len(f.relative_path.parts) <= 2:
                    entry_points.append(EntryPoint(str(f.relative_path), "Application entry point"))

            # Next.js/React entry points
            elif name in ["_app.tsx", "_app.js"]:
                entry_points.append(EntryPoint(str(f.relative_path), "Next.js application wrapper"))

            elif name in ["layout.tsx", "layout.js"] and f.relative_path.parent.name == "app":
                entry_points.append(EntryPoint(str(f.relative_path), "Next.js App Router layout"))

        return entry_points

    def _analyze_config(self) -> ConfigInfo:
        """Analyze configuration files and environment variables."""
        import re
        config = ConfigInfo()

        config_patterns = {
            # Python
            "config.py": ("Python", "Application configuration module"),
            "settings.py": ("Python", "Django-style settings module"),
            "pyproject.toml": ("TOML", "Python project configuration"),
            "alembic.ini": ("INI", "Alembic database migration configuration"),
            "pytest.ini": ("INI", "Pytest configuration"),
            "setup.cfg": ("INI", "Python package configuration"),
            # General
            "config.yaml": ("YAML", "YAML configuration file"),
            "config.yml": ("YAML", "YAML configuration file"),
            "config.json": ("JSON", "JSON configuration file"),
            ".env": ("Environment", "Environment variables file"),
            ".env.example": ("Environment", "Example environment variables template"),
            ".env.local": ("Environment", "Local environment overrides"),
            # JavaScript/TypeScript
            "package.json": ("JSON", "Node.js package configuration"),
            "tsconfig.json": ("JSON", "TypeScript compiler configuration"),
            "next.config.js": ("JavaScript", "Next.js configuration"),
            "next.config.mjs": ("JavaScript", "Next.js configuration"),
            "vite.config.ts": ("TypeScript", "Vite bundler configuration"),
            "vite.config.js": ("JavaScript", "Vite bundler configuration"),
            "webpack.config.js": ("JavaScript", "Webpack bundler configuration"),
            "tailwind.config.js": ("JavaScript", "Tailwind CSS configuration"),
            "tailwind.config.ts": ("TypeScript", "Tailwind CSS configuration"),
            "jest.config.js": ("JavaScript", "Jest testing configuration"),
            "jest.config.ts": ("TypeScript", "Jest testing configuration"),
            ".eslintrc.js": ("JavaScript", "ESLint configuration"),
            ".eslintrc.json": ("JSON", "ESLint configuration"),
            ".prettierrc": ("JSON", "Prettier configuration"),
            "prisma/schema.prisma": ("Prisma", "Prisma database schema"),
        }

        for f in self.structure.files:
            fname = f.relative_path.name
            if fname in config_patterns:
                config.config_files.append(str(f.relative_path))
                ftype, desc = config_patterns[fname]
                settings_count = 0
                if f.content:
                    if f.extension == ".py":
                        settings_count = len(re.findall(r'^\s*[A-Z_]+\s*=', f.content, re.MULTILINE))
                    elif f.extension in [".env", ""]:
                        settings_count = len(re.findall(r'^[A-Z_]+=', f.content, re.MULTILINE))
                config.config_file_details.append(ConfigFileInfo(
                    path=str(f.relative_path),
                    file_type=ftype,
                    description=desc,
                    settings_count=settings_count,
                ))

            if f.content and f.extension == ".py":
                # Find env vars with getenv (with potential default)
                getenv_matches = re.findall(
                    r'os\.getenv\s*\(\s*["\']([^"\']+)["\'](?:\s*,\s*([^)]+))?\)',
                    f.content
                )
                for var, default in getenv_matches:
                    if var not in config.env_vars:
                        config.env_vars.append(var)
                        has_default = bool(default and default.strip())
                        config.env_var_details.append(EnvVarInfo(
                            name=var,
                            source_file=str(f.relative_path),
                            has_default=has_default,
                            default_value=default.strip() if has_default else "",
                        ))

                # Find env vars with environ[]
                environ_matches = re.findall(r'os\.environ\s*\[\s*["\']([^"\']+)["\']\s*\]', f.content)
                for var in environ_matches:
                    if var not in config.env_vars:
                        config.env_vars.append(var)
                        config.env_var_details.append(EnvVarInfo(
                            name=var,
                            source_file=str(f.relative_path),
                            has_default=False,
                            description="Required - no default provided",
                        ))

                # Find pydantic settings fields
                settings_matches = re.findall(
                    r'(\w+)\s*:\s*\w+\s*=\s*Field\s*\([^)]*env\s*=\s*["\']([^"\']+)["\']',
                    f.content
                )
                for field_name, var in settings_matches:
                    if var not in config.env_vars:
                        config.env_vars.append(var)
                        config.env_var_details.append(EnvVarInfo(
                            name=var,
                            source_file=str(f.relative_path),
                            has_default=True,
                            description=f"Pydantic settings field: {field_name}",
                        ))

            # JavaScript/TypeScript env var detection
            if f.content and f.extension in [".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"]:
                # process.env.VAR_NAME
                process_env_matches = re.findall(r'process\.env\.([A-Z_][A-Z0-9_]*)', f.content)
                for var in process_env_matches:
                    if var not in config.env_vars:
                        config.env_vars.append(var)
                        config.env_var_details.append(EnvVarInfo(
                            name=var,
                            source_file=str(f.relative_path),
                            has_default=False,
                            description="Node.js environment variable",
                        ))

                # process.env["VAR_NAME"] or process.env['VAR_NAME']
                process_env_bracket = re.findall(r'process\.env\[["\']([A-Z_][A-Z0-9_]*)["\']', f.content)
                for var in process_env_bracket:
                    if var not in config.env_vars:
                        config.env_vars.append(var)
                        config.env_var_details.append(EnvVarInfo(
                            name=var,
                            source_file=str(f.relative_path),
                            has_default=False,
                            description="Node.js environment variable",
                        ))

                # Next.js public env vars (NEXT_PUBLIC_*)
                next_public = re.findall(r'(NEXT_PUBLIC_[A-Z0-9_]+)', f.content)
                for var in next_public:
                    if var not in config.env_vars:
                        config.env_vars.append(var)
                        config.env_var_details.append(EnvVarInfo(
                            name=var,
                            source_file=str(f.relative_path),
                            has_default=False,
                            description="Next.js public environment variable (exposed to browser)",
                        ))

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

    def _detect_subsystems(self) -> list[Subsystem]:
        """Detect major subsystems in the codebase."""
        subsystems = []

        subsystem_patterns = {
            "services": ("Services", "Business logic and service layer"),
            "service": ("Services", "Business logic and service layer"),
            "api": ("API Layer", "HTTP API handlers and endpoints"),
            "routes": ("Routing", "HTTP route definitions"),
            "models": ("Data Models", "Database models and entities"),
            "schemas": ("Schemas", "Data validation and serialization schemas"),
            "core": ("Core", "Core application configuration and utilities"),
            "utils": ("Utilities", "Helper functions and utilities"),
            "auth": ("Authentication", "Authentication and authorization"),
            "db": ("Database", "Database connection and queries"),
            "database": ("Database", "Database connection and queries"),
            "middleware": ("Middleware", "Request/response middleware"),
            "tasks": ("Background Tasks", "Async tasks and job processing"),
            "workers": ("Workers", "Background job workers"),
        }

        seen_names = set()
        for d in self.structure.directories:
            dir_name = d.relative_path.name.lower()
            if dir_name in subsystem_patterns and dir_name not in seen_names:
                name, desc = subsystem_patterns[dir_name]
                key_files = [
                    str(f.relative_path) for f in self.structure.files
                    if str(f.relative_path).startswith(str(d.relative_path) + "/")
                    and f.extension == ".py"
                    and "__init__" not in f.relative_path.name
                ][:5]

                subsystems.append(Subsystem(
                    name=name,
                    directory=str(d.relative_path),
                    description=desc,
                    key_files=key_files,
                ))
                seen_names.add(dir_name)

        return subsystems

    def _detect_risk_areas(self) -> list[RiskArea]:
        """Detect risky or fragile areas in the codebase."""
        import re
        risks = []

        for f in self.structure.files:
            if f.content is None:
                continue

            # Skip non-code files for most checks
            is_code = f.extension in [".py", ".js", ".ts", ".java", ".go", ".rb"]

            # Large files
            if f.line_count > 500:
                risks.append(RiskArea(
                    location=str(f.relative_path),
                    risk_type="Large file",
                    description=f"File has {f.line_count} lines, may be difficult to maintain",
                    severity="low",
                ))

            if not is_code:
                continue

            # Raw SQL - potential injection
            if "execute(" in f.content and ("SELECT" in f.content or "INSERT" in f.content or "UPDATE" in f.content or "DELETE" in f.content):
                # Check if it uses parameterized queries
                if not re.search(r'execute\s*\([^,]+,\s*[\[\(]', f.content):
                    risks.append(RiskArea(
                        location=str(f.relative_path),
                        risk_type="Possible SQL injection",
                        description="Raw SQL execution without apparent parameterization detected",
                        severity="high",
                    ))

            # Hardcoded secrets patterns (skip if looks like env var reference)
            secret_patterns = [
                (r'(?<!os\.environ)(?<!getenv)password\s*=\s*["\'][^"\']{4,}["\']', "hardcoded password"),
                (r'(?<!os\.environ)(?<!getenv)secret_key\s*=\s*["\'][^"\']{8,}["\']', "hardcoded secret"),
                (r'(?<!os\.environ)(?<!getenv)api_key\s*=\s*["\'][^"\']{8,}["\']', "hardcoded API key"),
                (r'(?<!os\.environ)(?<!getenv)auth_token\s*=\s*["\'][^"\']{20,}["\']', "hardcoded token"),
                (r'private_key\s*=\s*["\'][^"\']{20,}["\']', "hardcoded private key"),
                (r'AWS_SECRET_ACCESS_KEY\s*=\s*["\'][^"\']+["\']', "AWS secret key"),
                (r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "embedded private key"),
                (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token"),
                (r'sk-[a-zA-Z0-9]{48}', "OpenAI API key pattern"),
            ]
            for pattern, desc in secret_patterns:
                if re.search(pattern, f.content, re.IGNORECASE):
                    # Skip if in test file or example
                    if "test" in str(f.relative_path).lower() or "example" in str(f.relative_path).lower():
                        risks.append(RiskArea(
                            location=str(f.relative_path),
                            risk_type=f"Possible {desc}",
                            description=f"Found {desc} pattern in test/example file - verify it is not a real credential",
                            severity="medium",
                        ))
                    else:
                        risks.append(RiskArea(
                            location=str(f.relative_path),
                            risk_type=f"Possible {desc}",
                            description=f"Detected pattern matching {desc} - review for exposed credentials",
                            severity="high",
                        ))
                    break

            # Insecure configurations
            insecure_patterns = [
                (r'DEBUG\s*=\s*True', "Debug mode enabled", "medium"),
                (r'verify\s*=\s*False', "SSL verification disabled", "high"),
                (r'allow_origins\s*=\s*\["\*"\]', "Permissive CORS configuration", "medium"),
                (r'(?<!["\'])eval\s*\([^)]+\)', "Use of eval()", "high"),
                (r'(?<!["\'])exec\s*\([^)]+\)', "Use of exec()", "high"),
                (r'subprocess\.(run|call|Popen).*shell\s*=\s*True', "Shell injection risk", "high"),
                (r'pickle\.loads?\s*\(', "Pickle deserialization (potential RCE)", "medium"),
                (r'yaml\.load\s*\([^)]*Loader\s*=\s*None', "Unsafe YAML load (use safe_load)", "medium"),
                (r'hashlib\.md5\(|hashlib\.sha1\(', "Weak hash algorithm", "low"),
            ]
            for pattern, desc, severity in insecure_patterns:
                if re.search(pattern, f.content, re.IGNORECASE):
                    risks.append(RiskArea(
                        location=str(f.relative_path),
                        risk_type=desc,
                        description=f"Detected {desc} - review for security implications",
                        severity=severity,
                    ))

            # Missing input validation hints
            if f.extension == ".py" and "route" in str(f.relative_path).lower():
                # Check if route handlers have type hints (basic validation)
                func_defs = re.findall(r'(async )?def\s+\w+\s*\([^)]*\)', f.content)
                untyped = [fd for fd in func_defs if ':' not in fd and 'self' not in fd]
                if len(untyped) > 3:
                    risks.append(RiskArea(
                        location=str(f.relative_path),
                        risk_type="Missing type hints in routes",
                        description=f"Found {len(untyped)} route handlers without type hints - reduces validation",
                        severity="low",
                    ))

            # TODO/FIXME/HACK comments
            todo_count = len(re.findall(r'#\s*(TODO|FIXME|HACK|XXX|BUG)', f.content, re.IGNORECASE))
            if todo_count > 5:
                risks.append(RiskArea(
                    location=str(f.relative_path),
                    risk_type="Technical debt markers",
                    description=f"Contains {todo_count} TODO/FIXME/HACK comments indicating unfinished work",
                    severity="low",
                ))

        # Check test coverage
        test_files = [f for f in self.structure.files if "test" in str(f.relative_path).lower() and f.extension == ".py"]
        code_files = [f for f in self.structure.files if f.extension == ".py" and "test" not in str(f.relative_path).lower()]

        if code_files and len(test_files) < len(code_files) * 0.2:
            risks.append(RiskArea(
                location="tests/",
                risk_type="Limited test coverage",
                description=f"Only {len(test_files)} test files for {len(code_files)} code files (ratio: {len(test_files)/len(code_files)*100:.0f}%)",
                severity="medium",
            ))

        # Check for missing security headers in FastAPI/Flask
        main_files = [f for f in self.structure.files if f.relative_path.name == "main.py" and f.content]
        for mf in main_files:
            if "FastAPI" in mf.content or "Flask" in mf.content:
                if "SecurityMiddleware" not in mf.content and "Strict-Transport-Security" not in mf.content:
                    risks.append(RiskArea(
                        location=str(mf.relative_path),
                        risk_type="Missing security headers",
                        description="No security middleware detected - consider adding HSTS, CSP headers",
                        severity="low",
                    ))

        # Deduplicate and limit
        seen = set()
        unique_risks = []
        for r in risks:
            key = (r.location, r.risk_type)
            if key not in seen:
                seen.add(key)
                unique_risks.append(r)

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        unique_risks.sort(key=lambda r: severity_order.get(r.severity, 3))

        return unique_risks[:30]

    def _detect_patterns(self) -> list[str]:
        """Detect architectural patterns in the codebase."""
        patterns = []

        has_routes = any("route" in str(f.relative_path).lower() for f in self.structure.files)
        has_services = any("service" in str(f.relative_path).lower() for f in self.structure.files)
        has_models = any("model" in str(f.relative_path).lower() for f in self.structure.files)

        if has_routes and has_services and has_models:
            patterns.append("Layered architecture (routes -> services -> models)")

        has_deps = any("dependencies" in str(f.relative_path).lower() or
                      (f.content and "Depends(" in f.content if f.content else False)
                      for f in self.structure.files)
        if has_deps:
            patterns.append("Dependency injection")

        has_schemas = any("schema" in str(f.relative_path).lower() for f in self.structure.files)
        if has_schemas:
            patterns.append("Request/response schema validation")

        has_migrations = any("alembic" in str(f.relative_path).lower() or
                            "migrations" in str(f.relative_path).lower()
                            for f in self.structure.directories)
        if has_migrations:
            patterns.append("Database migrations")

        has_middleware = any("middleware" in str(f.relative_path).lower() for f in self.structure.files)
        if has_middleware:
            patterns.append("Middleware pattern")

        return patterns

    def _trace_request_flow(self) -> RequestFlow | None:
        """Trace a typical request through the system with detailed analysis."""
        import re
        steps = []
        touchpoints = []
        order = 1

        # Find entry point
        entry_file = None
        for f in self.structure.files:
            if f.relative_path.name == "main.py" and len(f.relative_path.parts) <= 2:
                entry_file = f
                break
            elif "app" in str(f.relative_path).lower() and f.relative_path.name == "main.py":
                entry_file = f

        if not entry_file:
            return None

        # Analyze entry file content
        entry_insight = ""
        entry_what = ""
        entry_funcs = []
        if entry_file.content:
            if "FastAPI(" in entry_file.content:
                entry_insight = "Creates a FastAPI application instance"
            if "include_router" in entry_file.content:
                router_count = entry_file.content.count("include_router")
                entry_insight += f", mounts {router_count} router(s)"
            if "on_startup" in entry_file.content or "lifespan" in entry_file.content:
                entry_what = "The app also defines startup/shutdown lifecycle hooks for initializing resources like database connections."
            func_matches = re.findall(r'def\s+(\w+)\s*\(', entry_file.content)
            entry_funcs = [f for f in func_matches if not f.startswith("_")][:3]

        steps.append(RequestFlowStep(
            order=order,
            location="Application Entry",
            description="HTTP request arrives at the ASGI server (uvicorn/gunicorn) which delegates to the FastAPI application instance.",
            file_path=str(entry_file.relative_path),
            code_insight=entry_insight,
            what_happens=entry_what or "The FastAPI app receives the request and begins the routing process.",
            key_functions=entry_funcs,
        ))
        order += 1
        touchpoints.append(f"Entry: {entry_file.relative_path}")

        # Check for middleware
        middleware_files = [f for f in self.structure.files if "middleware" in str(f.relative_path).lower()]
        if middleware_files:
            mw_file = middleware_files[0]
            mw_insight = ""
            mw_what = ""
            if mw_file.content:
                if "CORSMiddleware" in mw_file.content:
                    mw_insight = "CORS middleware configured"
                if "authenticate" in mw_file.content.lower():
                    mw_insight += ", authentication middleware present"
                mw_what = "Before reaching the route handler, requests pass through middleware that can modify requests/responses, handle authentication, add headers, or reject invalid requests."
            steps.append(RequestFlowStep(
                order=order,
                location="Middleware Processing",
                description="Request passes through middleware stack for cross-cutting concerns like CORS, authentication, logging, and error handling.",
                file_path=str(mw_file.relative_path),
                code_insight=mw_insight or "Middleware intercepts all requests",
                what_happens=mw_what,
            ))
            order += 1
            touchpoints.append("Middleware processing")

        # Check for router/routes - pick a representative route file
        route_files = [f for f in self.structure.files
                      if "route" in str(f.relative_path).lower()
                      and f.extension == ".py"
                      and "__init__" not in f.relative_path.name]
        if route_files:
            # Pick the most substantial route file
            route_file = max(route_files, key=lambda x: x.line_count)
            route_insight = ""
            route_what = ""
            route_funcs = []
            if route_file.content:
                # Count endpoints
                endpoints = re.findall(r'@\w+\.(get|post|put|delete|patch)', route_file.content, re.IGNORECASE)
                route_insight = f"Defines {len(endpoints)} endpoint(s)"
                # Find function names
                route_funcs = re.findall(r'async def\s+(\w+)\s*\(|def\s+(\w+)\s*\(', route_file.content)
                route_funcs = [f[0] or f[1] for f in route_funcs if (f[0] or f[1]) and not (f[0] or f[1]).startswith("_")][:5]
                route_what = "The router matches the request URL and HTTP method to a specific handler function. FastAPI automatically validates path parameters and query parameters against type hints."

            steps.append(RequestFlowStep(
                order=order,
                location="Route Matching and Handler",
                description=f"FastAPI router matches the URL path to a handler function. Found {len(route_files)} route file(s) defining the API surface.",
                file_path=str(route_file.relative_path),
                code_insight=route_insight,
                what_happens=route_what,
                key_functions=route_funcs,
            ))
            order += 1
            touchpoints.append(f"Routes: {len(route_files)} route files with {len(endpoints) if route_file.content else 'multiple'} endpoints")

        # Check for dependencies
        dep_files = [f for f in self.structure.files if "dependenc" in str(f.relative_path).lower()]
        if dep_files:
            dep_file = dep_files[0]
            dep_insight = ""
            dep_what = ""
            dep_funcs = []
            if dep_file.content:
                if "get_db" in dep_file.content or "get_session" in dep_file.content:
                    dep_insight = "Provides database session injection"
                if "get_current_user" in dep_file.content:
                    dep_insight += ", user authentication dependency"
                dep_funcs = re.findall(r'def\s+(\w+)\s*\(', dep_file.content)
                dep_funcs = [f for f in dep_funcs if not f.startswith("_")][:5]
                dep_what = "Before the handler executes, FastAPI resolves all dependencies declared in the function signature using Depends(). This typically includes database sessions, authenticated user objects, and other shared resources."

            steps.append(RequestFlowStep(
                order=order,
                location="Dependency Injection",
                description="FastAPI resolves dependencies declared with Depends() - database sessions, authentication, permissions, and other injected resources.",
                file_path=str(dep_file.relative_path),
                code_insight=dep_insight or "Dependencies resolved before handler execution",
                what_happens=dep_what,
                key_functions=dep_funcs,
            ))
            order += 1
            touchpoints.append("Dependency injection")

        # Check for services
        service_files = [f for f in self.structure.files
                        if "service" in str(f.relative_path).lower()
                        and f.extension == ".py"
                        and "__init__" not in f.relative_path.name]
        if service_files:
            svc_file = max(service_files, key=lambda x: x.line_count)
            svc_insight = ""
            svc_what = ""
            svc_funcs = []
            if svc_file.content:
                # Find class name
                class_match = re.search(r'class\s+(\w+)', svc_file.content)
                if class_match:
                    svc_insight = f"Service class: {class_match.group(1)}"
                # Find methods
                svc_funcs = re.findall(r'(?:async )?def\s+(\w+)\s*\(self', svc_file.content)
                svc_funcs = [f for f in svc_funcs if not f.startswith("_")][:5]
                svc_what = "The route handler delegates business logic to service classes. Services encapsulate domain logic, coordinate between multiple data sources, handle transactions, and keep route handlers thin."

            steps.append(RequestFlowStep(
                order=order,
                location="Service Layer (Business Logic)",
                description=f"Business logic executes in service classes. Found {len(service_files)} service file(s) containing domain operations.",
                file_path=str(svc_file.relative_path),
                code_insight=svc_insight,
                what_happens=svc_what,
                key_functions=svc_funcs,
            ))
            order += 1
            touchpoints.append(f"Services: {len(service_files)} service files")

        # Check for models/database
        model_files = [f for f in self.structure.files
                      if "model" in str(f.relative_path).lower()
                      and f.extension == ".py"
                      and "__init__" not in f.relative_path.name]
        if model_files:
            model_file = max(model_files, key=lambda x: x.line_count)
            model_insight = ""
            model_what = ""
            if model_file.content:
                tables = re.findall(r'__tablename__\s*=\s*["\'](\w+)["\']', model_file.content)
                if tables:
                    model_insight = f"Tables: {', '.join(tables[:3])}"
                model_what = "Services interact with the database through SQLAlchemy ORM models. The ORM translates Python objects to SQL queries, handles relationships between entities, and manages the unit of work pattern for transactions."

            steps.append(RequestFlowStep(
                order=order,
                location="Database Layer (ORM)",
                description=f"Data persistence via SQLAlchemy models. Found {len(model_files)} model file(s) defining the database schema.",
                file_path=str(model_file.relative_path),
                code_insight=model_insight or "SQLAlchemy models define database tables",
                what_happens=model_what,
            ))
            order += 1
            touchpoints.append("Database via SQLAlchemy ORM")

        # Response serialization
        schema_files = [f for f in self.structure.files
                       if "schema" in str(f.relative_path).lower()
                       and f.extension == ".py"
                       and "__init__" not in f.relative_path.name]
        if schema_files:
            schema_file = max(schema_files, key=lambda x: x.line_count)
            schema_insight = ""
            schema_what = ""
            if schema_file.content:
                schemas = re.findall(r'class\s+(\w+)\s*\([^)]*BaseModel[^)]*\)', schema_file.content)
                if schemas:
                    schema_insight = f"Schemas: {', '.join(schemas[:4])}"
                schema_what = "Before returning to the client, response data is validated and serialized through Pydantic schemas. This ensures type safety, filters out internal fields, and converts ORM objects to JSON-serializable dictionaries."

            steps.append(RequestFlowStep(
                order=order,
                location="Response Serialization",
                description="Response data validated and serialized through Pydantic schemas before returning JSON to client.",
                file_path=str(schema_file.relative_path),
                code_insight=schema_insight or "Pydantic schemas validate response shape",
                what_happens=schema_what,
            ))
            touchpoints.append("Schema validation on response")

        if len(steps) < 2:
            return None

        return RequestFlow(
            name="Typical API Request Flow",
            description="A detailed walkthrough of how an HTTP request travels through the application layers, from entry to response.",
            steps=steps,
            touchpoints=touchpoints,
        )

    def _recommend_reading_order(self) -> tuple[list[tuple[str, str, int]], list[tuple[str, str]]]:
        """Recommend files to read first and files to skip."""
        first_read: list[tuple[str, str, int]] = []
        skip_files: list[tuple[str, str]] = []
        priority = 1

        # Priority 1: Main entry point
        for f in self.structure.files:
            if f.relative_path.name == "main.py" and len(f.relative_path.parts) <= 2:
                first_read.append((
                    str(f.relative_path),
                    "Application entry point - start here to understand how the app boots",
                    priority,
                ))
                priority += 1
                break

        # Priority 2: Config file
        for f in self.structure.files:
            if "config" in f.relative_path.name.lower() and f.extension == ".py":
                first_read.append((
                    str(f.relative_path),
                    "Configuration - shows environment variables and app settings",
                    priority,
                ))
                priority += 1
                break

        # Priority 3: Models (data structure)
        model_files = [
            f for f in self.structure.files
            if "model" in str(f.relative_path).lower()
            and f.extension == ".py"
            and "__init__" not in f.relative_path.name
            and f.line_count > 10
        ]
        if model_files:
            model_file = max(model_files, key=lambda x: x.line_count)
            first_read.append((
                str(model_file.relative_path),
                "Data models - understand what entities exist in the system",
                priority,
            ))
            priority += 1

        # Priority 4: A route file (API surface)
        route_files = [
            f for f in self.structure.files
            if "route" in str(f.relative_path).lower()
            and f.extension == ".py"
            and "__init__" not in f.relative_path.name
        ]
        if route_files:
            route_file = max(route_files, key=lambda x: x.line_count)
            first_read.append((
                str(route_file.relative_path),
                "API routes - see what endpoints are exposed and how requests are handled",
                priority,
            ))
            priority += 1

        # Priority 5: A service file (business logic)
        service_files = [
            f for f in self.structure.files
            if "service" in str(f.relative_path).lower()
            and f.extension == ".py"
            and "__init__" not in f.relative_path.name
        ]
        if service_files:
            service_file = max(service_files, key=lambda x: x.line_count)
            first_read.append((
                str(service_file.relative_path),
                "Service layer - where the core business logic lives",
                priority,
            ))
            priority += 1

        # Files to skip initially
        skip_patterns = [
            ("alembic/versions/", "Migration files - generated, read only when debugging migrations"),
            ("__pycache__/", "Python cache - auto-generated"),
            ("conftest.py", "Test fixtures - read when writing tests"),
            (".lock", "Lock files - dependency management, not code"),
        ]

        for f in self.structure.files:
            path_str = str(f.relative_path)
            for pattern, reason in skip_patterns:
                if pattern in path_str or path_str.endswith(pattern):
                    skip_files.append((path_str, reason))
                    break

        # Also skip test files initially
        for f in self.structure.files:
            if "test" in str(f.relative_path).lower() and f.extension == ".py":
                if (str(f.relative_path), "Test files - read when you need to understand expected behavior") not in skip_files:
                    skip_files.append((
                        str(f.relative_path),
                        "Test files - read when you need to understand expected behavior",
                    ))

        return first_read, skip_files[:10]

    def _extract_domain_entities(self) -> list[str]:
        """Extract domain entities from model files."""
        import re
        entities = []

        for f in self.structure.files:
            if f.content is None:
                continue
            if "model" in str(f.relative_path).lower() and f.extension == ".py":
                # Look for SQLAlchemy model classes
                class_matches = re.findall(r'class\s+(\w+)\s*\([^)]*Base[^)]*\)', f.content)
                for match in class_matches:
                    if match not in entities and not match.startswith("_"):
                        entities.append(match)

                # Look for table names
                table_matches = re.findall(r'__tablename__\s*=\s*["\'](\w+)["\']', f.content)
                for match in table_matches:
                    entity_name = match.replace("_", " ").title().replace(" ", "")
                    if entity_name not in entities:
                        entities.append(f"{entity_name} (table: {match})")

        return entities[:15]

    def _extract_api_endpoints(self) -> list[tuple[str, str, str]]:
        """Extract API endpoints from route files."""
        import re
        endpoints = []

        for f in self.structure.files:
            if f.content is None:
                continue
            if "route" in str(f.relative_path).lower() and f.extension == ".py":
                # Match FastAPI decorators like @router.get("/path")
                patterns = [
                    r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, f.content, re.IGNORECASE)
                    for method, path in matches:
                        # Try to find the function name/docstring for description
                        desc = f"Endpoint in {f.relative_path.name}"
                        endpoints.append((method.upper(), path, desc))

        return endpoints[:20]

    def _build_detailed_purpose(self, result: AnalysisResult) -> str:
        """Build a detailed purpose description."""
        lines = []

        # Analyze what kind of system this is
        if result.domain_entities:
            entity_names = [e.split(" (")[0] for e in result.domain_entities[:5]]
            lines.append(f"This system manages {', '.join(entity_names).lower()} data.")

        # Describe API surface
        if result.api_endpoints:
            methods = {}
            for method, path, _ in result.api_endpoints:
                methods[method] = methods.get(method, 0) + 1
            method_summary = ", ".join(f"{count} {m}" for m, count in sorted(methods.items()))
            lines.append(f"It exposes a REST API with {len(result.api_endpoints)} endpoints ({method_summary}).")

        # Describe authentication if present
        auth_files = [f for f in self.structure.files if "auth" in str(f.relative_path).lower()]
        if auth_files:
            for f in auth_files:
                if f.content and "jwt" in f.content.lower():
                    lines.append("Authentication is handled via JWT tokens.")
                    break
                elif f.content and "oauth" in f.content.lower():
                    lines.append("Authentication uses OAuth.")
                    break
            else:
                lines.append("The system includes authentication mechanisms.")

        # Describe data persistence
        if any(fw.name == "SQLAlchemy" for fw in result.frameworks):
            lines.append("Data is persisted using SQLAlchemy ORM with a relational database.")
        if any(fw.name == "Alembic" for fw in result.frameworks):
            lines.append("Database schema changes are managed through Alembic migrations.")

        # Check for background tasks
        if any("celery" in str(f.relative_path).lower() or "task" in str(f.relative_path).lower()
               for f in self.structure.files):
            lines.append("Background task processing appears to be supported.")

        return " ".join(lines) if lines else "Unable to determine detailed purpose from code analysis."
