"""Fail-closed: in-repo goldens/ originals + INDEX.

Run: python -m ate.core.check_ingest_goldens
"""
from __future__ import annotations

import sys
from pathlib import Path

from ate.core.paths import REPO_ROOT
from ate.core import ingest_goldens as ig
from ate.core.test_detect import load_golden_roots

GOLDENS = REPO_ROOT / "goldens"


def check_ingest_goldens() -> list[str]:
    errors: list[str] = []
    need = [
        GOLDENS / "downloads" / "logic_tests.py",
        GOLDENS / "GUIDE.md",
        GOLDENS / "TUTORIAL.md",
        GOLDENS / "INDEX.md",
    ]
    for p in need:
        if not p.is_file():
            errors.append(f"missing {p.relative_to(REPO_ROOT)}")
    ariff_main = GOLDENS / "ariff" / "main.py"
    see_lin = GOLDENS / "see_lin" / "RS1G126" / "main.py"
    eugene_any = list((GOLDENS / "eugene").rglob("main.py")) if (GOLDENS / "eugene").is_dir() else []
    if not ariff_main.is_file() and not see_lin.is_file() and not eugene_any:
        errors.append("goldens/ has no author main.py -- run python -m ate.core.ingest_goldens")
    venvs = [p for p in GOLDENS.rglob("*") if p.is_dir() and p.name in ("venv", ".venv")]
    if venvs:
        errors.append(f"do not copy venv into goldens/: {venvs[0]}")
    rows = ig.catalog_rows()
    if GOLDENS.joinpath("downloads", "logic_tests.py").is_file() and not rows:
        errors.append("INDEX/catalog empty but goldens py exist")
    fns = {r["fn"] for r in rows}
    if rows and "test_parameter" not in fns and "test_tp" not in fns and "test_ioff" not in fns:
        errors.append("catalog missing expected golden test_* names")
    roots = load_golden_roots()
    labels = " ".join(str(r.get("path") or "") for r in roots).replace("\\", "/")
    if "goldens/" not in labels.replace("\\", "/") and "goldens\\" not in str(roots):
        joined = " ".join(str(r.get("path") or "") for r in roots)
        if "goldens" not in joined.replace("\\", "/"):
            errors.append("golden_roots.yaml must point at in-repo goldens/")
    return errors


def main() -> int:
    errors = check_ingest_goldens()
    if errors:
        print("FAIL check_ingest_goldens:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_ingest_goldens: originals in goldens/ + INDEX + golden_roots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
