"""DC CMRR: Vs=5.5 V, Vcm -0.1 V then 4 V (RS62X 7.4), DMM error Vout-Vin.

CMRR_dB = 20*log10(|dVcm|/|d(Vout-Vin)|). BUFFER follower. Not a screenshot.
"""
from __future__ import annotations

import math
import time

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_VS = 5.5
_VCM = (-0.1, 4.0)


def _db(num: float, den: float) -> float:
    floor = 1e-6
    d = abs(den) if abs(den) >= floor else floor
    return 20.0 * math.log10(abs(num) / d)


def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook(
        "CMRR DC: BUFFER DUT; PSU CH1=+2.75 CH2=-2.75 (Vs=5.5); "
        "AWG CH1 DC Vcm; DMM VDC on VOUT. Continue."
    ):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: PSU, DMM")
    if getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: AWG")
    from dmm_setup import dmm_read, dmm_setup_voltage
    from generator_setup import setup_dc, stop_output
    from psu_setup import power_off, power_on_protected

    ilim = float(params.current_limit_a or 0.1)
    rail = _VS / 2.0
    settle = 0.3
    rows: list[dict[str, float]] = []
    try:
        power_on_protected(instr.psu, 1, rail, ilim)
        power_on_protected(instr.psu, 2, rail, ilim)
        dmm_setup_voltage(instr.dmm)
        for vcm in _VCM:
            setup_dc(instr.gen, 1, vcm)
            time.sleep(settle)
            vout = float(dmm_read(instr.dmm))
            rows.append({"Vcm": vcm, "Vout": vout, "err": vout - vcm})
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
    if len(rows) < 2:
        return {"summary": "aborted", "data": {"rows": rows}}
    dvcm = rows[1]["Vcm"] - rows[0]["Vcm"]
    derr = rows[1]["err"] - rows[0]["err"]
    cmrr = _db(dvcm, derr)
    return {
        "summary": f"CMRR={cmrr:.1f} dB dVcm={dvcm:.2f} derr={derr:.6g}",
        "data": {"Vcm_lo": rows[0], "Vcm_hi": rows[1], "CMRR_dB": cmrr},
        "measurements": [{"id": "CMRR_dB", "value": round(cmrr, 2), "unit": "dB"}],
    }


register(
    TestSpec(
        id="cmrr",
        label="CMRR (DC Vcm step)",
        required_instruments=frozenset({"PSU", "DMM", "AWG"}),
        fixture_mode="ATE",
        lab_sheet="CMRR",
        run=run,
        dual_channel=False,
        notes="DC CMRR Vcm=-0.1 to 4 V at Vs=5.5. Not a screenshot.",
        fixed_steps=[{"id": "measure", "label": "Step Vcm, read Vout-Vin", "phase": "measure"}],
    )
)
