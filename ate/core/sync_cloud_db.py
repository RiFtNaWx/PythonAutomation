"""Write ate/config/cloud_db.txt from a OneDrive-synced #Test_Database.

Run: python -m ate.core.sync_cloud_db
Exit 0 if a folder was found (or the existing cloud_db.txt path still exists).
Exit 1 if none -- keep the existing cloud_db.txt. START.bat still launches.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ate.core.paths import (
    CLOUD_DB_FILE,
    apply_test_db_root,
    cloud_kind,
    discover_onedrive_test_db,
    first_data_line,
)


def sync_cloud_db_txt() -> Path | None:
    found = discover_onedrive_test_db()
    cur_raw = first_data_line(CLOUD_DB_FILE)
    cur = Path(cur_raw) if cur_raw else None
    cur_ok = bool(cur is not None and cur.is_dir())
    if found is None:
        return cur if cur_ok else None
    if cur_ok and cloud_kind(cur) == "onedrive" and cur.resolve() == found.resolve():
        return cur
    if cur_ok and cloud_kind(cur) == "onedrive":
        # Keep this PC's existing OneDrive shortcut; do not ping-pong layouts.
        return cur
    apply_test_db_root(found)
    return found


def main() -> int:
    found = sync_cloud_db_txt()
    if found is None:
        print("NO_ONEDRIVE_TEST_DB", file=sys.stderr)
        return 1
    print(found)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
