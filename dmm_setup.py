"""Keithley DMM6500 helpers. Golden tokens only -- do not paste web SCPI.

DMM6500 SYST:ERR **-113** = undefined header (same class as Rigol -116).
Do not *RST. :CONF:<func> switches the front panel. Then :READ?.
Live writes/SYST:ERR go to ate/worker/dmm_scpi.log -- last_worker.log is RPC only.

Allowlist:
  *CLS
  SYST:CLE
  :CONF:VOLT:DC
  :CONF:CURR:DC
  :CONF:CAP
  (extra :SENS:FUNC after CONF is -113 on 1.7.16a -- CONF already switches)
  (VOLT RANG:AUTO is -113 -- CONF:VOLT:DC is enough)
  (CURR SENS:RANG / CONF 0.01 arity are -113 -- CONF:CURR:DC is enough)
  :SENS:CAP:RANG:AUTO ON
  :READ?
  SYST:ERR?

Banned: *RST, :MEAS:CURR?, :SENS:CURR:NPLC / AZER / AVER / :TRAC:CLE,
:HCOP:SDUM:DATA? and DATA:FORM. Do not send :HCOP:SDUM:DATA:FORM -- that
header is -113 on this box. Those pop the front-panel error and block
:READ? until OK -- then SAFE IDLE kills PSU outputs.

Filter / NPLC / span-rdgs: set Rate + Filter on the box MENU. SCPI NPLC/AVER
is -113 on 1.7.16a. Console filter is host-side: clear active buffer (*CLS +
drain SYST:ERR), then n :READ? (default 5), then mean. :READ? already waits
the box NPLC -- do not add a host sleep. Do not send TRAC:CLE.

Screen dump is a :READ? reading-card PNG (still DMM, never MSO). Never HCOP
(that screenshot is the SCPI header dialog).
"""
from __future__ import annotations

import statistics
import struct
import time
import zlib
from datetime import datetime
from pathlib import Path

# last_worker.log is HTTP RPC only -- print() never lands there. This file does.
_SCPI_LOG = Path(__file__).resolve().parent / "ate" / "worker" / "dmm_scpi.log"


def _trace(msg: str) -> None:
    print(msg, flush=True)
    try:
        _SCPI_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _SCPI_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass

_CONF = {
    "VOLT:DC": ":CONF:VOLT:DC",
    "CURR:DC": ":CONF:CURR:DC",
    "CAP": ":CONF:CAP",
}


def is_banned_dmm_scpi(cmd: str) -> bool:
    """True if this DMM6500 1.7.16a would queue SYST:ERR -113."""
    n = str(cmd or "").upper().replace(" ", "")
    if n.startswith("*RST"):
        return True
    if "HCOP" in n:
        return True
    if "MEAS:CURR" in n:
        return True
    if any(tok in n for tok in ("NPLC", "AZER", "AVER")):
        return True
    if "TRAC" in n:
        return True
    if "RANG:AUTO" in n and "CAP" not in n:
        return True
    if "CURR:DC:RANG" in n:
        return True
    if "0.0001" in n or "1E-4" in n:
        return True
    if "SENS:FUNC" in n:
        return True
    return False


def _syst_err(dmm) -> str:
    try:
        return str(dmm.query("SYST:ERR?")).strip()
    except Exception:
        return ""


def dmm_drain_errors(dmm, *, limit: int = 10) -> list[str]:
    """SYST:ERR? until 0. Clears the front-panel header dialog so :READ? is not blocked."""
    found: list[str] = []
    for _ in range(max(1, int(limit))):
        err = _syst_err(dmm)
        if not err or err.startswith("0"):
            break
        # Keithley is `-113,"Undefined header"`. A raw float is a :READ? stub, not an error.
        if "," not in err and not err.lstrip().startswith("-"):
            break
        found.append(err)
        _trace(f"DMM SYST:ERR drain {err}")
    return found


def clear_active_buffer(dmm) -> None:
    """Clear error queue + active reading path. Never TRAC:CLE (that is -113)."""
    try:
        _trace("DMM write *CLS")
        dmm.write("*CLS")
    except Exception as exc:
        _trace(f"DMM write fail '*CLS': {exc}")
    dmm_drain_errors(dmm)


_EVENT_LOG_CLEARED = False


def dmm_dismiss_header(dmm) -> None:
    """Drop leftover Event Log so the operator does not see old -113.

    SYST:ERR? drains the queue. Keithley Event Log on screen is separate.
    SYST:CLE clears that log. Send it once per worker process -- if this
    firmware returns -113, do not retry.
    """
    global _EVENT_LOG_CLEARED
    clear_active_buffer(dmm)
    if _EVENT_LOG_CLEARED:
        return
    _EVENT_LOG_CLEARED = True
    dmm_write_ok(dmm, "SYST:CLE")
    dmm_drain_errors(dmm)


def dmm_write_ok(dmm, cmd: str) -> bool:
    """Write allowlist only. Drain immediately so a bad header never sticks on screen."""
    if is_banned_dmm_scpi(cmd):
        _trace(f"DMM skip banned header {cmd!r}")
        return False
    try:
        _trace(f"DMM write {cmd}")
        dmm.write(cmd)
    except Exception as exc:
        _trace(f"DMM write fail {cmd!r}: {exc}")
        clear_active_buffer(dmm)
        return False
    err = _syst_err(dmm)
    if err and not err.startswith("0"):
        if "," not in err and not err.lstrip().startswith("-"):
            return True
        _trace(f"DMM SYST:ERR after {cmd} {err}")
        clear_active_buffer(dmm)
        return False
    return True


def _func(dmm, name: str) -> None:
    dmm_dismiss_header(dmm)
    conf = _CONF.get(name)
    if conf:
        dmm_write_ok(dmm, conf)
    # Do not send :SENS:FUNC '{name}' -- extra FUNC after CONF is -113 on 1.7.16a.
    time.sleep(0.2)
    dmm_drain_errors(dmm)


def dmm_read(dmm):
    """One recorded value: clear active buffer, 5 readings, mean."""
    return dmm_read_avg(dmm)


def dmm_read_avg(dmm, n=5, nplc=1):
    """Host-side repeat filter. Clear buffer, n readings, mean.

    nplc is the Rate on the DMM MENU. :READ? already waits that NPLC -- do not
    add a host sleep (it stacked past 50 ms SIM settle timeouts).
    """
    del nplc
    clear_active_buffer(dmm)
    count = max(1, int(n or 5))
    values = [float(dmm.query(":READ?")) for _ in range(count)]
    return float(statistics.mean(values))


def dmm_setup_voltage(dmm):
    # CONF:VOLT:DC already picks auto range. Extra :SENS:VOLT:DC:RANG:AUTO ON
    # is -113 (undefined header) on this DMM6500 -- do not re-send it.
    _func(dmm, "VOLT:DC")
    time.sleep(0.1)
    return dmm_read(dmm)


def dmm_setup_current(dmm, range_a: float = 0.01):
    """Switch front panel to DCI. Fixed 10 mA (AUTO hangs).

    Allowlist is :CONF:CURR:DC only (no range arity).
    DMM6500 1.7.16a: CONF/RANG 0.0001 is -113. Extra :SENS:CURR:DC:RANG
    0.01 and CONF:CURR:DC 0.01 were also -113 on this box.
    range_a is API compat only -- do not send 100 uA / 1 mA on the wire.
    """
    del range_a  # ponytail: CONF:CURR:DC only; extra FUNC/RANG were -113
    dmm_dismiss_header(dmm)
    dmm_write_ok(dmm, ":CONF:CURR:DC")
    time.sleep(0.2)
    dmm_drain_errors(dmm)
    return dmm_read(dmm)


def dmm_setup_current_continuous(dmm, avg_count=10, nplc=1):
    """CONF only. Hardware NPLC/AZER/AVER/TRAC are -113; avg is dmm_read_avg."""
    del avg_count, nplc
    return dmm_setup_current(dmm)


def dmm_setup_cap(dmm):
    _func(dmm, "CAP")
    dmm_write_ok(dmm, ":SENS:CAP:RANG:AUTO ON")
    time.sleep(0.2)
    return dmm_read(dmm)


def measure_voltage(dmm):
    return dmm_setup_voltage(dmm)


def measure_current(dmm):
    return dmm_setup_current(dmm)


def measure_capacitance(dmm):
    return dmm_setup_cap(dmm)


# 1x1 PNG so SIM / DEMO has a real file when HCOP is not on the USB box.
_SIM_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def _ieee_payload(raw: bytes) -> bytes:
    if not raw:
        return b""
    if raw[:1] != b"#":
        return raw
    try:
        nlen = int(chr(raw[1]))
        nbytes = int(raw[2 : 2 + nlen])
        return raw[2 + nlen : 2 + nlen + nbytes]
    except (ValueError, IndexError):
        return raw


# 5x7 glyphs for a DMM reading card when USB HCOP is leftover (-113).
_GLYPH = {
    " ": "00000\n00000\n00000\n00000\n00000\n00000\n00000",
    "0": "01110\n10001\n10011\n10101\n11001\n10001\n01110",
    "1": "00100\n01100\n00100\n00100\n00100\n00100\n01110",
    "2": "01110\n10001\n00001\n00010\n00100\n01000\n11111",
    "3": "01110\n10001\n00001\n00110\n00001\n10001\n01110",
    "4": "00010\n00110\n01010\n10010\n11111\n00010\n00010",
    "5": "11111\n10000\n11110\n00001\n00001\n10001\n01110",
    "6": "01110\n10000\n11110\n10001\n10001\n10001\n01110",
    "7": "11111\n00001\n00010\n00100\n01000\n01000\n01000",
    "8": "01110\n10001\n10001\n01110\n10001\n10001\n01110",
    "9": "01110\n10001\n10001\n01111\n00001\n00001\n01110",
    ".": "00000\n00000\n00000\n00000\n00000\n00100\n00100",
    "-": "00000\n00000\n00000\n01110\n00000\n00000\n00000",
    "+": "00000\n00100\n00100\n11111\n00100\n00100\n00000",
    ":": "00000\n00100\n00100\n00000\n00100\n00100\n00000",
    "A": "01110\n10001\n10001\n11111\n10001\n10001\n10001",
    "C": "01110\n10001\n10000\n10000\n10000\n10001\n01110",
    "D": "11110\n10001\n10001\n10001\n10001\n10001\n11110",
    "I": "01110\n00100\n00100\n00100\n00100\n00100\n01110",
    "M": "10001\n11011\n10101\n10101\n10001\n10001\n10001",
    "O": "01110\n10001\n10001\n10001\n10001\n10001\n01110",
    "U": "10001\n10001\n10001\n10001\n10001\n10001\n01110",
    "V": "10001\n10001\n10001\n10001\n10001\n01010\n00100",
    "Y": "10001\n10001\n01010\n00100\n00100\n00100\n00100",
    "Z": "11111\n00001\n00010\n00100\n01000\n10000\n11111",
}


def _reading_png(line1: str, line2: str = "") -> bytes:
    """RGB PNG reading card. ponytail: not front-panel pixels; HCOP leftover."""
    scale = 4
    pad = 16
    gh, gw = 7, 5
    lines = [str(line1 or "DMM"), str(line2 or "")]
    cols = max((len(s) for s in lines), default=1)
    w = pad * 2 + cols * (gw + 1) * scale
    h = pad * 2 + len(lines) * (gh + 2) * scale
    pix = bytearray(b"\x12\x14\x18" * (w * h))

    def _put(x: int, y: int, rgb: bytes) -> None:
        if 0 <= x < w and 0 <= y < h:
            i = (y * w + x) * 3
            pix[i : i + 3] = rgb

    def _draw(text: str, ox: int, oy: int) -> None:
        for ci, ch in enumerate(text.upper()):
            rows = _GLYPH.get(ch, _GLYPH[" "]).split("\n")
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit != "1":
                        continue
                    for dy in range(scale):
                        for dx in range(scale):
                            _put(
                                ox + (ci * (gw + 1) + rx) * scale + dx,
                                oy + ry * scale + dy,
                                b"\xe8\xf0\xff",
                            )

    _draw(lines[0][:48], pad, pad)
    if lines[1]:
        _draw(lines[1][:48], pad, pad + (gh + 2) * scale)

    raw = b"".join(b"\x00" + bytes(pix[y * w * 3 : (y + 1) * w * 3]) for y in range(h))

    def _chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )


def capture_screen(dmm, filepath, reading=None, unit: str = "A") -> str:
    """DMM dump. Not MSO. Never HCOP (that PNG is the SCPI header dialog)."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if getattr(dmm, "simulated", False) or type(dmm).__name__ == "SimResource":
        dest = path.with_suffix(".png")
        dest.write_bytes(_SIM_PNG)
        return str(dest)
    drained = dmm_drain_errors(dmm)
    if drained:
        _trace("DMM screen: drained header error; no HCOP")
    val = reading
    if val is None:
        try:
            val = dmm_read(dmm)
        except Exception:
            val = None
    if val is None:
        body = "NO READ"
    else:
        body = f"{float(val):.6g} {unit}".strip()
    dest = path.with_suffix(".png")
    dest.write_bytes(_reading_png("DMM6500 DCI", body))
    _trace(f"DMM reading card {body}")
    return str(dest)
