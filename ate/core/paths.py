"""Shared paths and constants for the modular ATE.

Canonical campaign paths resolve through ate.core.database.DbContext so the
operator can select Component / Part / Package / Version. Module-level
constants remain as defaults for the current RS622 TTSOP8 Version_1 campaign.
"""
from __future__ import annotations

import os
from pathlib import Path

# Repo root (PythonAutomation/)
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"
PARTS_DIR = CONFIG_DIR / "parts"

_FALLBACK_DB_ROOT = Path.home() / "#Test_Database"
CLOUD_DB_FILE = CONFIG_DIR / "cloud_db.txt"
SHAREPOINT_URL_FILE = CONFIG_DIR / "sharepoint.url"


def first_data_line(path: Path) -> str:
    """First non-empty, non-# line. Used by cloud_db.txt and sharepoint.url."""
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            return s
    return ""


def expand_user_path(raw: str) -> Path:
    """%USERPROFILE%, ~, and relative-to-repo paths for try-packets."""
    s = os.path.expandvars(os.path.expanduser(str(raw or "").strip()))
    if not s:
        raise ValueError("empty path")
    p = Path(s)
    if not p.is_absolute():
        p = (REPO_ROOT / p).resolve()
    return p


def sharepoint_url() -> str:
    """https library link (browser). Not a filesystem path. A13 Graph stays parked."""
    env = str(os.environ.get("ATE_SHAREPOINT_URL") or "").strip()
    if env:
        return env
    raw = first_data_line(SHAREPOINT_URL_FILE)
    if raw:
        return raw
    cfg = CONFIG_DIR / "bench.yaml"
    try:
        import yaml

        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) if cfg.is_file() else {}
        if isinstance(data, dict):
            return str(data.get("sharepoint_url") or "").strip()
    except Exception:
        pass
    return ""


def load_test_db_root() -> Path:
    """Central #Test_Database. Env, then cloud_db.txt, then bench.yaml.

    App zip (ATE_APP_ONLY=1) must use the OneDrive-synced SharePoint folder,
    not a private copy inside the unzip. https:// links are not folders --
    sync the library, then put that local path in cloud_db.txt.
    """
    env = str(os.environ.get("ATE_TEST_DATABASE_ROOT") or "").strip()
    if env:
        return expand_user_path(env)
    cloud = first_data_line(CLOUD_DB_FILE)
    if cloud:
        return expand_user_path(cloud)
    cfg = CONFIG_DIR / "bench.yaml"
    try:
        import yaml

        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) if cfg.is_file() else {}
        if not isinstance(data, dict):
            data = {}
        raw = str(data.get("test_database_root") or "").strip()
        if raw:
            return expand_user_path(raw)
        td = str(data.get("test_database") or "").strip()
        if td:
            p = expand_user_path(td)
            parts = p.parts
            idx = next(i for i, x in enumerate(parts) if x in ("#Test_Database", "Test_Database"))
            return Path(*parts[: idx + 1])
    except Exception:
        pass
    return _FALLBACK_DB_ROOT


def cloud_kind(root: Path | None = None) -> str:
    """local | onedrive | sharepoint -- path name only; A13 Graph/MCP stays parked."""
    s = str(root or TEST_DB_ROOT).replace("/", "\\").lower()
    if "sharepoint" in s:
        return "sharepoint"
    if "onedrive" in s:
        return "onedrive"
    return "local"


# Canonical characterization database root (SharePoint = sync this folder, not a second writer)
TEST_DB_ROOT = load_test_db_root()

# Default campaign (overridden at runtime by DbContext)
PART_DB_ROOT = TEST_DB_ROOT / "OpAmp" / "RS622" / "TTSOP8" / "Eugene" / "Version_1"
DB_WORKBOOK_DIR = PART_DB_ROOT / "workbook"
DB_MANIFEST_DIR = PART_DB_ROOT / "_manifest"
DB_SESSIONS_DIR = PART_DB_ROOT / "sessions"

# Primary lab report — editable copy inside Test Database workbook/
LAB_REPORT_PATH = DB_WORKBOOK_DIR / "RS622XK_Lab_Report_TTSOP.xlsx"

# Optional research workbook (legacy VOS Characterization)
RESEARCH_EXCEL_PATH = Path(r"C:\Users\OoiJianHong\Downloads\VOS Research.xlsx")

# Screenshots default into Test Database ORT folder; per-test helpers override
SCREENSHOT_DIR = PART_DB_ROOT / "ORT" / "screenshots"

# LabAutomation_14.7 reference tree (recipes / registry patterns)
LAB_AUTOMATION_REF = Path(r"C:\Users\OoiJianHong\LabAutomation_14.7")

JSONRPC_HOST = "127.0.0.1"
# 8765 is AirGPT — do not reuse
JSONRPC_PORT = 8766


def active_root() -> Path:
    """Return the operator-selected campaign root (or default PART_DB_ROOT)."""
    try:
        from ate.core.database import get_context

        return get_context().root()
    except Exception:
        return PART_DB_ROOT


def test_folder(test_key: str) -> Path:
    """Return <Version>/ <TestKey> folder (e.g. ORT, VOS)."""
    try:
        from ate.core.database import get_context

        return get_context().test_folder(test_key)
    except Exception:
        return PART_DB_ROOT / test_key


def dut_folder(test_key: str, dut_index: int) -> Path:
    """Return <Version>/<TestKey>/DUT_N."""
    try:
        from ate.core.database import get_context

        return get_context().dut_folder(test_key, dut_index)
    except Exception:
        return test_folder(test_key) / f"DUT_{int(dut_index)}"


def screenshot_dir(test_key: str, dut_index: int | None = None) -> Path:
    """Per-DUT screenshots folder, or shared <Test>/screenshots if dut is None."""
    try:
        from ate.core.database import get_context

        return get_context().screenshot_dir(test_key, dut_index)
    except Exception:
        if dut_index is None:
            return test_folder(test_key) / "screenshots"
        return dut_folder(test_key, dut_index) / "screenshots"


def graph_dir(test_key: str, dut_index: int | None = None) -> Path:
    try:
        from ate.core.database import get_context

        return get_context().graph_dir(test_key, dut_index)
    except Exception:
        if dut_index is None:
            return test_folder(test_key) / "graphs"
        return dut_folder(test_key, dut_index) / "graphs"


def artifact_name(
    test_key: str,
    dut_index: int,
    variant: str,
    *,
    timestamp: str,
    ext: str = "jpg",
) -> str:
    """Standard name: ORT_1_POS_CHA_2026-07-22_094100.jpg"""
    return f"{test_key}_{int(dut_index)}_{variant}_{timestamp}.{ext.lstrip('.')}"


def sync_defaults_from_context() -> None:
    """Refresh module-level aliases after set_context (for legacy imports)."""
    global PART_DB_ROOT, DB_WORKBOOK_DIR, DB_MANIFEST_DIR, DB_SESSIONS_DIR
    global LAB_REPORT_PATH, SCREENSHOT_DIR
    from ate.core.database import get_context

    ctx = get_context()
    PART_DB_ROOT = ctx.root()
    DB_WORKBOOK_DIR = ctx.workbook_dir()
    DB_MANIFEST_DIR = ctx.manifest_dir()
    DB_SESSIONS_DIR = ctx.sessions_dir()
    LAB_REPORT_PATH = ctx.lab_report_path()
    SCREENSHOT_DIR = ctx.screenshot_dir("ORT")
