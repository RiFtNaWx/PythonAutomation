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
    "node_modules",
}
SKIP_FILE_NAMES = {
    "cloud_db.txt",
    "env.local",
    "last_worker.log",
    "last_ingest.json",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".ps1", ".log"}

ROOT_FILES = [
    "00_START_HERE.txt",
    "START.bat",
    "requirements-console.txt",
    "run_ate_app.bat",
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
    "ate/ui/web/canvas/recipe-canvas.js",
    "ate/ui/dev_server.py",
    "ate/config/owners.yaml",
    "ate/config/inventory.yaml",
    "ate/config/cloud_db.example.txt",
    "ate/config/sharepoint.url",
    "00_START_HERE.txt",
    "START.bat",
    "run_ate_app.bat",
    "requirements-console.txt",
    "opa_tests.py",
    "logic_tests.py",
]

PACKET_BENCH = """# Operator app. Campaigns are the OneDrive shortcut of #Test_Database.
# START.bat writes cloud_db.txt. Do not keep a private unzip copy.
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

1. Unzip. You should see START.bat at the top (not buried).
2. Open ate\\config\\sharepoint.url -- Handover / Jianhong / #Test_Database.
3. Click Add shortcut to OneDrive. If asked Replace folder with your shortcut, click Replace.
4. Right-click the folder in Explorer -> Always keep on this device.
5. Double-click START.bat. First run installs packages (2 to 5 minutes).
   START writes the OneDrive path into ate\\config\\cloud_db.txt. Do not type https.
   If the folder is not on this PC yet, the console still opens. Setup -> Choose folder.
6. Browser: http://127.0.0.1:5174  Stale page: Ctrl+F5.
7. Pick a person (not All) -> Setup -> Apply campaign.
8. DEMO needs no instruments. START needs the Rigol bench.
9. DUT pin-1: Continue only if orientation is correct. Wrong = Abort, rotate, Continue.

#Test_Database may sit under any OneDrive prefix (Research & Development-AE FAE - Core AE, etc).
START writes the local path into cloud_db.txt. Lab xlsx live under
#Test_Database\\{Component}\\{Part}\\{Package}\\{Operator}\\{Version_N}\\workbook\\
Goldens also copy to #Test_Database\\_ate\\goldens. PDFs stay in
%USERPROFILE%\\Downloads\\Reference\\Reference (or #Test_Database\\Reference).
Do not keep C:\\Users\\<someone-else> paths. Do not dump PDFs into #Test_Database.

Do not click SharePoint Sync if you already have another RD shortcut.
Do not drag-copy #Test_Database. Do not keep a private database in this unzip.

Change the product: git clone -b eugene-console (read AGENTS.md). Double-click START.bat there too.
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
            arc = f"{prefix}/{name}"
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
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.name in SKIP_FILE_NAMES:
            continue
        if path.suffix.lower() == ".md":
            continue
        if path.name.startswith("check_") and path.suffix == ".py":
            continue
        rel = path.relative_to(REPO).as_posix()
        if rel == "ate/config/bench.yaml":
            continue
        out.append((path, f"{prefix}/{rel}"))
    tutorial = REPO / "docs" / "tutorial"
    if (tutorial / "ATE_TUTORIAL.html").is_file():
        out.append((tutorial / "ATE_TUTORIAL.html", f"{prefix}/docs/tutorial/ATE_TUTORIAL.html"))
        img = tutorial / "images"
        if img.is_dir():
            for path in img.iterdir():
                if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                    out.append((path, f"{prefix}/docs/tutorial/images/{path.name}"))
    ingest_md = REPO / "docs" / "datasheet" / "INGEST.md"
    if ingest_md.is_file():
        out.append((ingest_md, f"{prefix}/docs/datasheet/INGEST.md"))
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
    bat = (REPO / "START.bat").read_text(encoding="utf-8")
    if "pin-1" not in bat.lower():
        print("FAIL pack_ate_console: START must mention pin-1 orientation")
        return 1
    for rel in REQUIRED:
        want = f"ATE_Console_Try/{rel}"
        if want not in names:
            print(f"FAIL pack_ate_console: {rel} not packed")
            return 1
    print("OK pack check: required console files present")
    bat = (REPO / "START.bat").read_text(encoding="utf-8")
    if 'mkdir "#Test_Database"' in bat or "mkdir #Test_Database" in bat:
        print("FAIL pack_ate_console: START must not create a private #Test_Database")
        return 1
    if "ATE_APP_ONLY" not in bat:
        print("FAIL pack_ate_console: START must set ATE_APP_ONLY")
        return 1
    if "need_cloud" in bat.lower() or "exit /b 2" in bat.lower():
        print("FAIL pack_ate_console: START must still launch when #Test_Database is missing")
        return 1
    if "test_database_root: \"#Test_Database\"" in PACKET_BENCH:
        print("FAIL pack_ate_console: packet bench must not use unzip-local DB")
        return 1
    if "%USERPROFILE%/Downloads/Reference/Reference" not in PACKET_BENCH:
        print("FAIL pack_ate_console: packet bench must use %USERPROFILE% reference_root")
        return 1
    packed = names | {"ATE_Console_Try/TRY.txt"}
    banned = [n for n in packed if n.endswith(".ps1") or n.endswith("TRY_ATE.bat") or n.endswith("force_continue.bat") or n.endswith("cloud_db.txt") and "example" not in n]
    if banned:
        print("FAIL pack_ate_console: zip must not include")
        for n in banned:
            print(f"  - {n}")
        return 1
    leak_files = [
        REPO / "ate" / "config" / "inventory.yaml",
        REPO / "ate" / "config" / "golden_roots.yaml",
        REPO / "ate" / "config" / "datasheets.yaml",
        REPO / "ate" / "config" / "datasheets" / "coverage.json",
    ]
    for src in leak_files:
        if not src.is_file():
            continue
        blob = src.read_text(encoding="utf-8", errors="ignore")
        if "OoiJianHong" in blob or "C:\\\\Users\\\\OoiJianHong" in blob:
            print(f"FAIL pack_ate_console: {src.relative_to(REPO)} still has a Jianhong-absolute path")
            return 1
    if "ATE_Console_Try/ate/config/datasheets/last_ingest.json" in packed:
        print("FAIL pack_ate_console: last_ingest.json is a machine log, do not zip it")
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
