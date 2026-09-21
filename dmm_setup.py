"""Keithley DMM6500 helpers. Golden tokens only -- do not paste web SCPI.

DMM6500 SYST:ERR **-113** = undefined header (same class as Rigol -116).
Do not *RST. :CONF:<func> switches the front panel. Then :READ?.

Allowlist:
  *CLS
  :CONF:VOLT:DC
  :CONF:CURR:DC
  :CONF:CAP
  :SENS:FUNC 'VOLT:DC' | 'CURR:DC' | 'CAP'   (single quotes)
  (VOLT RANG:AUTO is -113 -- CONF:VOLT:DC is enough)
  (CURR SENS:RANG / CONF 0.01 arity are -113 -- CONF:CURR:DC is enough)
  :SENS:CAP:RANG:AUTO ON
  :READ?
  SYST:ERR?
  :HCOP:SDUM:DATA?   (optional; DMM6500 1.7.16a often -113)

Banned: *RST, :MEAS:CURR?, :SENS:CURR:NPLC (no DC), :SENS:CURR:AZER,
:SENS:CURR:AVER..., :TRAC:CLE. IDD averaging is the 5 s settle + one :READ?.
Do not send :HCOP:SDUM:DATA:FORM -- that header is -113 on this box.
Screen dump is DMM only -- not Rigol :DISP:DATA? (MSO). USB HCOP leftover
falls back to a :READ? reading card PNG (still DMM, never MSO).
"""
from __future__ import annotations

import struct
import time
import zlib
from pathlib import Path

_CONF = {
    "VOLT:DC": ":CONF:VOLT:DC",
    "CURR:DC": ":CONF:CURR:DC",
    "CAP": ":CONF:CAP",
}


def _syst_err(dmm) -> str:
    try:
        return str(dmm.query("SYST:ERR?")).strip()
    except Exception:
        return ""


def _func(dmm, name: str) -> None:
    dmm.write("*CLS")
    conf = _CONF.get(name)
    if conf:
        dmm.write(conf)
    # Golden RS1G07 used single quotes. Keep them -- DMM6500 is picky.
    dmm.write(f":SENS:FUNC '{name}'")
    time.sleep(0.2)
    err = _syst_err(dmm)
    if err and not err.startswith("0"):
        print(f"DMM SYST:ERR after CONF {name} {err}", flush=True)


def dmm_read(dmm):
    return float(dmm.query(":READ?"))


def dmm_read_avg(dmm, n=5):
    values = [float(dmm.query(":READ?")) for _ in range(n)]
    return sum(values) / len(values)


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
    dmm.write("*CLS")
    dmm.write(":CONF:CURR:DC")
    time.sleep(0.2)
    err = _syst_err(dmm)
    if err and not err.startswith("0"):
        print(f"DMM SYST:ERR after CONF CURR:DC {err}", flush=True)
    return dmm_read(dmm)


def dmm_setup_current_continuous(dmm, avg_count=10, nplc=1):
    """Same as dmm_setup_current. NPLC/AZER/AVER/TRAC were DMM6500 -113."""
    return dmm_setup_current(dmm)


def dmm_setup_cap(dmm):
    _func(dmm, "CAP")
    dmm.write(":SENS:CAP:RANG:AUTO ON")
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
    """DMM dump. Not MSO. DMM6500 1.7.16a has no USB HCOP -- reading card PNG."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    if getattr(dmm, "simulated", False) or type(dmm).__name__ == "SimResource":
        dest = path.with_suffix(".png")
        dest.write_bytes(_SIM_PNG)
        return str(dest)
    val = reading
    if val is None:
        try:
            val = float(dmm.query(":READ?"))
        except Exception:
            val = None
    if val is None:
        body = "NO READ"
    else:
        body = f"{float(val):.6g} {unit}".strip()
    dest = path.with_suffix(".png")
    dest.write_bytes(_reading_png("DMM6500 DCI", body))
    print(f"DMM HCOP leftover; reading card {body}", flush=True)
    return str(dest)
