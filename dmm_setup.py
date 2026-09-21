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

Banned: *RST, :MEAS:CURR?, :SENS:CURR:NPLC (no DC), :SENS:CURR:AZER,
:SENS:CURR:AVER..., :TRAC:CLE. IDD averaging is the 5 s settle + one :READ?.
"""
from __future__ import annotations

import time

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
