"""Self-check: cloud DB resolve order (env, cloud_db.txt, bench). No SharePoint login.

Run: python -m ate.core.check_cloud_db
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def main() -> int:
    from ate.core import paths as pathmod

    errors: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="ate_cloud_"))
    fake = tmp / "OneDrive" / "Lab" / "#Test_Database"
    fake.mkdir(parents=True)

    old_env = os.environ.get("ATE_TEST_DATABASE_ROOT")
    old_url = os.environ.get("ATE_SHAREPOINT_URL")
    os.environ["ATE_TEST_DATABASE_ROOT"] = str(fake)
    os.environ["ATE_SHAREPOINT_URL"] = "https://example.sharepoint.com/sites/lab/Shared%20Documents"
    try:
        got = pathmod.load_test_db_root()
        if got != fake.resolve() and got != fake:
            if got.resolve() != fake.resolve():
                errors.append(f"env root expected {fake}, got {got}")
        url = pathmod.sharepoint_url()
        if "example.sharepoint.com" not in url:
            errors.append(f"sharepoint_url env not used: {url!r}")
    finally:
        if old_env is None:
            os.environ.pop("ATE_TEST_DATABASE_ROOT", None)
        else:
            os.environ["ATE_TEST_DATABASE_ROOT"] = old_env
        if old_url is None:
            os.environ.pop("ATE_SHAREPOINT_URL", None)
        else:
            os.environ["ATE_SHAREPOINT_URL"] = old_url

    line = pathmod.first_data_line(tmp / "missing.txt")
    if line:
        errors.append("missing file should yield empty first_data_line")
    sample = tmp / "cloud_db.txt"
    sample.write_text("# comment\n\nC:\\\\synced\\\\#Test_Database\n", encoding="utf-8")
    got_line = pathmod.first_data_line(sample)
    if "Test_Database" not in got_line:
        errors.append(f"first_data_line skipped data: {got_line!r}")

    if errors:
        print("FAIL check_cloud_db:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_cloud_db: env wins, sharepoint url, first_data_line")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
