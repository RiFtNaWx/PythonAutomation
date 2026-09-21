# scope_setup.py
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from typing import Callable, List, Optional, Union, Generator
from configurations import *
from instruments import find_instruments 
import time
import os
import logging
import sys
import pyvisa

def measure_delay(scope, item, ch1, ch2):
    scope.write(f":Measure:ITEM {item},CHAN{ch1},CHAN{ch2}")
    time.sleep(1)
    result = scope.query(
        f":Measure:Statistic:ITEM? AVERages,{item},CHAN{ch1},CHAN{ch2}"
    )
    return float(result)
    
def measure_single(scope, item, ch):
    scope.write(f":Measure:ITEM {item},CHAN{ch}")
    time.sleep(1)
    result = scope.query(
    f":Measure:Statistic:ITEM? AVERages,{item},CHAN{ch}"
    )
    return float(result)
    
def scope_setup(scope, time_scale, trig_level):
    scope.write(":AUToscale")
    time.sleep(2)
    scope.write(f"TIMebase:MAIN:SCAle {time_scale}")
    scope.write(":TRIGger:EDGE:SLOPe POSitive")
    scope.write(f":TRIGger:EDGE:LEVel {trig_level}")
    time.sleep(1)
    scope.write(":SYSTem:KEY:PRESs MOFF")

def set_threshold(scope, ch):
    scope.write(f":Measure:THR:SOURce CHAN{ch}")
    scope.write(":Measure:SETup:MAX 80")
    scope.write(":Measure:SETup:MIN 20")
    scope.write(":Measure:SETup:MID 50")
 

@contextmanager
def connect_scope(
    config: Optional[ScopeConfig] = None,
    auto_disconnect: bool = True
) -> Generator[Optional[ScopeDevice], None, None]:
    """
    示波器连接上下文管理器
    
    使用示例:
        with connect_scope() as scope:
            if scope:
                print(scope.query("*IDN?"))
    
    Args:
        config: 连接配置
        auto_disconnect: 是否自动断开连接
        
    Yields:
        连接的设备对象，连接失败返回None
    """
    connector = ScopeConnector(config)
    device = None
    
    try:
        device = connector.connect()
        yield device
    except ScopeConnectionError as e:
        logging.getLogger("rigol_scope").error(f"连接失败: {e}")
        yield None
    finally:
        if auto_disconnect:
            connector.disconnect()

def _png_bytes_to_jpeg_file(png_bytes: bytes, path: Path, quality: int = 90) -> None:
    """Re-encode Rigol :DISP:DATA? PNG payload as JPEG (Excel-friendly)."""
    from io import BytesIO

    from PIL import Image

    img = Image.open(BytesIO(png_bytes))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.save(path, format="JPEG", quality=quality, optimize=True)


def recover_scope_session(scope, *, clear: bool = True, run: bool = True) -> None:
    """Clear VISA errors; optionally return scope to RUN (default) or park STOP."""
    if clear:
        try:
            scope.clear()
        except Exception:
            pass
        # Drain leftover :DISP:DATA? bytes that poison the next query
        try:
            old_to = scope.timeout
            scope.timeout = 150
            try:
                for _ in range(8):
                    scope.read_raw()
            except Exception:
                pass
            finally:
                try:
                    scope.timeout = old_to
                except Exception:
                    pass
        except Exception:
            pass
        try:
            scope.write("*CLS")
        except Exception:
            pass
    try:
        scope.write(":STOP")
    except Exception:
        pass
    time.sleep(0.15)
    if run:
        try:
            scope.write(":RUN")
        except Exception:
            pass
        time.sleep(0.45)
    # Handshake — proves SCPI is alive again
    try:
        scope.query("*IDN?")
    except Exception:
        try:
            scope.clear()
            scope.write("*CLS")
            time.sleep(0.3)
            scope.query("*IDN?")
        except Exception:
            pass


def park_scope_idle(scope, *, clear: bool = True) -> None:
    """STOP scope and clear VISA — do not RUN (operator wait / bench safe idle)."""
    recover_scope_session(scope, clear=clear, run=False)
    try:
        scope.write(":STOP")
    except Exception:
        pass


def capture_scope_png(scope, filepath, timeout_ms=8000, jpeg_quality: int = 90):
    """Capture scope screen via :DISP:DATA? on an existing PyVISA session.

    Rigol returns PNG binary. If ``filepath`` ends with ``.jpg`` / ``.jpeg``,
    auto-converts to JPEG (openpyxl / Excel insert-friendly). Otherwise writes PNG.
    """
    from utils import BinaryDataParser

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    original_timeout = scope.timeout
    raw = None
    try:
        scope.timeout = int(timeout_ms)
        try:
            scope.write(":SYSTem:KEY:PRESs MOFF")
        except Exception:
            pass
        scope.write(":DISP:DATA?")
        raw = scope.read_raw()
    finally:
        scope.timeout = original_timeout
        # Drain :DISP:DATA? leftover bytes, then RUN again.
        # park_scope_idle here froze slew/ORT/settling shots 2+ at STOP / Cnt=0.
        recover_scope_session(scope, clear=True, run=True)

    if raw is None:
        raise RuntimeError("scope :DISP:DATA? returned no bytes")

    png_bytes = BinaryDataParser.parse_visa_binary(raw)
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        _png_bytes_to_jpeg_file(png_bytes, path, quality=jpeg_quality)
    else:
        # Default / legacy: keep PNG bytes as-is
        if suffix != ".png":
            path = path.with_suffix(".png")
        path.write_bytes(png_bytes)
    return str(path)


def screenshot():
    """Hook used by root logic_tests TP wraps. Live PNGs are runner capture_scope_png.

    The old body was a Chinese demo that printed to cp1252 stdout and opened a
    second AutoCapture session -- that crashed every TP START on Windows.
    """
    return None
 
 