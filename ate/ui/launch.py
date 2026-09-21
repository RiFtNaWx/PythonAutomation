"""Silent ATE start: hidden worker + UI, supervisor stays up.

Run: pythonw -m ate.ui.launch
     python -m ate.ui.launch
     python -m ate.ui.launch --worker-only   (restart_ate_worker.bat)
"""
from __future__ import annotations

import atexit
import ctypes
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORKER_PORT = 8766
UI_PORT = 5174
WORKER_LOG = REPO / "ate" / "worker" / "last_worker.log"
SUPER_PID = REPO / "ate" / "worker" / "supervisor.pid"
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
HIGH_PRIORITY_CLASS = 0x00000080
WATCH_S = 4.0


def listening(port: int) -> bool:
    s = socket.socket()
    s.settimeout(0.35)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _rpc(method: str, timeout: float = 1.5) -> dict:
    req = urllib.request.Request(
        f"http://127.0.0.1:{WORKER_PORT}",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": {}}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8") or "{}")
    return body.get("result") or {}


def worker_ping() -> bool:
    try:
        got = _rpc("ping")
        return bool(got.get("ok"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return False


def worker_busy() -> bool:
    try:
        return bool(_rpc("session_status", timeout=2.0).get("busy"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return False


def python_exe() -> str:
    py = REPO / "venv" / "Scripts" / "python.exe"
    if py.is_file():
        return str(py)
    pyw = REPO / "venv" / "Scripts" / "pythonw.exe"
    if pyw.is_file():
        return str(pyw)
    return sys.executable


def spawn(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    log: Path | None = None,
) -> None:
    kw: dict = {
        "cwd": str(REPO),
        "close_fds": True,
    }
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        fh = open(log, "w", encoding="utf-8", errors="replace")
        kw["stdout"] = fh
        kw["stderr"] = fh
    else:
        kw["stdout"] = subprocess.DEVNULL
        kw["stderr"] = subprocess.DEVNULL
    if env is not None:
        kw["env"] = env
    flags = 0
    if CREATE_NO_WINDOW:
        flags |= CREATE_NO_WINDOW
    if sys.platform == "win32":
        flags |= HIGH_PRIORITY_CLASS
    if flags:
        kw["creationflags"] = flags
    subprocess.Popen(args, **kw)


def set_high_priority() -> None:
    if sys.platform != "win32":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), HIGH_PRIORITY_CLASS)
    except Exception:
        pass


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
    kernel32.CloseHandle(handle)
    return int(code.value) == STILL_ACTIVE


def pid_on_port(port: int) -> int:
    try:
        flags = CREATE_NO_WINDOW if CREATE_NO_WINDOW else 0
        out = subprocess.check_output(
            ["netstat", "-ano"],
            creationflags=flags,
            text=True,
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return 0
    needle = f":{port}"
    for line in out.splitlines():
        if needle not in line or "LISTENING" not in line.upper():
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            return int(parts[-1])
        except ValueError:
            continue
    return 0


def kill_port(port: int) -> None:
    pid = pid_on_port(port)
    if pid <= 0 or pid == os.getpid():
        return
    flags = CREATE_NO_WINDOW if CREATE_NO_WINDOW else 0
    subprocess.run(
        ["taskkill", "/F", "/PID", str(pid)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
        check=False,
    )


def wait_port(port: int, tries: int = 40) -> bool:
    for _ in range(tries):
        if listening(port):
            return True
        time.sleep(0.25)
    return False


def wait_rpc(tries: int = 80) -> bool:
    for _ in range(tries):
        if worker_ping():
            return True
        time.sleep(0.25)
    return False


def start_worker() -> None:
    if worker_ping():
        return
    if listening(WORKER_PORT):
        time.sleep(0.8)
        if worker_ping():
            return
        kill_port(WORKER_PORT)
        time.sleep(0.4)
    env = os.environ.copy()
    spawn([python_exe(), "-m", "ate.worker.server"], env=env, log=WORKER_LOG)


def start_ui() -> None:
    if listening(UI_PORT):
        return
    env = os.environ.copy()
    env["ATE_OPEN_BROWSER"] = "0"
    spawn([python_exe(), str(REPO / "ate" / "ui" / "dev_server.py")], env=env)


def restart_worker_idle() -> str:
    if worker_busy():
        return "busy"
    kill_port(WORKER_PORT)
    time.sleep(0.4)
    start_worker()
    wait_rpc(40)
    return "ok" if worker_ping() else "down"


def open_console() -> None:
    if not listening(UI_PORT):
        start_ui()
        wait_port(UI_PORT, 40)
    webbrowser.open(f"http://127.0.0.1:{UI_PORT}")


def existing_supervisor() -> bool:
    if not SUPER_PID.is_file():
        return False
    try:
        pid = int(SUPER_PID.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    if pid == os.getpid():
        return False
    return pid_alive(pid)


def _write_pid() -> None:
    SUPER_PID.parent.mkdir(parents=True, exist_ok=True)
    SUPER_PID.write_text(str(os.getpid()), encoding="utf-8")


def _clear_pid() -> None:
    try:
        if SUPER_PID.is_file() and SUPER_PID.read_text(encoding="utf-8").strip() == str(os.getpid()):
            SUPER_PID.unlink()
    except OSError:
        pass


def watch_forever(stop: threading.Event) -> None:
    while not stop.wait(WATCH_S):
        if not worker_ping():
            start_worker()
        if not listening(UI_PORT):
            start_ui()


def main() -> int:
    worker_only = "--worker-only" in sys.argv
    start_worker()
    if worker_only:
        wait_rpc(80)
        return 0 if worker_ping() else 1

    if existing_supervisor():
        had_ui = listening(UI_PORT)
        start_ui()
        wait_rpc(40)
        wait_port(UI_PORT, 40)
        if not had_ui:
            webbrowser.open(f"http://127.0.0.1:{UI_PORT}")
        return 0

    set_high_priority()
    atexit.register(_clear_pid)
    _write_pid()
    had_ui = listening(UI_PORT)
    start_ui()
    wait_rpc(80)
    wait_port(UI_PORT, 40)
    if not had_ui:
        webbrowser.open(f"http://127.0.0.1:{UI_PORT}")

    stop = threading.Event()
    watcher = threading.Thread(target=watch_forever, args=(stop,), name="ate-watch", daemon=True)
    watcher.start()
    tray_ok = False
    if sys.platform == "win32":
        try:
            from ate.ui.tray import run_tray

            tray_ok = bool(
                run_tray(
                    on_open=open_console,
                    on_restart=restart_worker_idle,
                    stop=stop,
                )
            )
        except Exception:
            tray_ok = False
    if not tray_ok:
        try:
            while not stop.wait(WATCH_S):
                pass
        except KeyboardInterrupt:
            stop.set()
    _clear_pid()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
