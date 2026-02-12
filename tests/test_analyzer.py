"""Tests for the Analyzer — dependency graph, layers, import resolution."""

import tempfile
from pathlib import Path

import pytest

from selitys.core.scanner import RepoScanner
from selitys.core.analyzer import Analyzer, DependencyGraph, DependencyEdge, DependencyNode


@pytest.fixture
def py_repo(tmp_path):
    """Python repo with clear dependency structure."""
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("")
    (tmp_path / "app" / "main.py").write_text(
        "from app.routes import router\n"
        "from app.config import settings\n"
        "from app.db import get_db\n"
    )
    (tmp_path / "app" / "config.py").write_text("settings = {'debug': True}\n")
    (tmp_path / "app" / "db.py").write_text(
        "from app.config import settings\n"
        "def get_db(): pass\n"
    )
    (tmp_path / "app" / "routes.py").write_text(
        "from app.db import get_db\n"
        "from app.models import User\n"
        "router = None\n"
    )
    (tmp_path / "app" / "models.py").write_text(
        "from app.db import get_db\n"
        "class User: pass\n"
    )
    (tmp_path / "app" / "services.py").write_text(
        "from app.models import User\n"
        "from app.db import get_db\n"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text(
        "from app.main import router\n"
    )
    return tmp_path


@pytest.fixture
def js_repo(tmp_path):
    """JS repo with relative imports."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.js").write_text(
        "import { App } from './app'\n"
        "import { config } from './config'\n"
    )
    (tmp_path / "src" / "app.js").write_text(
        "import { db } from './db'\n"
        "export const App = {}\n"
    )
    (tmp_path / "src" / "db.js").write_text(
        "import { config } from './config'\n"
        "export const db = {}\n"
    )
    (tmp_path / "src" / "config.js").write_text("export const config = {}\n")
    return tmp_path


class TestAnalyzerBasic:
    def test_analyze_returns_result(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        assert result.repo_name == py_repo.name
        assert result.likely_purpose

    def test_analyze_detects_dependency_graph(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        graph = result.dependency_graph
        assert isinstance(graph, DependencyGraph)
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0


class TestDependencyGraph:
    def test_python_edges_detected(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        graph = result.dependency_graph
        edge_pairs = {(e.source, e.target) for e in graph.edges}
        # main.py imports routes, config, db
        assert ("app/main.py", "app/routes.py") in edge_pairs
        assert ("app/main.py", "app/config.py") in edge_pairs
        assert ("app/main.py", "app/db.py") in edge_pairs

    def test_no_self_edges(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        for e in result.dependency_graph.edges:
            assert e.source != e.target, f"Self-edge found: {e.source}"

    def test_edges_are_deduplicated(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        edge_pairs = [(e.source, e.target) for e in result.dependency_graph.edges]
        assert len(edge_pairs) == len(set(edge_pairs)), "Duplicate edges found"

    def test_node_import_counts(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        node_map = {n.path: n for n in result.dependency_graph.nodes}
        # config.py is imported by main.py and db.py
        assert node_map["app/config.py"].imported_by_count >= 2
        # main.py imports 3 things
        assert node_map["app/main.py"].imports_count >= 3

    def test_js_edges_detected(self, js_repo):
        structure = RepoScanner(js_repo).scan()
        result = Analyzer(structure).analyze()
        graph = result.dependency_graph
        edge_pairs = {(e.source, e.target) for e in graph.edges}
        assert ("src/index.js", "src/app.js") in edge_pairs
        assert ("src/index.js", "src/config.js") in edge_pairs
        assert ("src/app.js", "src/db.js") in edge_pairs

    def test_js_skips_node_modules(self, js_repo):
        # Add an npm import that should be ignored
        (js_repo / "src" / "utils.js").write_text(
            "import React from 'react'\n"
            "import { config } from './config'\n"
        )
        structure = RepoScanner(js_repo).scan()
        result = Analyzer(structure).analyze()
        for e in result.dependency_graph.edges:
            assert "react" not in e.target


class TestLayers:
    def test_layers_detected(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        layer_types = {l["type"] for l in result.dependency_graph.layers}
        # Should have at least some layers
        assert len(result.dependency_graph.layers) > 0

    def test_layers_contain_valid_files(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        node_paths = {n.path for n in result.dependency_graph.nodes}
        for layer in result.dependency_graph.layers:
            for f in layer["files"]:
                assert f in node_paths, f"{f} in layer but not in nodes"

    def test_test_files_classified(self, py_repo):
        structure = RepoScanner(py_repo).scan()
        result = Analyzer(structure).analyze()
        node_map = {n.path: n for n in result.dependency_graph.nodes}
        test_file = node_map.get("tests/test_main.py")
        if test_file:
            assert test_file.node_type == "test"


class TestFixtureRepo:
    """Tests against the full fixtures/test_backend repo."""

    @pytest.fixture(autouse=True)
    def setup(self):
        repo = Path(__file__).resolve().parents[1] / "fixtures" / "test_backend"
        if not repo.exists():
            pytest.skip("fixtures/test_backend missing")
        self.structure = RepoScanner(repo).scan()
        self.result = Analyzer(self.structure).analyze()

    def test_has_many_nodes(self):
        assert len(self.result.dependency_graph.nodes) >= 20

    def test_has_many_edges(self):
        assert len(self.result.dependency_graph.edges) >= 50

    def test_detects_entry_points(self):
        ep_paths = {ep.path for ep in self.result.entry_points}
        assert any("main.py" in p for p in ep_paths)

    def test_detects_frameworks(self):
        fw_names = {fw.name for fw in self.result.frameworks}
        assert "FastAPI" in fw_names or "SQLAlchemy" in fw_names

    def test_layers_include_routes_and_models(self):
        layer_types = {l["type"] for l in self.result.dependency_graph.layers}
        assert "route" in layer_types
        assert "model" in layer_types

    def test_config_detected(self):
        assert len(self.result.config.config_files) > 0
