"""Compatibility entry point for selitys CLI."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from selitys.cli import app  # noqa: E402

if __name__ == "__main__":
    app()
