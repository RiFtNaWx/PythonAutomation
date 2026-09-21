"""RS2323 OFF isolation at 1 MHz. High-Z MSO probes, not 50 ohm RF.

ISO_dB = 20*log10(Vcom/Vnc) with IN selecting the other throw (NC OFF).
SIM CHAN2 sine is the G11 GBW filter -- do not use it as COM residual.
MSO5072 is 70 MHz; this slot is 1 MHz isolation, not datasheet 110 MHz BW.
Not RS2227 USB DPDT.
"""
from __future__ import annotations

import math
from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.tests.lim.rs2323 import _is_usb, _part_cfg, _pause

_FIXTURE = "LIM_RS2323"
_FREQ_HZ = 1_000_000.0
_VPP = 1.0
# SIM OFF coupling vs Vin. Not G11 CHAN2, not a datasheet typ.
_SIM_COUPLE = 1e-3


def chan2_off_vpp(scope, vin: float, *, sim: bool, couple: float = _SIM_COUPLE) -> float:
    """Always query CHAN2 (same USB SCPI). SIM G11 1-pole is not OFF residual."""
    scope.write(":MEASure:ITEM VPP,CHAN2")
    vout = abs(float(scope.query(":MEASure:ITEM? VPP,CHAN2")))
    if sim:
        return max(float(vin), 1e-6) * float(couple)
    return vout


def _db(vout: float, vin: float) -> float:
    den = abs(vin) if abs(vin) >= 1e-6 else 1e-6
    num = abs(vout) if abs(vout) >= 1e-9 else 1e-9
    return 20.0 * math.log10(num / den)


def run(instr, params: RunParams) -> dict[str, Any]:
    if _is_usb():
        raise RuntimeError("iso is RS2323 SPDT OFF isolation. Not RS2227 USB DPDT.")
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_sine, stop_output
    from psu_setup import power_off, power_on_protected

    cfg = _part_cfg()
    vcc = float(params.vcc or cfg.get("vcc") or 5.0)
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    if not _pause(
        params,
        "ISO 1 MHz",
        [
            "IN1=GND (COM-NO ON, NC OFF).",
            "AWG CH1 1 MHz 1 Vpp on NC1; MSO CH1=NC1 CH2=COM1.",
            "High-Z probes. Not 50 ohm RF. Not 110 MHz BW.",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "ISO"}}
    vin = vout = 0.0
    sim = bool(getattr(instr.scope, "simulated", False))
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_sine(instr.gen, 1, _FREQ_HZ, _VPP, vcc / 2.0)
        instr.scope.write("TIMebase:MAIN:SCAle 1e-6")
        instr.scope.write(":MEASure:ITEM VPP,CHAN1")
        vin = abs(float(instr.scope.query(":MEASure:ITEM? VPP,CHAN1")))
        vout = chan2_off_vpp(instr.scope, vin, sim=sim, couple=_SIM_COUPLE)
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
    iso = _db(vout, vin)
    return {
        "summary": f"ISO={iso:.1f} dB Vin={vin:.4g} Vcom={vout:.4g} sim={sim}",
        "data": {
            "Test": "ISO",
            "VCC": vcc,
            "freq_hz": _FREQ_HZ,
            "Vin_Vpp": vin,
            "Vcom_Vpp": vout,
            "ISO_dB": iso,
            "sim_couple": sim,
        },
        "measurements": [{"id": "ISO_dB", "value": round(iso, 2), "unit": "dB"}],
    }


register(
    TestSpec(
        id="iso",
        label="Off Isolation (1 MHz)",
        required_instruments=frozenset({"PSU", "AWG", "MSO"}),
        fixture_mode=_FIXTURE,
        lab_sheet="ISO",
        run=run,
        dual_channel=False,
        notes="1 MHz high-Z ISO_dB. Not 50 ohm RF. Not 110 MHz BW. SIM not G11 CHAN2.",
        short_tag="ISO",
        fixed_steps=[
            {"id": "wire", "label": "Wire NC OFF + MSO then Continue", "phase": "operator"},
            {"id": "measure", "label": "Measure 1 MHz isolation", "phase": "measure"},
        ],
    )
)
