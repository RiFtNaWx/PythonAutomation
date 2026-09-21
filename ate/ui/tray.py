"""Hidden tray icon for the ATE supervisor. stdlib + ctypes, no pywin32.

No balloon popups. Menu: Open console / Restart worker.
"""
from __future__ import annotations

import ctypes
import sys
import threading
from ctypes import wintypes
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parents[2]
ICON_PATH = REPO / "assets" / "ate.ico"

WM_USER = 0x0400
WM_TRAY = WM_USER + 21
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_QUIT = 0x0012
NIM_ADD = 0
NIM_DELETE = 2
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
IDI_APPLICATION = 32512
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010
LR_DEFAULTSIZE = 0x0040
CW_USEDEFAULT = 0x80000000
HWND_MESSAGE = ctypes.c_void_p(-3)
TPM_RIGHTBUTTON = 0x0002
MF_STRING = 0x0000
ID_OPEN = 1001
ID_RESTART = 1002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_longlong, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


_wndproc_hold = None
_on_open: Optional[Callable[[], None]] = None
_on_restart: Optional[Callable[[], None]] = None
_nid: Optional[NOTIFYICONDATAW] = None
_hicon = None


def _load_icon() -> int:
    if ICON_PATH.is_file():
        handle = user32.LoadImageW(
            None,
            str(ICON_PATH),
            IMAGE_ICON,
            0,
            0,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )
        if handle:
            return handle
    return user32.LoadIconW(None, ctypes.cast(IDI_APPLICATION, wintypes.LPCWSTR))


def _wndproc(hwnd, msg, wparam, lparam):
    if msg == WM_TRAY:
        ev = int(lparam) & 0xFFFF
        if ev == WM_LBUTTONUP and _on_open:
            try:
                _on_open()
            except Exception:
                pass
            return 0
        if ev == WM_RBUTTONUP:
            _popup(hwnd)
            return 0
    if msg == WM_COMMAND:
        cmd = int(wparam) & 0xFFFF
        if cmd == ID_OPEN and _on_open:
            try:
                _on_open()
            except Exception:
                pass
        elif cmd == ID_RESTART and _on_restart:
            try:
                _on_restart()
            except Exception:
                pass
        return 0
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def _popup(hwnd) -> None:
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    menu = user32.CreatePopupMenu()
    user32.AppendMenuW(menu, MF_STRING, ID_OPEN, "Open console")
    user32.AppendMenuW(menu, MF_STRING, ID_RESTART, "Restart worker")
    user32.SetForegroundWindow(hwnd)
    user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON, pt.x, pt.y, 0, hwnd, None)
    user32.DestroyMenu(menu)


def _add_icon(hwnd) -> bool:
    global _nid, _hicon
    _hicon = _load_icon()
    nid = NOTIFYICONDATAW()
    nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    nid.hWnd = hwnd
    nid.uID = 1
    nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
    nid.uCallbackMessage = WM_TRAY
    nid.hIcon = _hicon
    nid.szTip = "ATE console (worker 8766)"
    _nid = nid
    return bool(shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)))


def _del_icon() -> None:
    if _nid is not None:
        try:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(_nid))
        except Exception:
            pass


def run_tray(
    on_open: Callable[[], None],
    on_restart: Callable[[], None],
    stop: threading.Event,
) -> bool:
    """Block on a hidden message window until stop is set. False = tray unavailable."""
    global _wndproc_hold, _on_open, _on_restart
    if sys.platform != "win32":
        return False
    _on_open = on_open
    _on_restart = on_restart
    _wndproc_hold = WNDPROC(_wndproc)
    wc = WNDCLASSW()
    wc.lpfnWndProc = _wndproc_hold
    wc.hInstance = kernel32.GetModuleHandleW(None)
    wc.lpszClassName = "AteSupervisorTray"
    atom = user32.RegisterClassW(ctypes.byref(wc))
    if not atom:
        err = kernel32.GetLastError()
        if err not in (1410,):  # already registered
            return False
    hwnd = user32.CreateWindowExW(
        0,
        wc.lpszClassName,
        "ATE",
        0,
        0,
        0,
        0,
        0,
        HWND_MESSAGE,
        None,
        wc.hInstance,
        None,
    )
    if not hwnd:
        return False
    if not _add_icon(hwnd):
        user32.DestroyWindow(hwnd)
        return False
    msg = wintypes.MSG()
    try:
        while not stop.is_set():
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                if msg.message == WM_QUIT:
                    stop.set()
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            stop.wait(0.25)
    finally:
        _del_icon()
        try:
            user32.DestroyWindow(hwnd)
        except Exception:
            pass
    return True
