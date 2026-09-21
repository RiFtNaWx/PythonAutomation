"""Combinational CMOS A->Y tPD. Not I2C buffer. Not DFF clk_q.

AND: strap B=VCC. OR: strap B=GND. Open-drain: 10k pull-up Y. 3-state: /OE=GND.
Do not drive reverse on AWG CH2 -- that pin is the other input, not Y->A.
"""
from __future__ import annotations

from typing import Any

from ate.core.runner import RunParams

_AND = frozenset({"rs1g08", "rs1gt08"})
_OR = frozenset({"rs1g32", "rs1gt32", "rs1gt32d"})
_OD = frozenset({"rs1g07", "rs74aup1g07"})
_OE_LOW = frozenset({"rs1g125"})
_INVERT = frozenset({"rs1g14"})


def _part(params: RunParams) -> str:
    return str(getattr(params, "part", "") or "").strip().lower()


def _wire(pk: str) -> str:
    bits = [
        "CMOS tPD: PSU CH1=VCC; AWG CH1=A 0..VCC square; MSO CH1=A CH2=Y.",
    ]
    if pk in _AND:
        bits.append("AND: AWG CH2=B=VCC DC. Do not reverse-drive CH2.")
    elif pk in _OR:
        bits.append("OR: AWG CH2=B=GND DC. Do not reverse-drive CH2.")
    elif pk in _OD:
        bits.append("Open-drain: 10k pull-up Y to VCC.")
    elif pk in _OE_LOW:
        bits.append("RS1G125: jumper /OE to GND.")
    elif pk in _INVERT:
        bits.append(
            "Inverter: Y is not A. MSO RFDelay A-rise->Y-fall and FRDelay A-fall->Y-rise."
        )
    else:
        bits.append("Buffer: Y follows A. No AWG CH2 reverse.")
    bits.append("Continue.")
    return " ".join(bits)


def _run_cmos(instr, params: RunParams, *, freq_hz: float, timebase_s: float, idle: bool) -> dict[str, Any]:
    pk = _part(params)
    hook = params.pause_hook
    if hook is not None and not hook(_wire(pk)):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_dc, setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    strap = "none"
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        if pk in _AND:
            setup_dc(instr.gen, 2, vcc)
            strap = "VCC"
        elif pk in _OR:
            setup_dc(instr.gen, 2, 0.0)
            strap = "GND"
        setup_square(instr.gen, 1, freq_hz, vcc, vcc / 2.0)
        scope_setup(instr.scope, timebase_s, vcc / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        if pk in _INVERT:
            item_hl, item_lh = "RFDelay", "FRDelay"
        else:
            item_hl, item_lh = "FFDelay", "RRDelay"
        t_hl = abs(measure_delay(instr.scope, item_hl, 1, 2)) * 1e9
        t_lh = abs(measure_delay(instr.scope, item_lh, 1, 2)) * 1e9
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
        mids = (("TIDLE_PHL_ns", t_hl), ("TIDLE_PLH_ns", t_lh))
        data = {
            "VCC": vcc,
            "cmos_prop": True,
            "strap_b": strap,
            "invert": pk in _INVERT,
            "delay_hl": item_hl,
            "delay_lh": item_lh,
            "TIDLE_PHL_ns": t_hl,
            "TIDLE_PLH_ns": t_lh,
        }
    else:
        mids = (("TPD_PHL_ns", t_hl), ("TPD_PLH_ns", t_lh))
        data = {
            "VCC": vcc,
            "cmos_prop": True,
            "strap_b": strap,
            "invert": pk in _INVERT,
            "delay_hl": item_hl,
            "delay_lh": item_lh,
            "TPD_PHL_ns": t_hl,
            "TPD_PLH_ns": t_lh,
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
    return _run_cmos(instr, params, freq_hz=400000.0, timebase_s=1e-6, idle=False)


def run_tidle(instr, params: RunParams) -> dict[str, Any]:
    return _run_cmos(instr, params, freq_hz=100000.0, timebase_s=500e-9, idle=True)
