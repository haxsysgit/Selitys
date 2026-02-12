#!/usr/bin/env python3
"""Bump the version across all components from the single source of truth (pyproject.toml).

Usage:
    python scripts/bump_version.py 2.5.0
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <new_version>")
        sys.exit(1)

    new_version = sys.argv[1]
    if not re.match(r"^\d+\.\d+\.\d+$", new_version):
        print(f"Error: '{new_version}' is not a valid semver (X.Y.Z)")
        sys.exit(1)

    # 1. pyproject.toml (source of truth)
    pyproject = ROOT / "pyproject.toml"
    text = pyproject.read_text()
    text = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_version}"', text, count=1)
    pyproject.write_text(text)
    print(f"  pyproject.toml  → {new_version}")

    # 2. frontend/package.json
    pkg_json = ROOT / "frontend" / "package.json"
    if pkg_json.exists():
        data = json.loads(pkg_json.read_text())
        data["version"] = new_version
        pkg_json.write_text(json.dumps(data, indent=2) + "\n")
        print(f"  package.json    → {new_version}")

    print(f"\nDone. All components set to v{new_version}")
    print("Backend + CLI read from pyproject.toml via importlib.metadata at runtime.")


if __name__ == "__main__":
    main()
