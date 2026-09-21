"""Self-check: cloud DB resolve order (env, cloud_db.txt, bench). No SharePoint login.

Run: python -m ate.core.check_cloud_db
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def _mk_campaign(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "OpAmp").mkdir(exist_ok=True)
    (path / "Logic").mkdir(exist_ok=True)
    return path


def main() -> int:
    from ate.core import paths as pathmod
    from ate.core import require_cloud_db as reqmod

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
    bullets = tmp / "bullets.txt"
    sample_path = r"C:\Users\You\OneDrive\#Test_Database"
    bullets.write_text(f"\u2022 {sample_path}\n", encoding="utf-8")
    if pathmod.first_data_line(bullets) != sample_path:
        errors.append(f"first_data_line left notepad bullet: {pathmod.first_data_line(bullets)!r}")

    od = tmp / "OneDrive - JumpWin Tech"
    camp = _mk_campaign(od / "#Test_Database")
    nested_core = _mk_campaign(
        od / "Research & Development-AE FAE - Core AE" / "#Test_Database"
    )
    nested_fae = _mk_campaign(
        od / "Research & Development-AE FAE - AE FAE" / "Core AE" / "#Test_Database"
    )
    parent_only = od / "Research & Development-AE FAE - Core AE"
    old_homes = pathmod.onedrive_home_dirs
    pathmod.onedrive_home_dirs = lambda: [od]
    try:
        hits = {p.resolve() for p in pathmod.list_onedrive_test_dbs()}
        for want in (camp, nested_core, nested_fae):
            if want.resolve() not in hits:
                errors.append(f"list_onedrive_test_dbs missed {want}")
        got_od = pathmod.discover_onedrive_test_db()
        if got_od is None:
            errors.append("discover_onedrive_test_db returned None")
        landed = pathmod.descend_to_campaign(parent_only)
        if landed.resolve() != nested_core.resolve() and landed.resolve() != camp.resolve():
            if "#test_database" not in landed.name.lower():
                errors.append(f"descend_to_campaign expected #Test_Database, got {landed}")
    finally:
        pathmod.onedrive_home_dirs = old_homes

    missing_txt = tmp / "cloud_missing.txt"
    missing_txt.write_text(str(tmp / "does-not-exist" / "#Test_Database") + "\n", encoding="utf-8")
    od_only = tmp / "OneDrive-only"
    found_nested = _mk_campaign(
        od_only / "Research & Development-AE FAE - Core AE" / "#Test_Database"
    )
    old_file = pathmod.CLOUD_DB_FILE
    old_homes = pathmod.onedrive_home_dirs
    saved_env = os.environ.pop("ATE_TEST_DATABASE_ROOT", None)
    pathmod.CLOUD_DB_FILE = missing_txt
    pathmod.onedrive_home_dirs = lambda: [od_only]
    try:
        got = pathmod.load_test_db_root()
        if got.resolve() != found_nested.resolve():
            errors.append(f"missing cloud_db.txt path must fall through to discover, got {got}")
    finally:
        pathmod.CLOUD_DB_FILE = old_file
        pathmod.onedrive_home_dirs = old_homes
        if saved_env is not None:
            os.environ["ATE_TEST_DATABASE_ROOT"] = saved_env

    old_load = reqmod.load_test_db_root
    old_sp = reqmod.sharepoint_url
    reqmod.load_test_db_root = lambda: tmp / "no-such-db"
    reqmod.sharepoint_url = lambda: ""
    try:
        rc = reqmod.main()
        if rc != 0:
            errors.append(f"require_cloud_db must exit 0 when missing, got {rc}")
    finally:
        reqmod.load_test_db_root = old_load
        reqmod.sharepoint_url = old_sp

    start = (pathmod.REPO_ROOT / "START.bat").read_text(encoding="utf-8")
    if "need_cloud" in start.lower() or "exit /b 2" in start.lower():
        errors.append("START.bat must still launch when #Test_Database is missing")

    src = (pathmod.REPO_ROOT / "ate" / "worker" / "server.py").read_text(encoding="utf-8")
    if 'method == "pick_cloud_db"' not in src or 'method == "cloud_db_status"' not in src:
        errors.append("worker must expose pick_cloud_db and cloud_db_status")

    deep = Path(
        r"C:\Users\Someone\OneDrive - JumpWin Tech\Research & Development-AE FAE - Core AE\#Test_Database\Logic\RS1G08\SC70-5\Ariff\Version_1\workbook\x.xlsx"
    )
    stored = pathmod.store_portable(deep)
    if stored != "#Test_Database/Logic/RS1G08/SC70-5/Ariff/Version_1/workbook/x.xlsx":
        errors.append(f"store_portable want #Test_Database/... got {stored}")
    sliced = pathmod.slice_test_db_root(deep)
    if sliced.name not in ("#Test_Database", "Test_Database"):
        errors.append(f"slice_test_db_root want #Test_Database, got {sliced}")
    fake_db = tmp / "sync" / "#Test_Database"
    want = fake_db / "Logic" / "RS1G08" / "SC70-5" / "Ariff" / "Version_1" / "workbook" / "x.xlsx"
    want.parent.mkdir(parents=True)
    want.write_text("x", encoding="utf-8")
    hit = pathmod.resolve_portable(stored, db_root=fake_db)
    if hit is None or hit.resolve() != want.resolve():
        errors.append(f"resolve_portable rebase failed: {hit}")
    home_pdf = Path.home() / "Downloads" / "Reference" / "Reference" / "RS1G08_(RevA.7).pdf"
    home_stored = pathmod.store_portable(home_pdf)
    if not home_stored.startswith("%USERPROFILE%/"):
        errors.append(f"Downloads path must store as %USERPROFILE%, got {home_stored}")
    if "C:\\Users\\" in stored or "OoiJianHong" in stored:
        errors.append("portable store leaked a user home path")
    if "Do not store C:\\Users\\" not in pathmod.PATH_RULE:
        errors.append("PATH_RULE must forbid C:\\Users\\<name> in zip config")

    if errors:
        print("FAIL check_cloud_db:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_cloud_db: env wins, nested OneDrive shortcuts, missing path does not block")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
