"""Fail-closed: golden safety gateway does not rewrite bodies; mixed blast blocked.

Run: python -m ate.core.check_golden_gateway
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from ate.core.paths import REPO_ROOT
from ate.core import golden_gateway as gw


def check_golden_gateway() -> list[str]:
    errors: list[str] = []
    tutorial = REPO_ROOT / "goldens" / "TUTORIAL.md"
    bat = REPO_ROOT / "UPDATE_GOLDENS.bat"
    helper = REPO_ROOT / "Github_Auto" / "git_helper.py"
    if not tutorial.is_file():
        errors.append("missing goldens/TUTORIAL.md")
    if not bat.is_file():
        errors.append("missing UPDATE_GOLDENS.bat")
    if not (REPO_ROOT / "ate" / "core" / "golden_gateway.py").is_file():
        errors.append("missing ate/core/golden_gateway.py")

    if not gw.mixed_forbidden(["goldens/ariff/main.py", "ate/core/runner.py"]):
        errors.append("mixed goldens + runner.py must be forbidden")
    if gw.mixed_forbidden(["goldens/ariff/main.py"]):
        errors.append("goldens-only must be allowed")
    if gw.mixed_forbidden(["ate/core/runner.py"]):
        errors.append("runner-only must be allowed (split from goldens)")
    if not gw.is_blast("ate/ui/web/app.js"):
        errors.append("ate/ui/web must count as blast")
    if gw.is_blast("goldens/ariff/main.py"):
        errors.append("goldens must not count as blast")

    tmp = Path(tempfile.mkdtemp(prefix="ate_gw_")) / "bad.py"
    tmp.write_text("def (\n", encoding="utf-8")
    syn = gw.syntax_issues([str(tmp)])
    if not syn or "syntax" not in syn[0]:
        errors.append("syntax_issues must report the broken file:line")
    try:
        tmp.unlink()
    except OSError:
        pass

    if "verify_push" not in helper.read_text(encoding="utf-8", errors="replace"):
        errors.append("Github_Auto/git_helper.py must call verify_push before commit")

    src = (REPO_ROOT / "ate" / "core" / "golden_gateway.py").read_text(encoding="utf-8")
    if "copy_sources" not in src or "ast.parse" not in src:
        errors.append("gateway must AST-parse and reuse ingest copy_sources")
    if "subprocess" in src and "git push" in src:
        errors.append("gateway must not git push itself -- use push.bat")
    return errors


def main() -> int:
    errors = check_golden_gateway()
    if errors:
        print("FAIL check_golden_gateway:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_golden_gateway: safety mix blocked, syntax named, tutorial+push hook")
    return 0


if __name__ == "__main__":
    sys.exit(main())
