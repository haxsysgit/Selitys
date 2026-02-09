import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from selitys.analysis import PythonAstAnalyzer  # noqa: E402
from selitys.analysis.model import FactKind  # noqa: E402
from selitys.core.scanner import RepoScanner  # noqa: E402


class TestPythonAstAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_path = ROOT / "fixtures" / "test_backend"
        if not cls.repo_path.exists():
            raise unittest.SkipTest("fixtures/test_backend is missing")

    def test_extracts_frameworks_routes_and_models(self) -> None:
        structure = RepoScanner(self.repo_path).scan()
        facts = PythonAstAnalyzer().analyze(structure).facts

        frameworks = [f for f in facts if f.kind == FactKind.FRAMEWORK]
        framework_names = {f.attributes.get("name") or f.summary for f in frameworks}
        self.assertIn("FastAPI", framework_names)
        self.assertIn("SQLAlchemy", framework_names)

        routes = [f for f in facts if f.kind == FactKind.ROUTE]
        self.assertTrue(any(f.attributes.get("path") == "/register" for f in routes))

        entities = [f for f in facts if f.kind == FactKind.DOMAIN_ENTITY]
        self.assertGreater(len(entities), 0)

    def test_extracts_entry_point(self) -> None:
        structure = RepoScanner(self.repo_path).scan()
        facts = PythonAstAnalyzer().analyze(structure).facts
        entry_points = [f for f in facts if f.kind == FactKind.ENTRY_POINT]
        entry_paths = {f.attributes.get("file") for f in entry_points}
        self.assertIn("app/main.py", entry_paths)


if __name__ == "__main__":
    unittest.main()
