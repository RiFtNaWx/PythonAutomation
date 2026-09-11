"""Gate for the operator app zip: central DB folder must already exist.

Run: python -m ate.core.require_cloud_db
Exit 0 if the resolved #Test_Database directory is on this PC.
Exit 2 if missing (sync SharePoint / fill cloud_db.txt).
"""
from __future__ import annotations

import os
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
    app = str(os.environ.get("ATE_APP_ONLY") or "").strip()
    if app:
        print("MISSING_CLOUD_DB", file=sys.stderr)
        return 2
    print("WARN_CLOUD_DB_MISSING", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
