"""OpAmp rail swing: BUFFER VOH/VOL via DMM. Not a screenshot.

Vin near +rail then -rail. Stamp VOH_V / VOL_V. No invented min/max
(RS62X extract has no VOH/VOL table numbers).
"""
from __future__ import annotations

import time

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_VS = 5.5


def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook(
        "VOHL: BUFFER DUT; PSU CH1=+2.75 CH2=-2.75 (Vs=5.5); "
        "AWG CH1 DC near +rail then -rail; DMM VDC on VOUT. Continue."
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
    head = 0.1
    settle = 0.3
    voh = float("nan")
    vol = float("nan")
    try:
        power_on_protected(instr.psu, 1, rail, ilim)
        power_on_protected(instr.psu, 2, rail, ilim)
        dmm_setup_voltage(instr.dmm)
        setup_dc(instr.gen, 1, rail - head)
        time.sleep(settle)
        voh = float(dmm_read(instr.dmm))
        setup_dc(instr.gen, 1, -(rail - head))
        time.sleep(settle)
        vol = float(dmm_read(instr.dmm))
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
        "summary": f"VOH={voh:.4f} V VOL={vol:.4f} V",
        "data": {"Vs": _VS, "VOH_V": voh, "VOL_V": vol},
        "measurements": [
            {"id": "VOH_V", "value": round(voh, 6), "unit": "V"},
            {"id": "VOL_V", "value": round(vol, 6), "unit": "V"},
        ],
    }


register(
    TestSpec(
        id="vohl",
        label="VOH / VOL (rail swing)",
        required_instruments=frozenset({"PSU", "DMM", "AWG"}),
        fixture_mode="ATE",
        lab_sheet="VOL",
        run=run,
        dual_channel=False,
        notes="BUFFER rail swing DMM. Not a screenshot. No invented min/max.",
        fixed_steps=[{"id": "measure", "label": "Drive +rail/-rail, read VOUT", "phase": "measure"}],
    )
)
