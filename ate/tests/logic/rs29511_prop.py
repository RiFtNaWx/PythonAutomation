"""RS29511 I2C buffer SDA/SCL propagation. Not CMOS 3-state. Not Soo wrap.

Datasheet 7.6: tPZL (HL) 30-50 ns, tPLZ (LH) 0-10 ns, both directions.
EN jumper to VCC. 10k pull-ups on SDA/SCL. AWG CH1 then CH2 for reverse.
"""
from __future__ import annotations

from typing import Any

from ate.core.runner import RunParams

_WIRE = (
    "RS29511 I2C buffer: EN=VCC jumper; 10k pull-up SDAIN/SCLIN/SDAOUT/SCLOUT; "
    "AWG CH1=SDAIN, MSO CH1=SDAIN CH2=SDAOUT, then reverse AWG CH2. Continue."
)


def _run_prop(instr, params: RunParams, *, freq_hz: float, timebase_s: float, idle: bool) -> dict[str, Any]:
    hook = params.pause_hook
    if hook is not None and not hook(_WIRE):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    t_hl = t_lh = t_hl_rev = t_lh_rev = float("nan")
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_square(instr.gen, 1, freq_hz, vcc, vcc / 2.0)
        scope_setup(instr.scope, timebase_s, vcc / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        t_hl = abs(measure_delay(instr.scope, "FFDelay", 1, 2)) * 1e9
        t_lh = abs(measure_delay(instr.scope, "RRDelay", 1, 2)) * 1e9
        if not idle:
            stop_output(instr.gen)
            setup_square(instr.gen, 2, freq_hz, vcc, vcc / 2.0)
            t_hl_rev = abs(measure_delay(instr.scope, "FFDelay", 2, 1)) * 1e9
            t_lh_rev = abs(measure_delay(instr.scope, "RRDelay", 2, 1)) * 1e9
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
    if idle:
        mids = (
            ("TIDLE_PHL_ns", t_hl),
            ("TIDLE_PLH_ns", t_lh),
        )
        data = {
            "VCC": vcc,
            "hotswap_prop": True,
            "TIDLE_PHL_ns": t_hl,
            "TIDLE_PLH_ns": t_lh,
        }
    else:
        mids = (
            ("TPD_PHL_ns", t_hl),
            ("TPD_PLH_ns", t_lh),
            ("TPD_REV_PHL_ns", t_hl_rev),
            ("TPD_REV_PLH_ns", t_lh_rev),
        )
        data = {
            "VCC": vcc,
            "hotswap_prop": True,
            "TPD_PHL_ns": t_hl,
            "TPD_PLH_ns": t_lh,
            "TPD_REV_PHL_ns": t_hl_rev,
            "TPD_REV_PLH_ns": t_lh_rev,
        }
    summary = " ".join(f"{k}={v:.2f} ns" for k, v in mids)
    return {
        "summary": summary,
        "data": data,
        "measurements": [
            {"id": mid, "value": round(val, 3), "unit": "ns"} for mid, val in mids
        ],
    }


def run_tp(instr, params: RunParams) -> dict[str, Any]:
    # 400 kHz Fast-mode class. 1 us/div ns-window (SIM ~50 ns).
    return _run_prop(instr, params, freq_hz=400000.0, timebase_s=1e-6, idle=False)


def run_tidle(instr, params: RunParams) -> dict[str, Any]:
    # 100 kHz. Same tPLZ/tPZL physics, longer timebase still ns-window.
    return _run_prop(instr, params, freq_hz=100000.0, timebase_s=500e-9, idle=True)
