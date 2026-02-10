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
class ImportTarget:
    module: str
    attr: str | None


@dataclass
class RouterInclude:
    source_file: str
    child_file: str
    prefix: str


@dataclass
class PythonAstAnalyzer:
    """Analyze Python files using AST parsing."""

    def analyze(self, structure: RepoStructure) -> FactBundle:
        bundle = FactBundle()
        route_facts: list[Fact] = []
        include_edges: list[RouterInclude] = []
        file_by_module, module_by_file = self._build_module_index(structure)

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
            router_prefixes = self._router_prefixes(tree)
            route_facts.extend(self._route_facts(tree, file_info, router_prefixes))
            bundle.facts.extend(self._model_facts(tree, file_info))

            import_map = self._build_import_map(tree, module_by_file.get(str(file_info.relative_path)))
            include_edges.extend(
                self._include_router_edges(
                    tree,
                    file_info,
                    import_map,
                    file_by_module,
                    set(router_prefixes.keys()),
                )
            )

        self._apply_include_prefixes(route_facts, include_edges)
        bundle.facts.extend(route_facts)

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

    def _route_facts(
        self,
        tree: ast.AST,
        file_info: FileInfo,
        router_prefixes: dict[str, str],
    ) -> list[Fact]:
        facts: list[Fact] = []
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

    def _build_module_index(self, structure: RepoStructure) -> tuple[dict[str, str], dict[str, str]]:
        file_by_module: dict[str, str] = {}
        module_by_file: dict[str, str] = {}
        for file_info in self._python_files(structure):
            rel = file_info.relative_path
            if rel.name == "__init__.py":
                module_path = ".".join(rel.parent.parts)
            else:
                module_path = ".".join(rel.with_suffix("").parts)
            if not module_path:
                continue
            file_by_module[module_path] = str(rel)
            module_by_file[str(rel)] = module_path
        return file_by_module, module_by_file

    def _build_import_map(self, tree: ast.AST, current_module: str | None) -> dict[str, ImportTarget]:
        import_map: dict[str, ImportTarget] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        import_map[alias.asname] = ImportTarget(module=alias.name, attr=None)
            elif isinstance(node, ast.ImportFrom):
                module = self._resolve_import_module(node.module, current_module, node.level)
                if not module:
                    continue
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    import_map[local] = ImportTarget(module=module, attr=alias.name)
        return import_map

    def _resolve_import_module(
        self,
        module: str | None,
        current_module: str | None,
        level: int,
    ) -> str | None:
        if level <= 0:
            return module
        if not current_module:
            return module
        parts = current_module.split(".")
        if level > len(parts):
            base = []
        else:
            base = parts[:-level]
        if module:
            base.append(module)
        return ".".join([p for p in base if p])

    def _include_router_edges(
        self,
        tree: ast.AST,
        file_info: FileInfo,
        import_map: dict[str, ImportTarget],
        file_by_module: dict[str, str],
        router_names: set[str],
    ) -> list[RouterInclude]:
        edges: list[RouterInclude] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "include_router":
                continue
            prefix = self._extract_prefix(node)
            if not prefix:
                continue
            if not node.args:
                continue
            child_file = self._resolve_router_target(
                node.args[0],
                import_map,
                file_by_module,
                str(file_info.relative_path),
                router_names,
            )
            if not child_file:
                continue
            edges.append(RouterInclude(source_file=str(file_info.relative_path), child_file=child_file, prefix=prefix))
        return edges

    def _extract_prefix(self, node: ast.Call) -> str | None:
        for keyword in node.keywords:
            if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant):
                if isinstance(keyword.value.value, str):
                    return keyword.value.value
        return None

    def _resolve_router_target(
        self,
        target: ast.AST,
        import_map: dict[str, ImportTarget],
        file_by_module: dict[str, str],
        default_file: str,
        router_names: set[str],
    ) -> str | None:
        if isinstance(target, ast.Name):
            name = target.id
            if name in import_map:
                mapped = import_map[name]
                if mapped.attr and mapped.attr != "router":
                    return None
                return file_by_module.get(mapped.module)
            if name in router_names:
                return default_file
            return None
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            base_name = target.value.id
            if base_name in import_map:
                mapped = import_map[base_name]
                if mapped.attr:
                    return None
                return file_by_module.get(mapped.module)
        return None

    def _apply_include_prefixes(self, route_facts: list[Fact], edges: list[RouterInclude]) -> None:
        if not edges:
            return
        prefixes_by_file = self._build_prefix_map(edges)
        for fact in route_facts:
            path = fact.attributes.get("path")
            file_path = fact.attributes.get("file")
            if not path or not file_path:
                continue
            prefixes = prefixes_by_file.get(file_path)
            if not prefixes:
                continue
            prefix = max(prefixes, key=len)
            if path.startswith(prefix):
                continue
            new_path = self._join_path(prefix, path)
            fact.attributes["path"] = new_path
            method = fact.attributes.get("method", "")
            fact.summary = f"{method} {new_path}".strip()

    def _build_prefix_map(self, edges: list[RouterInclude]) -> dict[str, list[str]]:
        outgoing: dict[str, list[RouterInclude]] = {}
        incoming: dict[str, int] = {}
        nodes: set[str] = set()
        for edge in edges:
            outgoing.setdefault(edge.source_file, []).append(edge)
            incoming[edge.child_file] = incoming.get(edge.child_file, 0) + 1
            nodes.add(edge.source_file)
            nodes.add(edge.child_file)
        roots = [node for node in nodes if incoming.get(node, 0) == 0]
        prefixes_by_file: dict[str, list[str]] = {}
        for root in roots:
            self._walk_prefixes(root, "", outgoing, prefixes_by_file, set())
        return prefixes_by_file

    def _walk_prefixes(
        self,
        node: str,
        current_prefix: str,
        outgoing: dict[str, list[RouterInclude]],
        prefixes_by_file: dict[str, list[str]],
        seen: set[tuple[str, str]],
    ) -> None:
        for edge in outgoing.get(node, []):
            combined = self._join_path(current_prefix, edge.prefix)
            key = (edge.child_file, combined)
            if key in seen:
                continue
            seen.add(key)
            prefixes_by_file.setdefault(edge.child_file, []).append(combined)
            self._walk_prefixes(edge.child_file, combined, outgoing, prefixes_by_file, seen)

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
