"""Print the resolved #Test_Database path. Never blocks the console.

Run: python -m ate.core.require_cloud_db
Exit 0 always. Missing folder -> WARN on stderr. START.bat still launches.
Operator then clicks Setup Choose folder (or Add shortcut to OneDrive).
"""
from __future__ import annotations

import sys

from ate.core.paths import load_test_db_root, sharepoint_url


def main() -> int:
    root = load_test_db_root()
    url = sharepoint_url()
    print(root)
    if url:
        print(url)
    if root.is_dir():
        return 0
    print("WARN_CLOUD_DB_MISSING", file=sys.stderr)
    print("Console still opens. Setup -> Choose folder to pick #Test_Database.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
