"""RS2227 USB 2.0 DPDT mux. Not RS2323 SPDT COM/NO/NC.

S selects HSD1 (S=0) or HSD2 (S=1). OE high = all off.
Do not enable rs2323 ron/ton_toff/con_coff/tbbm/vth on this SKU.
RON table is a PDF image -- stamp ohm, no invented min/max.
Banner tON 20 ns / tOFF 15 ns are typ only.
"""
from __future__ import annotations

import math
import time
from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.tests.lim.iso import _SIM_COUPLE, chan2_off_vpp
from ate.tests.lim.rs2323 import (
    _avg_v,
    _part_cfg,
    _pause,
    _power_off,
    _sweep_points,
)

_FIXTURE = "LIM_RS2323"
_NOTE = "USB DPDT (D+/D-/HSD). Not RS2323 SPDT pinout."


def _require(instr, *names: str) -> None:
    remap = {"MSO": "scope", "PSU": "psu", "AWG": "gen", "DMM": "dmm"}
    missing = [n for n in names if getattr(instr, remap[n], None) is None]
    if missing:
        raise RuntimeError(f"Missing instruments: {', '.join(missing)}")


def _run_usb_ron(instr, params: RunParams) -> dict[str, Any]:
    """D+ to HSDn RON at 10 mA. PDF rON min/max is an image."""
    _require(instr, "PSU", "DMM", "AWG")
    from generator_setup import setup_dc, stop_output
    from psu_setup import OVP_ABS_MAX_V, OVP_MARGIN_V, power_off, power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    i_force = float(cfg.get("ron_force_a") or 0.01)
    settle = float(cfg.get("dmm_settle_s") or 0.2)
    n = int(cfg.get("dmm_readings") or 3)
    if i_force <= 0:
        raise RuntimeError("ron_force_a must be > 0")
    subs = [
        (
            "USB RON HSD1 (S=0)",
            "RON_HSD1",
            [
                "OE=GND (paths on). S=GND (HSD1).",
                "CH1=V+; CH2 CC 10 mA into D+; DMM Kelvin D+ to HSD1+; HSD2 open",
            ],
            0.0,
        ),
        (
            "USB RON HSD2 (S=V+)",
            "RON_HSD2",
            [
                "OE=GND. S=V+ (HSD2).",
                "CH1=V+; CH2 CC 10 mA into D+; DMM Kelvin D+ to HSD2+; HSD1 open",
            ],
            1.0,
        ),
    ]
    worst: dict[str, Any] = {}
    worst_ohm = 0.0
    for label, param, wiring, s_frac in subs:
        _power_off(instr.psu)
        if not _pause(params, label, wiring):
            return {"summary": "aborted", "data": {"Test": "USB_RON", "Sub_results": worst}}
        rows: list[dict[str, Any]] = []
        max_ron = 0.0
        for vcc in _sweep_points(cfg, params):
            v_force = min(float(vcc) + 0.4, OVP_ABS_MAX_V - OVP_MARGIN_V)
            power_on_protected(instr.psu, 1, vcc, ilim)
            setup_dc(instr.gen, 1, 0.0)
            setup_dc(instr.gen, 2, round(float(vcc) * s_frac, 3))
            power_on_protected(instr.psu, 2, v_force, i_force)
            time.sleep(settle)
            vdrop = abs(_avg_v(instr.dmm, n))
            ron = vdrop / i_force
            rows.append(
                {
                    "VCC": vcc,
                    "S_frac": s_frac,
                    "Vdrop_V": round(vdrop, 6),
                    "I_force_A": i_force,
                    "RON_ohm": round(ron, 4),
                }
            )
            if ron > max_ron:
                max_ron = ron
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
        worst[param] = {"worst_ohm": round(max_ron, 4), "rows": rows}
        if max_ron > worst_ohm:
            worst_ohm = max_ron
    return {
        "summary": f"USB RON worst={worst_ohm} ohm @ {i_force * 1e3:.0f} mA",
        "data": {"Test": "USB_RON", "I_force_A": i_force, "Sub_results": worst},
        "measurements": [{"id": "USB_RON_ohm", "value": round(worst_ohm, 4), "unit": "ohm"}],
    }


def _run_usb_ton_toff(instr, params: RunParams) -> dict[str, Any]:
    """S-to-HSD1 delay. Banner typ tON 20 ns / tOFF 15 ns. No invented min/max."""
    _require(instr, "PSU", "AWG", "MSO")
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    cfg = _part_cfg()
    vcc = float(params.vcc or cfg.get("vcc") or 3.3)
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    t_on = t_off = float("nan")
    if not _pause(
        params,
        "USB TON/TOFF",
        [
            "OE=GND. AWG CH1 square on S. MSO CH1=S CH2=HSD1+ (or D+).",
            "PSU CH1=V+. HSD2 open.",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "USB_TON_TOFF"}}
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_square(instr.gen, 1, 100000.0, vcc, vcc / 2.0)
        scope_setup(instr.scope, 50e-9, vcc / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        t_off = measure_delay(instr.scope, "FFDelay", 1, 2) * 1e9
        t_on = measure_delay(instr.scope, "RRDelay", 1, 2) * 1e9
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
        "summary": f"USB TON={t_on:.2f} ns TOFF={t_off:.2f} ns",
        "data": {
            "Test": "USB_TON_TOFF",
            "VCC": vcc,
            "USB_TON_ns": t_on,
            "USB_TOFF_ns": t_off,
        },
        "measurements": [
            {"id": "USB_TON_ns", "value": round(t_on, 3), "unit": "ns"},
            {"id": "USB_TOFF_ns", "value": round(t_off, 3), "unit": "ns"},
        ],
    }


_FREQ_HZ = 1_000_000.0
_VPP = 1.0


def _db(vout: float, vin: float) -> float:
    den = abs(vin) if abs(vin) >= 1e-6 else 1e-6
    num = abs(vout) if abs(vout) >= 1e-9 else 1e-9
    return 20.0 * math.log10(num / den)


def _run_usb_ac_db(
    instr,
    params: RunParams,
    *,
    test_name: str,
    mid: str,
    title: str,
    wiring: list[str],
) -> dict[str, Any]:
    """1 MHz high-Z Vpp ratio. SIM CHAN2 is G11 GBW -- do not use it."""
    from ate.tests.lim.rs2323 import _is_usb

    if not _is_usb():
        raise RuntimeError(f"{test_name} is RS2227 USB DPDT. Not RS2323 SPDT.")
    _require(instr, "PSU", "AWG", "MSO")
    from generator_setup import setup_sine, stop_output
    from psu_setup import power_off, power_on_protected

    cfg = _part_cfg()
    vcc = float(params.vcc or cfg.get("vcc") or 5.0)
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    if not _pause(params, title, wiring):
        return {"summary": "aborted", "data": {"Test": test_name}}
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
    db = _db(vout, vin)
    return {
        "summary": f"{mid}={db:.1f} dB Vin={vin:.4g} Vout={vout:.4g} sim={sim}",
        "data": {
            "Test": test_name,
            "VCC": vcc,
            "freq_hz": _FREQ_HZ,
            "Vin_Vpp": vin,
            "Vout_Vpp": vout,
            mid: db,
            "sim_couple": sim,
        },
        "measurements": [{"id": mid, "value": round(db, 2), "unit": "dB"}],
    }


def _run_usb_iso(instr, params: RunParams) -> dict[str, Any]:
    return _run_usb_ac_db(
        instr,
        params,
        test_name="USB_ISO",
        mid="USB_ISO_dB",
        title="USB ISO 1 MHz",
        wiring=[
            "OE=V+ (all paths Hi-Z).",
            "AWG CH1 1 MHz 1 Vpp on D+; MSO CH1=D+ CH2=HSD1+.",
            "High-Z probes. Not 50 ohm RF. Not 550 MHz BW.",
        ],
    )


def _run_usb_xtalk(instr, params: RunParams) -> dict[str, Any]:
    return _run_usb_ac_db(
        instr,
        params,
        test_name="USB_XTalk",
        mid="USB_XTALK_dB",
        title="USB XTalk 1 MHz",
        wiring=[
            "OE=GND. S=GND (HSD1 ON, HSD2 OFF).",
            "AWG CH1 1 MHz 1 Vpp on D+; MSO CH1=HSD1+ CH2=HSD2+.",
            "High-Z probes. Not 50 ohm RF. Not 550 MHz BW.",
        ],
    )


register(
    TestSpec(
        id="usb_ron",
        label="RS2227 USB RON (10 mA)",
        required_instruments=frozenset({"PSU", "DMM", "AWG"}),
        fixture_mode=_FIXTURE,
        lab_sheet="RON",
        run=_run_usb_ron,
        dual_channel=False,
        notes=_NOTE,
    )
)
register(
    TestSpec(
        id="usb_ton_toff",
        label="RS2227 USB TON/TOFF",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode=_FIXTURE,
        lab_sheet="TonToff",
        run=_run_usb_ton_toff,
        dual_channel=False,
        notes=_NOTE,
    )
)
register(
    TestSpec(
        id="usb_iso",
        label="RS2227 USB Isolation (1 MHz)",
        required_instruments=frozenset({"PSU", "AWG", "MSO"}),
        fixture_mode=_FIXTURE,
        lab_sheet="USBISO",
        run=_run_usb_iso,
        dual_channel=False,
        notes="1 MHz high-Z USB_ISO_dB. Not 50 ohm RF. Not 550 MHz BW. SIM not G11 CHAN2.",
        short_tag="USBISO",
        fixed_steps=[
            {"id": "wire", "label": "Wire OE Hi-Z + MSO then Continue", "phase": "operator"},
            {"id": "measure", "label": "Measure 1 MHz USB isolation", "phase": "measure"},
        ],
    )
)
register(
    TestSpec(
        id="usb_xtalk",
        label="RS2227 USB Crosstalk (1 MHz)",
        required_instruments=frozenset({"PSU", "AWG", "MSO"}),
        fixture_mode=_FIXTURE,
        lab_sheet="USBXTalk",
        run=_run_usb_xtalk,
        dual_channel=False,
        notes="1 MHz high-Z USB_XTALK_dB. Not 50 ohm RF. Not 550 MHz BW. SIM not G11 CHAN2.",
        short_tag="USBXT",
        fixed_steps=[
            {"id": "wire", "label": "Wire HSD1/HSD2 + MSO then Continue", "phase": "operator"},
            {"id": "measure", "label": "Measure 1 MHz USB crosstalk", "phase": "measure"},
        ],
    )
)
