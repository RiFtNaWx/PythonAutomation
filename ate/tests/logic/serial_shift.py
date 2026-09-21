"""RS164 8-bit serial-in: 8 CLK edges then DMM on Q7.

A AND B must both be high to shift a 1 (functional table). Strap B to VCC;
AWG CH2 drives A. Not combinational VOH and not CLK-to-Q0 delay.
"""
from __future__ import annotations

import time

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams


def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook(
        "RS164 serial: PSU CH1=VCC; strap B=/MR=VCC; AWG CH1=CLK CH2=A; "
        "DMM VDC on Q7. Continue."
    ):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: DMM")
    from dmm_setup import dmm_read, dmm_setup_voltage
    from generator_setup import setup_dc, setup_square, stop_output
    from psu_setup import power_off, power_on_protected

    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    freq = 1000.0
    dwell = 8.0 / freq + 0.05
    q_hi = float("nan")
    q_lo = float("nan")
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_square(instr.gen, 1, freq, vcc, vcc / 2.0)
        setup_dc(instr.gen, 2, vcc)
        time.sleep(dwell)
        dmm_setup_voltage(instr.dmm)
        q_hi = float(dmm_read(instr.dmm))
        setup_dc(instr.gen, 2, 0.0)
        time.sleep(dwell)
        q_lo = float(dmm_read(instr.dmm))
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
    return {
        "summary": f"Q7 8x1={q_hi:.4f} V 8x0={q_lo:.4f} V",
        "data": {"VCC": vcc, "Q7_HIGH_V": q_hi, "Q7_LOW_V": q_lo},
        "measurements": [
            {"id": "Q7_HIGH_V", "value": round(q_hi, 6), "unit": "V"},
            {"id": "Q7_LOW_V", "value": round(q_lo, 6), "unit": "V"},
        ],
    }


register(
    TestSpec(
        id="serial_shift",
        label="8-bit Serial Shift (Q7)",
        required_instruments=frozenset({"PSU", "AWG", "DMM"}),
        fixture_mode="LOGIC",
        lab_sheet="Q7",
        run=run,
        dual_channel=False,
        notes="RS164 8 CLK then Q7. Strap B high. Not AND-gate tp.",
    )
)
