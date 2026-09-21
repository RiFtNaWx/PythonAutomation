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
TEST_DB_MARKERS = ("#Test_Database", "Test_Database")
# Later AI / zip pack: never write C:\Users\<name> into coverage.json or datasheets.yaml.
PATH_RULE = (
    "Prefix may be any OneDrive/SharePoint sync folder. Slice at #Test_Database. "
    "Live Excel: #Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/workbook/. "
    "Golden lab xlsx: reports_root (%USERPROFILE%/Downloads/Product Testing Report) else "
    "#Test_Database/_ate/goldens. Store inventory report: as a relative key (RS622/foo.xlsx). "
    "PDFs: %USERPROFILE%/Downloads/Reference/Reference else #Test_Database/Reference; index file name only. "
    "Specs SoT: ate/config/limits/<key>.yaml. Truth table SoT: ate/config/parts/<key>.yaml truth_table. "
    "Extract blob: ate/config/datasheets/text/<key>.txt. Export index: ate/config/datasheets/tables/<key>.json. "
    "Do not dump PDFs into #Test_Database. Do not guess A91. Do not store C:\\Users\\<name> in zip config."
)


_LIST_PREFIX = "\u2022\u2023\u25e6\u2043\u00b7-* \t"


def first_data_line(path: Path) -> str:
    """First non-empty, non-# line. Used by cloud_db.txt and sharepoint.url."""
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        s = line.strip().lstrip(_LIST_PREFIX).strip()
        if s and not s.startswith("#"):
            return s
    return ""


# Shortcut layout depends on when the person clicked Add shortcut.
# All of these are the same SharePoint folder:
#   ...\OneDrive - JumpWin Tech\#Test_Database
#   ...\Research & Development - #Test_Database
#   ...\Research & Development-AE FAE - Core AE\#Test_Database
#   ...\Research & Development-AE FAE - AE FAE\Core AE\#Test_Database
_KNOWN_DB_REL = (
    Path("#Test_Database"),
    Path("Test_Database"),
    Path("Research & Development - #Test_Database"),
    Path("Research & Development-AE FAE - Core AE") / "#Test_Database",
    Path("Research & Development-AE FAE - AE FAE") / "Core AE" / "#Test_Database",
    Path("Documents") / "#Test_Database",
)

_FAMILY_DIR_NAMES = frozenset({"opamp", "logic", "analogswitch", "level", "power", "_ate"})


def onedrive_home_dirs() -> list[Path]:
    """This PC's OneDrive roots (commercial first). Empty if OneDrive is not signed in."""
    out: list[Path] = []
    for key in ("OneDriveCommercial", "OneDrive", "OneDriveConsumer"):
        raw = str(os.environ.get(key) or "").strip()
        if not raw:
            continue
        p = Path(raw)
        if p.is_dir() and p not in out:
            out.append(p)
    home = Path.home()
    for extra in (
        home / "OneDrive - JumpWin Tech",
        home / "JumpWin Tech",
        home / "OneDrive",
    ):
        if extra.is_dir() and extra not in out:
            out.append(extra)
    return out


def _child_names(path: Path) -> set[str]:
    try:
        return {x.name.lower() for x in path.iterdir()}
    except OSError:
        return set()


def _is_campaign_db(path: Path) -> bool:
    """True if this folder is (or will be) the shared #Test_Database."""
    if not path.is_dir():
        return False
    base = path.name.lower()
    if base in {"#test_database", "test_database"} or "#test_database" in base:
        return True
    return bool(_FAMILY_DIR_NAMES & _child_names(path))


def _score_db(path: Path) -> tuple:
    """Prefer OneDrive campaign trees over a dead home copy."""
    s = str(path).replace("/", "\\").lower()
    onedrive = 2 if ("onedrive" in s or "jumpwin" in s) else 0
    families = 1 if (_FAMILY_DIR_NAMES & _child_names(path)) else 0
    exact = 1 if path.name.lower() in {"#test_database", "test_database"} else 0
    home_dead = 0 if path.resolve() == (Path.home() / "#Test_Database").resolve() else 1
    n = len(_child_names(path))
    return (onedrive, home_dead, families, exact, n)


def descend_to_campaign(path: Path, *, max_depth: int = 3) -> Path:
    """If the operator picked a parent (Core AE), land on #Test_Database inside it."""
    p = Path(path)
    if _is_campaign_db(p):
        return p
    cur = p
    for _ in range(max_depth):
        hit = None
        for name in ("#Test_Database", "Test_Database"):
            inner = cur / name
            if inner.is_dir():
                hit = inner
                break
        if hit is None:
            try:
                kids = [x for x in cur.iterdir() if x.is_dir() and "#test_database" in x.name.lower()]
            except OSError:
                kids = []
            hit = kids[0] if kids else None
        if hit is None:
            break
        cur = hit
        if _is_campaign_db(cur):
            return cur
    return p


def list_onedrive_test_dbs(*, max_depth: int = 6) -> list[Path]:
    """Every OneDrive #Test_Database shortcut on this PC (any Add-shortcut date)."""
    names = {"#test_database", "test_database"}
    skip = {
        ".git",
        "node_modules",
        "pictures",
        "attachments",
        "desktop",
        "microsoft teams chat files",
        "others",
        "appdata",
    }
    found: list[Path] = []
    seen: set[str] = set()

    def _add(cand: Path) -> None:
        if not _is_campaign_db(cand):
            return
        key = str(cand.resolve()).lower()
        if key in seen:
            return
        seen.add(key)
        found.append(cand)

    for root in onedrive_home_dirs():
        for rel in _KNOWN_DB_REL:
            _add(root / rel)
        for dirpath, dirs, _files in os.walk(root):
            rel = Path(dirpath).relative_to(root)
            depth = 0 if rel.as_posix() == "." else len(rel.parts)
            if depth >= max_depth:
                dirs.clear()
                continue
            dirs[:] = [d for d in dirs if d.lower() not in skip]
            base = os.path.basename(dirpath).lower()
            if base in names or "#test_database" in base:
                _add(Path(dirpath))
    found.sort(key=_score_db, reverse=True)
    return found


def discover_onedrive_test_db(*, max_depth: int = 6) -> Path | None:
    """Best OneDrive-synced #Test_Database. Does not invent a private copy."""
    hits = list_onedrive_test_dbs(max_depth=max_depth)
    return hits[0] if hits else None


def write_cloud_db_txt(root: Path) -> None:
    CLOUD_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLOUD_DB_FILE.write_text(str(root) + "\n", encoding="utf-8")


def apply_test_db_root(root: Path) -> Path:
    """Write cloud_db.txt and retarget the live worker (no restart)."""
    global TEST_DB_ROOT
    resolved = Path(root)
    if not resolved.is_absolute():
        resolved = (REPO_ROOT / resolved).resolve()
    else:
        resolved = resolved.resolve()
    resolved = slice_test_db_root(descend_to_campaign(resolved))
    write_cloud_db_txt(resolved)
    TEST_DB_ROOT = resolved
    try:
        import ate.core.database as dbmod

        dbmod.TEST_DB_ROOT = resolved
    except Exception:
        pass
    return resolved


def pick_test_db_folder(*, title: str = "Select #Test_Database folder") -> Path | None:
    """Windows folder picker. Cancel returns None. Does not mkdir."""
    import tkinter as tk
    from tkinter import filedialog

    win = tk.Tk()
    win.withdraw()
    try:
        win.attributes("-topmost", True)
    except Exception:
        pass
    raw = filedialog.askdirectory(title=title, mustexist=True)
    try:
        win.destroy()
    except Exception:
        pass
    if not raw:
        return None
    return descend_to_campaign(Path(raw))


def cloud_db_status() -> dict:
    root = load_test_db_root()
    exists = root.is_dir()
    cands = list_onedrive_test_dbs()
    return {
        "root": str(root),
        "exists": exists,
        "cloud_kind": cloud_kind(root),
        "sharepoint_url": sharepoint_url(),
        "candidates": [str(p) for p in cands],
        "pick_needed": not exists,
    }


def expand_user_path(raw: str) -> Path:
    """%USERPROFILE%, ~, and relative-to-repo paths for try-packets."""
    s = os.path.expandvars(os.path.expanduser(str(raw or "").strip()))
    if not s:
        raise ValueError("empty path")
    p = Path(s)
    if not p.is_absolute():
        p = (REPO_ROOT / p).resolve()
    return p


def test_db_marker_index(parts: tuple[str, ...] | list[str]) -> int:
    names = {n.lower() for n in TEST_DB_MARKERS}
    for i, part in enumerate(parts):
        if str(part).lower() in names:
            return i
    return -1


def slice_test_db_root(path: Path) -> Path:
    """Any deeper campaign path -> the #Test_Database folder itself."""
    parts = Path(path).parts
    i = test_db_marker_index(parts)
    if i >= 0:
        return Path(*parts[: i + 1])
    return Path(path)


def rebase_under_test_db(raw: str | Path, *, db_root: Path) -> Path | None:
    """Map C:\\...\\#Test_Database\\Logic\\... onto this PC's db_root."""
    s = os.path.expandvars(os.path.expanduser(str(raw or "").strip()))
    if not s:
        return None
    parts = Path(s).parts
    i = test_db_marker_index(parts)
    if i < 0:
        return None
    tail = parts[i + 1 :]
    root = Path(db_root)
    return root.joinpath(*tail) if tail else root


def store_portable(path: Path | str) -> str:
    """Zip-safe path: #Test_Database/... or %USERPROFILE%/... or a filename."""
    s = str(path or "").strip()
    if not s:
        return ""
    p = Path(os.path.expandvars(os.path.expanduser(s)))
    i = test_db_marker_index(p.parts)
    if i >= 0:
        tail = p.parts[i + 1 :]
        return "/".join(("#Test_Database",) + tuple(str(x) for x in tail))
    try:
        rel = p.resolve().relative_to(Path.home().resolve())
        return "%USERPROFILE%/" + rel.as_posix()
    except Exception:
        return p.name


def store_config_path(path: Path | str) -> str:
    """Repo-relative if inside this clone/zip, else store_portable."""
    s = str(path or "").strip()
    if not s:
        return ""
    p = Path(os.path.expandvars(os.path.expanduser(s)))
    try:
        return p.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return store_portable(p)


def store_rel(path: Path | str, root: Path | str) -> str:
    """Relative posix under root, else store_portable."""
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except Exception:
        return store_portable(path)


def resolve_portable(raw: str | Path, *roots: Path, db_root: Path | None = None) -> Path | None:
    """Open a stored key on this PC. roots = reports_root, goldens, Reference."""
    s = str(raw or "").strip()
    if not s:
        return None
    norm = s.replace("\\", "/")
    root = Path(db_root) if db_root is not None else None
    if norm.lower().startswith("#test_database") or norm.lower().startswith("test_database"):
        if root is None:
            root = load_test_db_root()
        bits = norm.split("/", 1)
        tail = bits[1] if len(bits) > 1 else ""
        cand = (root / tail) if tail else root
        if cand.exists():
            return cand
    try:
        p = expand_user_path(s)
    except ValueError:
        p = None
    if p is not None and p.exists():
        return p
    if p is not None:
        if root is None:
            try:
                root = load_test_db_root()
            except Exception:
                root = None
        if root is not None:
            hit = rebase_under_test_db(p, db_root=root)
            if hit is not None and hit.exists():
                return hit
    name = Path(s).name
    rel = norm.lstrip("./")
    for base in roots:
        if not base:
            continue
        r = Path(base)
        for cand in (r / rel, r / name):
            if cand.exists():
                return cand
    return None


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


def _existing_dir(raw: str) -> Path | None:
    if not str(raw or "").strip():
        return None
    try:
        p = slice_test_db_root(expand_user_path(raw))
    except ValueError:
        return None
    return p if p.is_dir() else None


def load_test_db_root() -> Path:
    """Central #Test_Database. Existing folders win; missing paths do not block.

    Order: env (if the folder exists) -> cloud_db.txt (if exists) -> OneDrive
    discover (any shortcut layout) -> bench.yaml (if exists) -> last remembered
    path even if missing. Never mkdir a private unzip copy.
    """
    env = str(os.environ.get("ATE_TEST_DATABASE_ROOT") or "").strip()
    hit = _existing_dir(env)
    if hit is not None:
        return hit

    cloud = first_data_line(CLOUD_DB_FILE)
    cloud_path = None
    if cloud:
        try:
            cloud_path = expand_user_path(cloud)
        except ValueError:
            cloud_path = None
    if cloud_path is not None:
        cloud_path = slice_test_db_root(cloud_path)
    if cloud_path is not None and cloud_path.is_dir():
        found = discover_onedrive_test_db()
        home_dead = (Path.home() / "#Test_Database").resolve()
        # Prefer a live OneDrive shortcut over the retired home drag-copy only.
        # An explicit Setup -> Choose folder pick (even local) stays.
        if (
            found is not None
            and cloud_path.resolve() == home_dead
            and cloud_kind(found) == "onedrive"
        ):
            return found
        return cloud_path

    found = discover_onedrive_test_db()
    if found is not None:
        return found

    cfg = CONFIG_DIR / "bench.yaml"
    try:
        import yaml

        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) if cfg.is_file() else {}
        if not isinstance(data, dict):
            data = {}
        raw = str(data.get("test_database_root") or "").strip()
        hit = _existing_dir(raw)
        if hit is not None:
            return hit
        td = str(data.get("test_database") or "").strip()
        if td:
            p = expand_user_path(td)
            parts = p.parts
            idx = next(i for i, x in enumerate(parts) if x in ("#Test_Database", "Test_Database"))
            bench = Path(*parts[: idx + 1])
            if bench.is_dir():
                return bench
    except Exception:
        pass
    if cloud_path is not None:
        return cloud_path
    return _FALLBACK_DB_ROOT


def cloud_kind(root: Path | None = None) -> str:
    """local | onedrive | sharepoint -- path name only; A13 Graph/MCP stays parked."""
    s = str(root or TEST_DB_ROOT).replace("/", "\\").lower()
    if "sharepoint" in s:
        return "sharepoint"
    if "onedrive" in s or "jumpwin tech" in s:
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
