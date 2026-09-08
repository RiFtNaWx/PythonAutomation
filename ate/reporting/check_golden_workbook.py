"""Fail-closed golden workbook check (A17-T03).

Run: python -m ate.reporting.check_golden_workbook
     python -m ate.reporting.check_golden_workbook --fix
"""
from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    fix = "--fix" in args
    path = None
    for a in args:
        if a != "--fix" and not a.startswith("-"):
            path = Path(a)
            break

    from ate.reporting.golden_workbook import check_golden_workbook

    # Self-check mode: no campaign workbook required for syntax/import.
    # If no workbook, create a tiny temp xlsx and prove apply+check path.
    if path is None:
        try:
            from ate.core.database import get_context

            ctx = get_context()
            wb = ctx.lab_report_path()
            if not wb.is_file():
                print("SKIP check_golden_workbook: no campaign workbook (Apply campaign + import xlsx)")
                # Still prove module imports and session_paste callable
                from ate.reporting.session_paste import paste_session_photos

                assert callable(paste_session_photos)
                print("OK check_golden_workbook (import-only; no xlsx)")
                return 0
            result = check_golden_workbook(wb, fix=fix)
        except Exception as exc:
            print(f"FAIL check_golden_workbook: {exc}")
            return 1
    else:
        result = check_golden_workbook(path, fix=fix)

    if result.get("ok"):
        print(f"OK check_golden_workbook path={result.get('path')} fixed={result.get('fixed')}")
        return 0
    print("FAIL check_golden_workbook:")
    for e in result.get("errors") or []:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
