import unittest
from pathlib import Path
import sys
import tempfile

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
        self.assertTrue(any(f.attributes.get("path") == "/auth/register" for f in routes))

        entities = [f for f in facts if f.kind == FactKind.DOMAIN_ENTITY]
        self.assertGreater(len(entities), 0)

    def test_extracts_entry_point(self) -> None:
        structure = RepoScanner(self.repo_path).scan()
        facts = PythonAstAnalyzer().analyze(structure).facts
        entry_points = [f for f in facts if f.kind == FactKind.ENTRY_POINT]
        entry_paths = {f.attributes.get("file") for f in entry_points}
        self.assertIn("app/main.py", entry_paths)

    def test_router_prefix_from_imported_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            routes_dir = root / "app" / "api" / "routes"
            routes_dir.mkdir(parents=True)
            (routes_dir / "__init__.py").write_text("", encoding="utf-8")
            (routes_dir / "auth_route.py").write_text(
                "from fastapi import APIRouter\n"
                "router = APIRouter()\n"
                "@router.get(\"/ping\")\n"
                "def ping():\n"
                "    return {\"ok\": True}\n",
                encoding="utf-8",
            )
            router_file = root / "app" / "api" / "router.py"
            router_file.parent.mkdir(parents=True, exist_ok=True)
            router_file.write_text(
                "from fastapi import APIRouter\n"
                "from app.api.routes import auth_route\n"
                "api_router = APIRouter()\n"
                "api_router.include_router(auth_route.router, prefix=\"/auth\")\n",
                encoding="utf-8",
            )

            structure = RepoScanner(root).scan()
            facts = PythonAstAnalyzer().analyze(structure).facts
            routes = [f for f in facts if f.kind == FactKind.ROUTE]
            paths = {f.attributes.get("path") for f in routes}
            self.assertIn("/auth/ping", paths)


if __name__ == "__main__":
    unittest.main()
