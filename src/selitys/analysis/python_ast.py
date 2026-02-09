"""Python AST analyzer for extracting structured facts."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Iterable

from selitys.analysis.model import Confidence, Evidence, Fact, FactBundle, FactKind
from selitys.core.scanner import FileInfo, RepoStructure


FRAMEWORK_MODULES = {
    "fastapi": ("FastAPI", "Web Framework"),
    "flask": ("Flask", "Web Framework"),
    "django": ("Django", "Web Framework"),
    "sqlalchemy": ("SQLAlchemy", "ORM"),
    "pydantic": ("Pydantic", "Data Validation"),
    "alembic": ("Alembic", "Database Migrations"),
    "celery": ("Celery", "Task Queue"),
    "redis": ("Redis", "Cache/Message Broker"),
}

ROUTE_METHODS = {"get", "post", "put", "delete", "patch"}


@dataclass
class PythonAstAnalyzer:
    """Analyze Python files using AST parsing."""

    def analyze(self, structure: RepoStructure) -> FactBundle:
        bundle = FactBundle()

        for file_info in self._python_files(structure):
            if not file_info.content:
                continue
            try:
                tree = ast.parse(file_info.content)
            except SyntaxError:
                continue

            entry_facts = self._entry_point_facts(file_info)
            bundle.facts.extend(entry_facts)
            entry_files = {fact.attributes.get("file") for fact in entry_facts}
            bundle.facts.extend(self._fastapi_app_facts(tree, file_info, entry_files))
            bundle.facts.extend(self._framework_facts(tree, file_info))
            bundle.facts.extend(self._route_facts(tree, file_info))
            bundle.facts.extend(self._model_facts(tree, file_info))

        return bundle

    def _python_files(self, structure: RepoStructure) -> Iterable[FileInfo]:
        return (f for f in structure.files if f.extension == ".py")

    def _entry_point_facts(self, file_info: FileInfo) -> list[Fact]:
        name = file_info.relative_path.name
        if name not in {"main.py", "app.py", "manage.py", "wsgi.py", "asgi.py"}:
            return []

        description = {
            "main.py": "Application entry point",
            "app.py": "Application factory or entry point",
            "manage.py": "Django management script",
            "wsgi.py": "WSGI application entry",
            "asgi.py": "ASGI application entry",
        }.get(name, "Application entry point")

        return [
            Fact(
                kind=FactKind.ENTRY_POINT,
                summary=description,
                confidence=Confidence.HIGH,
                evidence=[Evidence(file_path=str(file_info.relative_path), line_start=1, line_end=1)],
                attributes={"file": str(file_info.relative_path)},
            )
        ]

    def _fastapi_app_facts(
        self,
        tree: ast.AST,
        file_info: FileInfo,
        existing_entry_files: set[str | None],
    ) -> list[Fact]:
        if str(file_info.relative_path) in existing_entry_files:
            return []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "FastAPI":
                    return [
                        Fact(
                            kind=FactKind.ENTRY_POINT,
                            summary="FastAPI application instance",
                            confidence=Confidence.HIGH,
                            evidence=[self._evidence(file_info, node, symbol="FastAPI")],
                            attributes={"file": str(file_info.relative_path)},
                        )
                    ]
        return []

    def _framework_facts(self, tree: ast.AST, file_info: FileInfo) -> list[Fact]:
        facts: list[Fact] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in FRAMEWORK_MODULES:
                        name, category = FRAMEWORK_MODULES[top]
                        facts.append(
                            Fact(
                                kind=FactKind.FRAMEWORK,
                                summary=f"{name} ({category})",
                                confidence=Confidence.HIGH,
                                evidence=[self._evidence(file_info, node, symbol=alias.name)],
                                attributes={"name": name, "category": category},
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if top in FRAMEWORK_MODULES:
                        name, category = FRAMEWORK_MODULES[top]
                        facts.append(
                            Fact(
                                kind=FactKind.FRAMEWORK,
                                summary=f"{name} ({category})",
                                confidence=Confidence.HIGH,
                                evidence=[self._evidence(file_info, node, symbol=node.module)],
                                attributes={"name": name, "category": category},
                            )
                        )
        return self._dedupe_facts(facts)

    def _route_facts(self, tree: ast.AST, file_info: FileInfo) -> list[Fact]:
        facts: list[Fact] = []
        router_prefixes = self._router_prefixes(tree)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    call = decorator if isinstance(decorator, ast.Call) else None
                    if not call or not isinstance(call.func, ast.Attribute):
                        continue
                    method = call.func.attr.lower()
                    if method not in ROUTE_METHODS:
                        continue
                    path = None
                    if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, str):
                        path = call.args[0].value
                    router_name = None
                    if isinstance(call.func.value, ast.Name):
                        router_name = call.func.value.id
                    if router_name and path:
                        prefix = router_prefixes.get(router_name)
                        if prefix:
                            path = self._join_path(prefix, path)
                    summary = f"{method.upper()} {path or '<path>'}"
                    facts.append(
                        Fact(
                            kind=FactKind.ROUTE,
                            summary=summary,
                            confidence=Confidence.MEDIUM if path is None else Confidence.HIGH,
                            evidence=[self._evidence(file_info, call, symbol=node.name)],
                            attributes={
                                "method": method.upper(),
                                "path": path,
                                "handler": node.name,
                                "router": router_name,
                                "file": str(file_info.relative_path),
                            },
                        )
                    )
        return facts

    def _model_facts(self, tree: ast.AST, file_info: FileInfo) -> list[Fact]:
        facts: list[Fact] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            base_names = self._base_names(node)
            if not base_names:
                continue
            if not self._looks_like_model(base_names):
                continue
            table_name = self._find_table_name(node)
            summary = f"Model class {node.name}"
            if table_name:
                summary = f"Model class {node.name} (table: {table_name})"
            facts.append(
                Fact(
                    kind=FactKind.DOMAIN_ENTITY,
                    summary=summary,
                    confidence=Confidence.MEDIUM,
                    evidence=[self._evidence(file_info, node, symbol=node.name)],
                    attributes={
                        "class": node.name,
                        "table": table_name,
                        "file": str(file_info.relative_path),
                    },
                )
            )
        return facts

    def _base_names(self, node: ast.ClassDef) -> list[str]:
        names: list[str] = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                names.append(base.id)
            elif isinstance(base, ast.Attribute):
                names.append(base.attr)
        return names

    def _looks_like_model(self, base_names: list[str]) -> bool:
        for name in base_names:
            if name in {"Base", "DeclarativeBase"}:
                return True
            if name.endswith("Base"):
                return True
        return False

    def _find_table_name(self, node: ast.ClassDef) -> str | None:
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "__tablename__":
                        if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                            return stmt.value.value
        return None

    def _router_prefixes(self, tree: ast.AST) -> dict[str, str]:
        prefixes: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id == "APIRouter":
                    prefix = None
                    for keyword in node.value.keywords:
                        if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant):
                            if isinstance(keyword.value.value, str):
                                prefix = keyword.value.value
                    if prefix:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                prefixes[target.id] = prefix
        return prefixes

    def _join_path(self, prefix: str, path: str) -> str:
        if not prefix:
            return path
        if prefix.endswith("/") and path.startswith("/"):
            return prefix[:-1] + path
        if not prefix.endswith("/") and not path.startswith("/"):
            return prefix + "/" + path
        return prefix + path

    def _evidence(self, file_info: FileInfo, node: ast.AST, symbol: str | None = None) -> Evidence:
        return Evidence(
            file_path=str(file_info.relative_path),
            line_start=getattr(node, "lineno", None),
            line_end=getattr(node, "end_lineno", None),
            symbol=symbol,
        )

    def _dedupe_facts(self, facts: list[Fact]) -> list[Fact]:
        seen = set()
        unique: list[Fact] = []
        for fact in facts:
            key = (fact.kind, fact.summary)
            if key in seen:
                continue
            seen.add(key)
            unique.append(fact)
        return unique
