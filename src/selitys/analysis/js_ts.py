"""JavaScript and TypeScript analyzer using tree-sitter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from selitys.analysis.model import Confidence, Evidence, Fact, FactBundle, FactKind
from selitys.core.scanner import FileInfo, RepoStructure

try:
    from tree_sitter_languages import get_parser
except Exception:  # pragma: no cover - optional dependency handling
    get_parser = None


IMPORT_FRAMEWORKS = {
    "express": ("Express", "Web Framework (Node.js)"),
    "next": ("Next.js", "React Framework"),
    "react": ("React", "UI Library"),
    "@nestjs/core": ("NestJS", "Web Framework (Node.js)"),
    "fastify": ("Fastify", "Web Framework (Node.js)"),
    "koa": ("Koa", "Web Framework (Node.js)"),
}

ROUTE_METHODS = {"get", "post", "put", "delete", "patch"}
ROUTE_RECEIVERS = {"app", "router", "api", "server"}


@dataclass
class JsTsAnalyzer:
    """Analyze JS/TS files with tree-sitter parsers."""

    def analyze(self, structure: RepoStructure) -> FactBundle:
        bundle = FactBundle()
        if get_parser is None:
            return bundle

        for file_info in self._js_ts_files(structure):
            if not file_info.content:
                continue
            parser = self._select_parser(file_info)
            if parser is None:
                continue
            tree = parser.parse(file_info.content.encode("utf-8"))
            source_bytes = file_info.content.encode("utf-8")

            bundle.facts.extend(self._framework_facts(tree.root_node, source_bytes, file_info))
            bundle.facts.extend(self._route_facts(tree.root_node, source_bytes, file_info))

        return bundle

    def _js_ts_files(self, structure: RepoStructure) -> Iterable[FileInfo]:
        return (
            f
            for f in structure.files
            if f.extension in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
        )

    def _select_parser(self, file_info: FileInfo):
        if get_parser is None:
            return None
        if file_info.extension in {".ts"}:
            return get_parser("typescript")
        if file_info.extension in {".tsx"}:
            return get_parser("tsx")
        return get_parser("javascript")

    def _framework_facts(self, node, source_bytes: bytes, file_info: FileInfo) -> list[Fact]:
        facts: list[Fact] = []
        for child in self._walk(node):
            if child.type == "import_statement":
                module_name = self._extract_import_source(child, source_bytes)
                if not module_name:
                    continue
                if module_name in IMPORT_FRAMEWORKS:
                    name, category = IMPORT_FRAMEWORKS[module_name]
                    facts.append(
                        Fact(
                            kind=FactKind.FRAMEWORK,
                            summary=f"{name} ({category})",
                            confidence=Confidence.HIGH,
                            evidence=[self._evidence(file_info, child, symbol=module_name)],
                            attributes={"name": name, "category": category},
                        )
                    )
            elif child.type == "call_expression":
                if self._is_require_call(child, source_bytes):
                    module_name = self._extract_require_source(child, source_bytes)
                    if module_name and module_name in IMPORT_FRAMEWORKS:
                        name, category = IMPORT_FRAMEWORKS[module_name]
                        facts.append(
                            Fact(
                                kind=FactKind.FRAMEWORK,
                                summary=f"{name} ({category})",
                                confidence=Confidence.HIGH,
                                evidence=[self._evidence(file_info, child, symbol=module_name)],
                                attributes={"name": name, "category": category},
                            )
                        )
        return self._dedupe_facts(facts)

    def _route_facts(self, node, source_bytes: bytes, file_info: FileInfo) -> list[Fact]:
        facts: list[Fact] = []
        for child in self._walk(node):
            if child.type != "call_expression":
                continue
            method, path = self._extract_route_call(child, source_bytes)
            if not method:
                continue
            summary = f"{method} {path or '<path>'}"
            facts.append(
                Fact(
                    kind=FactKind.ROUTE,
                    summary=summary,
                    confidence=Confidence.MEDIUM if path is None else Confidence.HIGH,
                    evidence=[self._evidence(file_info, child, symbol=method)],
                    attributes={
                        "method": method,
                        "path": path,
                        "file": str(file_info.relative_path),
                    },
                )
            )
        return facts

    def _extract_import_source(self, node, source_bytes: bytes) -> str | None:
        for child in node.children:
            if child.type == "string":
                return self._strip_quotes(self._node_text(child, source_bytes))
        return None

    def _is_require_call(self, node, source_bytes: bytes) -> bool:
        if node.child_by_field_name("function") is None:
            return False
        func = node.child_by_field_name("function")
        if func and func.type == "identifier":
            return self._node_text(func, source_bytes) == "require"
        return False

    def _extract_require_source(self, node, source_bytes: bytes) -> str | None:
        args = node.child_by_field_name("arguments")
        if not args:
            return None
        for child in args.children:
            if child.type == "string":
                return self._strip_quotes(self._node_text(child, source_bytes))
        return None

    def _extract_route_call(self, node, source_bytes: bytes) -> tuple[str | None, str | None]:
        func = node.child_by_field_name("function")
        if func is None or func.type != "member_expression":
            return None, None
        object_node = func.child_by_field_name("object")
        if object_node and object_node.type == "identifier":
            receiver = self._node_text(object_node, source_bytes)
            receiver_lower = receiver.lower()
            if receiver_lower not in ROUTE_RECEIVERS and not receiver_lower.endswith("router"):
                return None, None
        property_node = func.child_by_field_name("property")
        if not property_node:
            return None, None
        method = self._node_text(property_node, source_bytes)
        if method not in ROUTE_METHODS:
            return None, None
        path = None
        args = node.child_by_field_name("arguments")
        if args:
            for child in args.children:
                if child.type == "string":
                    path = self._strip_quotes(self._node_text(child, source_bytes))
                    break
        return method.upper(), path

    def _node_text(self, node, source_bytes: bytes) -> str:
        return source_bytes[node.start_byte:node.end_byte].decode("utf-8")

    def _strip_quotes(self, text: str) -> str:
        return text.strip("\"'`")

    def _evidence(self, file_info: FileInfo, node, symbol: str | None = None) -> Evidence:
        start_line = node.start_point[0] + 1 if node.start_point else None
        end_line = node.end_point[0] + 1 if node.end_point else None
        return Evidence(
            file_path=str(file_info.relative_path),
            line_start=start_line,
            line_end=end_line,
            symbol=symbol,
        )

    def _walk(self, node):
        stack = [node]
        while stack:
            current = stack.pop()
            yield current
            stack.extend(reversed(current.children))

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
