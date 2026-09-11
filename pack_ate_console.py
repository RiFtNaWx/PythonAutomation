"""Build a downloadable try-packet of the operator console.

Run:  python pack_ate_console.py
Check: python pack_ate_console.py --check

Writes ATE_Console_Try.zip to Desktop (and dist/). Unzip, START.bat.
Operator app only: same SharePoint #Test_Database. Vibe-coders use git + AGENTS.md.
"""
from __future__ import annotations

import os
import sys
import zipfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent
SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    "venv",
    "kicad-source-mirror",
    "Github_Auto",
    "src-tauri",
    "dist",
    ".cursor",
}

ROOT_FILES = [
    "TRY_ATE.bat",
    "requirements-console.txt",
    "run_ate_app.bat",
    "restart_ate_app.bat",
    "restart_ate_worker.bat",
    "run_ate_worker.bat",
    "ate_runner.py",
    "configurations.py",
    "datalog.py",
    "dmm_setup.py",
    "generator_setup.py",
    "instruments.py",
    "limits.py",
    "logic_tests.py",
    "opa_tests.py",
    "psu_setup.py",
    "scope_setup.py",
    "utils.py",
]

REQUIRED = [
    "ate/worker/server.py",
    "ate/ui/web/index.html",
    "ate/ui/web/app.js",
    "ate/ui/dev_server.py",
    "ate/config/owners.yaml",
    "ate/config/inventory.yaml",
    "ate/config/cloud_db.example.txt",
    "ate/config/sharepoint.url",
    "TRY_ATE.bat",
    "run_ate_app.bat",
    "requirements-console.txt",
    "opa_tests.py",
    "logic_tests.py",
]

PACKET_BENCH = """# Operator app. Campaigns are the SharePoint-synced #Test_Database.
# Put the local OneDrive folder in cloud_db.txt (not a private unzip copy).
jsonrpc:
  host: "127.0.0.1"
  port: 8766

sharepoint_url: "SHAREPOINT_URL_HERE"
reference_root: "%USERPROFILE%/Downloads/Reference/Reference"

default_vcc: 5.0
current_limit_a: 0.10
default_part: rs622
sample_size: 4
year: "2026"
stm_bridge_enabled: false
"""

def _sharepoint_line() -> str:
    p = REPO / "ate" / "config" / "sharepoint.url"
    if not p.is_file():
        return ""
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            return s
    return ""


def packet_bench_text() -> str:
    url = _sharepoint_line()
    return PACKET_BENCH.replace("SHAREPOINT_URL_HERE", url)


TRY_TXT = """ATE operator app
================

This zip is for running tests. It is not the git repo.

Need: Windows + Python 3.11+ (tick Add python.exe to PATH).

1. Unzip this folder.
2. OneDrive: Add shortcut / sync the RD SharePoint library (link in ate\\config\\sharepoint.url).
3. Put that local folder path (the #Test_Database tree) in ate\\config\\cloud_db.txt -- one line, not https://
4. Double-click START.bat. First run installs packages (2 to 5 minutes).
5. Browser opens http://127.0.0.1:5174
6. Pick a person (not All) -> Setup -> Create folders + open.
7. DEMO needs no instruments. START needs the Rigol bench.
8. DUT pin-1: Continue only if orientation is correct. Wrong = Abort, rotate, Continue.

Sessions, Excel paste, and photos write into that same #Test_Database. OneDrive uploads. Do not keep a private database in this unzip.

Change the product (add a test / person): clone instead of this zip.

  git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git

Then read AGENTS.md. Cursor/VS Code folder-open and run_ate_app.bat auto-pull ff-only once a day; uncommitted files are never replaced.
"""


def required_missing() -> list[str]:
    return [rel for rel in REQUIRED if not (REPO / rel).is_file()]


def _skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.endswith(".egg-info")


def iter_packet_files() -> list[tuple[Path, str]]:
    """(src, zip_arcname under ATE_Console_Try/)."""
    prefix = "ATE_Console_Try"
    out: list[tuple[Path, str]] = []
    for name in ROOT_FILES:
        src = REPO / name
        if src.is_file():
            arc = f"{prefix}/START.bat" if name == "TRY_ATE.bat" else f"{prefix}/{name}"
            out.append((src, arc))
    ico = REPO / "assets" / "ate.ico"
    if ico.is_file():
        out.append((ico, f"{prefix}/assets/ate.ico"))
    ate = REPO / "ate"
    for path in ate.rglob("*"):
        if not path.is_file():
            continue
        if any(_skip_dir(p) for p in path.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        if path.name.startswith("check_") and path.suffix == ".py":
            continue
        rel = path.relative_to(REPO).as_posix()
        if rel == "ate/config/bench.yaml":
            continue
        out.append((path, f"{prefix}/{rel}"))
    return out


def desktop_dir() -> Path:
    return Path(os.environ.get("USERPROFILE") or str(Path.home())) / "Desktop"


def zip_paths() -> list[Path]:
    name = f"ATE_Console_Try_{date.today().isoformat()}.zip"
    dests = [desktop_dir() / name, REPO / "dist" / name]
    return dests


def build(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    files = iter_packet_files()
    if dest.is_file():
        dest.unlink()
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arc in files:
            zf.write(src, arc)
        zf.writestr("ATE_Console_Try/TRY.txt", TRY_TXT.replace("\n", "\r\n"))
        zf.writestr("ATE_Console_Try/ate/config/bench.yaml", packet_bench_text())
    return dest


def main() -> int:
    check_only = "--check" in sys.argv
    missing = required_missing()
    if missing:
        print("FAIL pack_ate_console:")
        for m in missing:
            print(f"  - missing {m}")
        return 1
    names = {arc.replace("\\", "/") for _, arc in iter_packet_files()}
    names.add("ATE_Console_Try/ate/config/bench.yaml")
    bench = packet_bench_text()
    if "jumptechwin.sharepoint.com" not in bench:
        print("FAIL pack_ate_console: packet bench missing SharePoint url")
        return 1
    if "SHAREPOINT_URL_HERE" in bench:
        print("FAIL pack_ate_console: packet bench url placeholder left in")
        return 1
    bat = (REPO / "TRY_ATE.bat").read_text(encoding="utf-8")
    if "pin-1" not in bat.lower():
        print("FAIL pack_ate_console: START must mention pin-1 orientation")
        return 1
    for rel in REQUIRED:
        want = "ATE_Console_Try/START.bat" if rel == "TRY_ATE.bat" else f"ATE_Console_Try/{rel}"
        if want not in names:
            print(f"FAIL pack_ate_console: {rel} not packed")
            return 1
    print("OK pack check: required console files present")
    bat = (REPO / "TRY_ATE.bat").read_text(encoding="utf-8")
    if 'mkdir "#Test_Database"' in bat or "mkdir #Test_Database" in bat:
        print("FAIL pack_ate_console: START must not create a private #Test_Database")
        return 1
    if "ATE_APP_ONLY" not in bat:
        print("FAIL pack_ate_console: START must set ATE_APP_ONLY")
        return 1
    if "test_database_root: \"#Test_Database\"" in PACKET_BENCH:
        print("FAIL pack_ate_console: packet bench must not use unzip-local DB")
        return 1
    if check_only:
        return 0
    written = []
    for dest in zip_paths():
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            build(dest)
            written.append(dest)
        except OSError as exc:
            print(f"skip {dest}: {exc}")
    if not written:
        print("FAIL pack_ate_console: no zip written")
        return 1
    size = written[0].stat().st_size
    print(f"OK packed {size} bytes")
    for p in written:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
