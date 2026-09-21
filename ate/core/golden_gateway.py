"""Safety gateway for golden import + verify. Does not rewrite author Python.

AST only -- never execute vendor modules. Does not edit ate/tests or runner.py.

  python -m ate.core.golden_gateway --import --verify
  python -m ate.core.golden_gateway --verify

Push stays Github_Auto / push.bat. This module blocks a mixed goldens+blast
push and prints cause+fix. It does not git commit by itself.
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ate.core.paths import REPO_ROOT
from ate.core import ingest_goldens as ig
from ate.core.check_ingest_goldens import check_ingest_goldens

BLAST_FILES = frozenset(
    {
        "ate/core/runner.py",
        "ate/core/database.py",
        "ate/core/registry.py",
        "ate/worker/server.py",
    }
)
BLAST_PREFIX = ("ate/ui/web/",)


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def is_blast(path: str) -> bool:
    n = _norm(path)
    return n in BLAST_FILES or n.startswith(BLAST_PREFIX)


def is_golden_tree(path: str) -> bool:
    n = _norm(path)
    return n == "goldens" or n.startswith("goldens/")


def mixed_forbidden(paths: list[str]) -> bool:
    """goldens/ + blast-radius in one push would mix two jobs."""
    gold = any(is_golden_tree(p) for p in paths)
    blast = any(is_blast(p) for p in paths)
    return gold and blast


def syntax_issues(paths: list[str]) -> list[str]:
    """Parse changed Python. One error per file. Does not execute."""
    errors: list[str] = []
    for raw in paths:
        n = _norm(raw)
        if not n.endswith(".py"):
            continue
        p = Path(raw)
        if not p.is_absolute():
            p = REPO_ROOT / n
        if not p.is_file():
            continue
        try:
            src = p.read_text(encoding="utf-8-sig", errors="replace")
            ast.parse(src)
        except SyntaxError as exc:
            line = exc.lineno or 0
            errors.append(
                f"syntax {n}:{line}: {exc.msg} -- fix that line only; "
                "do not edit sibling tests or runner.py"
            )
        except OSError as exc:
            errors.append(f"read {n}: {exc}")
    return errors


def debug_goldens(only: list[str] | None = None) -> list[str]:
    """Hints (not hard fail): missing docstring, test_* not named in nearby main.py."""
    hints: list[str] = []
    root = ig.GOLDENS_ROOT
    if not root.is_dir():
        return ["missing goldens/ -- run python -m ate.core.golden_gateway --import"]
    want: set[str] | None = None
    if only:
        want = set()
        for raw in only:
            n = _norm(raw)
            if n.startswith("goldens/"):
                want.add(n[len("goldens/") :])
            elif n != "goldens":
                want.add(n)
    for py in sorted(root.rglob("*.py")):
        if any(part in ig.SKIP_DIR for part in py.parts):
            continue
        rel = py.relative_to(root).as_posix()
        if want is not None and rel not in want:
            continue
        try:
            src = py.read_text(encoding="utf-8-sig", errors="replace")
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue
        names = [
            n.name
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name.startswith("test_")
            and n.name not in ("test_parameter", "test_generator_procedures")
        ]
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            if node.name in ("test_parameter", "test_generator_procedures"):
                continue
            if not (ast.get_docstring(node) or "").strip():
                hints.append(
                    f"{rel}:{node.lineno} `{node.name}` has no docstring -- "
                    "add one line; do not change delay/timing"
                )
        main_py = py.parent / "main.py"
        if names and main_py.is_file():
            try:
                main_src = main_py.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            missing = [n for n in names if n not in main_src]
            if missing:
                hints.append(
                    f"{rel}: {', '.join(missing)} not named in {py.parent.name}/main.py -- "
                    "add the id to that tree's menu; do not copy into ate/tests/"
                )
    return hints[:12]


@dataclass
class GateReport:
    ok: bool
    issues: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    imported: list[str] = field(default_factory=list)


def verify_push(changed_files: list[str]) -> GateReport:
    """Fail-closed for mixed blast+goldens and syntax. Goldens also run ingest check."""
    files = [p for p in changed_files if str(p).strip()]
    issues = syntax_issues(files)
    if mixed_forbidden(files):
        issues.append(
            "safety: goldens/ and blast-radius (runner/database/registry/worker/UI) "
            "in one push -- split into two commits"
        )
    if any(is_golden_tree(p) for p in files):
        issues.extend(check_ingest_goldens())
    gold_py = [p for p in files if is_golden_tree(p) and _norm(p).endswith(".py")]
    hints = debug_goldens(only=gold_py) if gold_py else []
    return GateReport(ok=not issues, issues=issues, hints=hints)


def run_import(*, force: bool = False) -> list[str]:
    """Byte-copy sources into goldens/ when newer (or force). Never rewrites bodies."""
    if not force and not ig.sources_need_copy():
        ig.write_index()
        return ["up to date -- skipped copy, refreshed INDEX.md"]
    notes = ig.copy_sources()
    ig.write_index()
    return notes


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    do_import = "--import" in args
    force = "--force" in args
    do_debug = "--debug" in args
    do_verify = "--verify" in args or "--debug" in args or not do_import
    notes: list[str] = []
    if do_import:
        notes = run_import(force=force)
        print("import:")
        for n in notes:
            print(f"  {n}")
    report = GateReport(ok=True, imported=notes)
    if do_verify:
        # Verify the in-repo goldens tree even when git is clean.
        files = ["goldens/INDEX.md"]
        if (ig.GOLDENS_ROOT / "downloads" / "logic_tests.py").is_file():
            files.append("goldens/downloads/logic_tests.py")
        report = verify_push(files)
        report.imported = notes
        if do_debug:
            extra = debug_goldens()
            seen = set(report.hints)
            report.hints = report.hints + [h for h in extra if h not in seen]
        if report.hints:
            print("debug hints:")
            for h in report.hints:
                print(f"  - {h}")
        if not report.ok:
            print("FAIL golden_gateway:")
            for e in report.issues:
                print(f"  - {e}")
            print("Fix the named file only. Then re-run. Do not edit runner.py.")
            return 1
        print("OK golden_gateway: syntax + ingest check; goldens not mixed with blast files")
        print("Next: double-click push.bat (gateway runs again before GitHub).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
