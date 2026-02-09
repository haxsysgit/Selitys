import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from selitys import __version__  # noqa: E402
from selitys.core.analyzer import Analyzer  # noqa: E402
from selitys.core.scanner import RepoScanner  # noqa: E402
from selitys.output.generator import MarkdownGenerator  # noqa: E402


class TestOutputGeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_path = ROOT / "fixtures" / "test_backend"
        if not cls.repo_path.exists():
            raise unittest.SkipTest("fixtures/test_backend is missing")

    def test_overview_includes_fact_sources(self) -> None:
        structure = RepoScanner(self.repo_path).scan()
        analysis = Analyzer(structure).analyze()
        generator = MarkdownGenerator(structure, analysis)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "selitys-overview.md"
            generator.generate_overview(output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("auth_route.py", content)
        self.assertIn("Frameworks and Libraries", content)

    def test_json_includes_fact_bundle(self) -> None:
        structure = RepoScanner(self.repo_path).scan()
        analysis = Analyzer(structure).analyze()
        generator = MarkdownGenerator(structure, analysis)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "selitys-analysis.json"
            generator.generate_json(output_path)
            data = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(data.get("version"), __version__)
        self.assertIn("facts", data)
        self.assertGreater(len(data["facts"]), 0)


if __name__ == "__main__":
    unittest.main()
