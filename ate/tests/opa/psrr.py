"""DC PSRR: hold Vin, step total Vs 2.5 V -> 5.5 V (RS62X 7.4), DMM on Vout.

PSRR_dB = 20*log10(|dVs|/|dVout|). BUFFER follower. Dual-rail CH1/CH2 = Vs/2.
Do not wrap Eugene test_SSR (delay + input()) as PSRR.
"""
from __future__ import annotations

import math
import time

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_VS_LO = 2.5
_VS_HI = 5.5


def _db(dvs: float, dvout: float) -> float:
    floor = 1e-6
    den = abs(dvout) if abs(dvout) >= floor else floor
    return 20.0 * math.log10(abs(dvs) / den)


def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook(
        "PSRR DC: BUFFER DUT; PSU CH1=+Vs/2 CH2=-Vs/2; AWG CH1 DC 0 V (mid); "
        "DMM VDC on VOUT. Continue."
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
    settle = 0.3
    rows: list[dict[str, float]] = []
    try:
        setup_dc(instr.gen, 1, 0.0)
        dmm_setup_voltage(instr.dmm)
        for vs in (_VS_LO, _VS_HI):
            rail = vs / 2.0
            power_on_protected(instr.psu, 1, rail, ilim)
            power_on_protected(instr.psu, 2, rail, ilim)
            time.sleep(settle)
            vout = float(dmm_read(instr.dmm))
            rows.append({"Vs": vs, "Vout": vout})
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
    dvs = rows[1]["Vs"] - rows[0]["Vs"]
    dvout = rows[1]["Vout"] - rows[0]["Vout"]
    psrr = _db(dvs, dvout)
    return {
        "summary": f"PSRR={psrr:.1f} dB dVs={dvs:.2f} dVout={dvout:.6g}",
        "data": {"Vs_lo": rows[0], "Vs_hi": rows[1], "PSRR_dB": psrr},
        "measurements": [{"id": "PSRR_dB", "value": round(psrr, 2), "unit": "dB"}],
    }


register(
    TestSpec(
        id="psrr",
        label="PSRR (DC Vs step)",
        required_instruments=frozenset({"PSU", "DMM", "AWG"}),
        fixture_mode="ATE",
        lab_sheet="PSRR",
        run=run,
        dual_channel=False,
        notes="DC PSRR Vs=2.5 to 5.5. Not Eugene SSR delay. Not a screenshot.",
        fixed_steps=[{"id": "measure", "label": "Step Vs, read Vout", "phase": "measure"}],
    )
)
