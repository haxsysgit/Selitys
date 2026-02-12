"""Tests for the RepoScanner."""

import tempfile
from pathlib import Path

import pytest

from selitys.core.scanner import RepoScanner


@pytest.fixture
def mini_repo(tmp_path):
    """Create a minimal Python repo structure."""
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("")
    (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
    (tmp_path / "app" / "config.py").write_text("DB_URL = 'sqlite:///db.sqlite'\n")
    (tmp_path / "app" / "models.py").write_text("class User:\n    pass\n")
    (tmp_path / "requirements.txt").write_text("fastapi\n")
    (tmp_path / "README.md").write_text("# Test\n")
    return tmp_path


class TestRepoScanner:
    def test_scan_finds_files(self, mini_repo):
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        rel_paths = {str(f.relative_path) for f in structure.files}
        assert "app/main.py" in rel_paths
        assert "app/config.py" in rel_paths
        assert "app/models.py" in rel_paths

    def test_scan_counts_lines(self, mini_repo):
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        assert structure.total_lines > 0

    def test_scan_detects_languages(self, mini_repo):
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        assert "Python" in structure.languages_detected

    def test_scan_reads_content(self, mini_repo):
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        main = next(f for f in structure.files if f.relative_path.name == "main.py")
        assert main.content is not None
        assert "FastAPI" in main.content

    def test_scan_respects_max_file_size(self, mini_repo):
        big_file = mini_repo / "big.py"
        big_file.write_text("x = 1\n" * 10000)
        scanner = RepoScanner(mini_repo, max_file_size_bytes=100)
        structure = scanner.scan()
        big = next((f for f in structure.files if f.relative_path.name == "big.py"), None)
        # File should be skipped or have no content
        assert big is None or big.content is None

    def test_scan_ignores_node_modules(self, mini_repo):
        nm = mini_repo / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = {}")
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        rel_paths = {str(f.relative_path) for f in structure.files}
        assert not any("node_modules" in p for p in rel_paths)

    def test_scan_ignores_venv(self, mini_repo):
        venv = mini_repo / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "site.py").write_text("pass")
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        rel_paths = {str(f.relative_path) for f in structure.files}
        assert not any(".venv" in p for p in rel_paths)

    def test_scan_with_exclude_patterns(self, mini_repo):
        scanner = RepoScanner(mini_repo, exclude_patterns=["*.md"])
        structure = scanner.scan()
        rel_paths = {str(f.relative_path) for f in structure.files}
        assert "README.md" not in rel_paths

    def test_get_top_level_items(self, mini_repo):
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        dirs, files = structure.get_top_level_items()
        dir_names = {d.relative_path.name for d in dirs}
        assert "app" in dir_names

    def test_find_file(self, mini_repo):
        scanner = RepoScanner(mini_repo)
        structure = scanner.scan()
        found = structure.find_file("main.py")
        assert found is not None
        assert found.relative_path.name == "main.py"
        assert structure.find_file("nonexistent.py") is None
