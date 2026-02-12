"""Tests for the FastAPI backend endpoints."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.app import app


client = TestClient(app)

FIXTURE_REPO = ROOT / "fixtures" / "test_backend"


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAnalyzeEndpoint:
    @pytest.fixture(autouse=True)
    def check_fixture(self):
        if not FIXTURE_REPO.exists():
            pytest.skip("fixtures/test_backend missing")

    def test_analyze_success(self):
        resp = client.post("/api/analyze", json={"repo_path": str(FIXTURE_REPO)})
        assert resp.status_code == 200
        data = resp.json()
        assert data["repo_name"] == "test_backend"
        assert data["total_files"] > 0
        assert data["total_lines"] > 0
        assert len(data["frameworks"]) > 0

    def test_analyze_includes_dependency_graph(self):
        resp = client.post("/api/analyze", json={"repo_path": str(FIXTURE_REPO)})
        data = resp.json()
        graph = data["dependency_graph"]
        assert "nodes" in graph
        assert "edges" in graph
        assert "layers" in graph
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0

    def test_analyze_invalid_path(self):
        resp = client.post("/api/analyze", json={"repo_path": "/nonexistent/path"})
        assert resp.status_code == 400

    def test_analyze_dependency_node_fields(self):
        resp = client.post("/api/analyze", json={"repo_path": str(FIXTURE_REPO)})
        data = resp.json()
        node = data["dependency_graph"]["nodes"][0]
        assert "path" in node
        assert "label" in node
        assert "node_type" in node
        assert "imports_count" in node
        assert "imported_by_count" in node

    def test_analyze_dependency_edge_fields(self):
        resp = client.post("/api/analyze", json={"repo_path": str(FIXTURE_REPO)})
        data = resp.json()
        edge = data["dependency_graph"]["edges"][0]
        assert "source" in edge
        assert "target" in edge
        assert "import_name" in edge


class TestAskEndpoint:
    @pytest.fixture(autouse=True)
    def check_fixture(self):
        if not FIXTURE_REPO.exists():
            pytest.skip("fixtures/test_backend missing")

    def test_ask_keyword(self):
        resp = client.post("/api/ask", json={
            "repo_path": str(FIXTURE_REPO),
            "question": "what frameworks are used?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data or "answer" in data
