"""Fail-closed: silent launch + boot splash exist.

Run: python -m ate.core.check_launch
"""
from __future__ import annotations

from pathlib import Path

from ate.core.paths import REPO_ROOT

WEB = REPO_ROOT / "ate" / "ui" / "web"


def main() -> int:
    errors: list[str] = []
    launch = (REPO_ROOT / "ate" / "ui" / "launch.py").read_text(encoding="utf-8")
    if "pythonw" not in launch and "python.exe" not in launch:
        errors.append("launch.py must start hidden python")
    if "CREATE_NO_WINDOW" not in launch:
        errors.append("launch.py must hide console windows")
    if "webbrowser.open" not in launch:
        errors.append("launch.py must open the UI")
    if "last_worker.log" not in launch:
        errors.append("launch.py must keep last_worker.log (pythonw hides crashes)")
    if "wait_rpc" not in launch or "worker_ping" not in launch:
        errors.append("launch.py must wait for ping JSON-RPC, not only TCP")
    if "HIGH_PRIORITY_CLASS" not in launch:
        errors.append("launch.py must spawn worker HIGH_PRIORITY_CLASS")
    if "watch_forever" not in launch:
        errors.append("launch.py must keep a supervisor loop (watch_forever)")
    if "had_ui" not in launch:
        errors.append("launch.py must not open a second browser tab when UI is already up")
    tray = (REPO_ROOT / "ate" / "ui" / "tray.py").read_text(encoding="utf-8")
    if "Shell_NotifyIconW" not in tray:
        errors.append("tray.py must use Shell_NotifyIcon (hidden icon, no extra window)")
    if "NIF_INFO" in tray or "NIM_MODIFY" in tray:
        errors.append("tray must not show balloon popups")
    worker = (REPO_ROOT / "ate" / "worker" / "server.py").read_text(encoding="utf-8")
    dispatch = worker[worker.find("def dispatch(") : worker.find("\ndef main(")]
    ping_at = dispatch.find('if method == "ping"')
    core_at = dispatch.find("_core()")
    if ping_at < 0 or ping_at > (core_at if core_at >= 0 else 10**9):
        errors.append("worker ping must not wait for ATECore / load_family")
    if "Bind before ATECore" not in worker:
        errors.append("worker must bind :8766 before ATECore warmup")
    if "worker already listening" not in worker:
        errors.append("worker duplicate bind must exit 0 if ping already works")
    if "worker accept loop" not in worker:
        errors.append("worker serve_forever must recover from accept errors")
    bat = (REPO_ROOT / "run_ate_app.bat").read_text(encoding="utf-8")
    if "ate.ui.launch" not in bat:
        errors.append("run_ate_app.bat must call ate.ui.launch")
    if "start \"ATE Worker\"" in bat or "start \"ATE UI\"" in bat:
        errors.append("run_ate_app.bat must not show named backend windows")
    start = (REPO_ROOT / "START.bat").read_text(encoding="utf-8")
    if "pin-1" not in start.lower():
        errors.append("START.bat must mention pin-1 orientation")
    if "need_cloud" in start.lower() or "exit /b 2" in start.lower():
        errors.append("START.bat must still launch when #Test_Database is missing")
    if start.lower().split(":launch", 1)[-1].count("pause") > 0:
        after = start.split(":launch", 1)[-1]
        if "pause" in after.lower():
            errors.append("START.bat must not pause after launch")
    html = (WEB / "index.html").read_text(encoding="utf-8")
    if 'id="boot-splash"' not in html or 'id="boot-splash-msg"' not in html:
        errors.append("boot splash overlay missing")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    if "sync_repo" not in js or "hideBootSplash" not in js:
        errors.append("boot must call sync_repo then hide splash")
    if errors:
        print("FAIL check_launch:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_launch: silent start, watchdog, tray, no backend windows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
