"""Copy golden author trees into goldens/ (original bytes) and write INDEX.md.

AST catalog only -- never execute vendor modules. Do not rewrite delay/timing.
Run: python -m ate.core.ingest_goldens
"""
from __future__ import annotations

import ast
import shutil
from pathlib import Path
from typing import Any

from ate.core.paths import REPO_ROOT
from ate.core.test_detect import SKIP_DIR_NAMES

GOLDENS_ROOT = REPO_ROOT / "goldens"
INDEX_PATH = GOLDENS_ROOT / "INDEX.md"

SKIP_DIR = SKIP_DIR_NAMES | frozenset({"Github_Auto", ".git"})
COPY_SUFFIX = frozenset({
    ".py", ".yaml", ".yml", ".txt", ".md", ".json", ".ini", ".cfg", ".csv",
})

# Named Downloads / author trees. Missing sources are skipped.
SOURCES: list[tuple[str, Path, str]] = [
    (
        "downloads/logic_tests.py",
        Path(r"C:/Users/OoiJianHong/Downloads/logic_tests.py"),
        "file",
    ),
    (
        "downloads/logic_test.py",
        Path(r"C:/Users/OoiJianHong/Downloads/logic_test.py"),
        "file",
    ),
    (
        "ariff",
        Path(
            r"C:/Users/OoiJianHong/Downloads/Ariff Repo/"
            r"LabAutomation test/LabAutomation_v1 - Copy"
        ),
        "dir",
    ),
    (
        "see_lin",
        Path(r"C:/Users/OoiJianHong/Downloads/See Lin Repo"),
        "dir",
    ),
    (
        "see_lin",
        Path(r"C:/Users/OoiJianHong/Downloads/See Lim Repo"),
        "dir",
    ),
    (
        "eugene",
        Path(r"C:/Users/OoiJianHong/Downloads/Eugene Repo/LabAutomation-1"),
        "dir",
    ),
]


def _resolve_src(src: Path, kind: str) -> Path:
    if src.exists():
        return src
    if kind != "dir":
        return src
    alt = src.parent
    if alt.is_dir() and any(alt.glob("*.py")):
        return alt
    return src


def _ignore(dirpath: str, names: list[str]) -> list[str]:
    skip: list[str] = []
    for name in names:
        if name in SKIP_DIR:
            skip.append(name)
            continue
        p = Path(dirpath) / name
        if p.is_file() and p.suffix.lower() not in COPY_SUFFIX:
            skip.append(name)
    return skip


def sources_need_copy() -> bool:
    """True when a named source .py is newer than the goldens/ copy."""
    for rel, src, kind in SOURCES:
        src = _resolve_src(src, kind)
        dest = GOLDENS_ROOT / rel
        if not src.exists():
            continue
        if not dest.exists():
            return True
        if kind == "file":
            if src.stat().st_mtime > dest.stat().st_mtime:
                return True
            continue
        for p in src.rglob("*.py"):
            if any(part in SKIP_DIR for part in p.parts):
                continue
            d = dest / p.relative_to(src)
            try:
                if not d.exists() or p.stat().st_mtime > d.stat().st_mtime:
                    return True
            except OSError:
                return True
    return False


def copy_sources() -> list[str]:
    """Byte-copy originals into goldens/. Does not rewrite Python."""
    GOLDENS_ROOT.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []
    for rel, src, kind in SOURCES:
        dest = GOLDENS_ROOT / rel
        src = _resolve_src(src, kind)
        if not src.exists():
            notes.append(f"skip missing {src}")
            continue
        if kind == "file":
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            notes.append(f"file {rel}")
            continue
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=_ignore)
        notes.append(f"dir {rel}")
    return notes


def _first_line(node: ast.AST) -> str:
    doc = ast.get_docstring(node) or ""
    line = doc.strip().splitlines()[0].strip() if doc.strip() else ""
    return line.replace("|", "/")[:120]


def catalog_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not GOLDENS_ROOT.is_dir():
        return rows
    for py in sorted(GOLDENS_ROOT.rglob("*.py")):
        if any(part in SKIP_DIR for part in py.parts):
            continue
        try:
            src = py.read_text(encoding="utf-8-sig", errors="replace")
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue
        rel = py.relative_to(GOLDENS_ROOT).as_posix()
        bucket = rel.split("/", 1)[0]
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            helper = node.name in ("test_parameter", "test_generator_procedures")
            rows.append(
                {
                    "bucket": bucket,
                    "fn": node.name,
                    "file": rel,
                    "lineno": int(node.lineno or 0),
                    "definition": _first_line(node),
                    "helper": helper,
                }
            )
    rows.sort(key=lambda r: (r["bucket"], r["file"], r["lineno"]))
    return rows


def write_index(rows: list[dict[str, Any]] | None = None) -> Path:
    rows = rows if rows is not None else catalog_rows()
    GOLDENS_ROOT.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Golden test catalog",
        "",
        "Original author trees. AST scan only -- never executed.",
        "Edit the original file. Keep delay/timing as written. Run that tree `main.py` without the ATE console.",
        "ATE console: Tests page Remember + enable (Path C). Do not paste these into `ate/tests/`.",
        "",
        f"Count: {len(rows)} `def test_*`.",
        "",
        "Jump: " + " | ".join(
            f"[{b}](#{b}-{sum(1 for x in rows if x['bucket'] == b)})"
            f" ({sum(1 for x in rows if x['bucket'] == b)})"
            for b in sorted({r["bucket"] for r in rows})
        ),
        "",
        "Guide: [TUTORIAL.md](TUTORIAL.md) -- add in `*tests.py` then `limits.py` then `main.py`.",
        "",
    ]
    current = ""
    for r in rows:
        if r["bucket"] != current:
            current = r["bucket"]
            n = sum(1 for x in rows if x["bucket"] == current)
            lines.extend(["", f"## {current} ({n})", "", "| fn | file:line | definition |", "|----|-----------|------------|"])
        mark = " *(config)*" if r["helper"] else ""
        defin = r["definition"] or "(no docstring -- add one on new tests)"
        lines.append(f"| `{r['fn']}`{mark} | `{r['file']}:{r['lineno']}` | {defin} |")
    lines.append("")
    INDEX_PATH.write_text("\n".join(lines), encoding="utf-8")
    return INDEX_PATH


def main() -> int:
    notes = copy_sources()
    path = write_index()
    rows = catalog_rows()
    print("copied:")
    for n in notes:
        print(f"  {n}")
    print(f"index {path} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
