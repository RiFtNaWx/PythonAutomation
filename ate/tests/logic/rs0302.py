"""RS0302 I2C / SMBus bidirectional translator (not RS0204 CMOS).

VREF1/VREF2 + EN. Open-drain SDA/SCL. Do not copy RS0204 vih/voh/tpd.
RON platform force is 10 mA (DMM/PSU class). Datasheet also lists 64 mA --
do not stamp that as this body's min/max.
"""
from __future__ import annotations

import time
from typing import Any

import yaml

from ate.core.paths import PARTS_DIR
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_FIXTURE = "LOGIC"
_PART = "rs0302"
_NOTE = "I2C bidirectional switch. Not RS0204 dual-rail CMOS."


def _part_cfg(params: RunParams) -> dict[str, Any]:
    key = str(getattr(params, "part", None) or _PART).strip().lower()
    path = PARTS_DIR / f"{key}.yaml"
    if not path.is_file():
        path = PARTS_DIR / f"{_PART}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _rails(params: RunParams) -> tuple[float, float, float]:
    cfg = _part_cfg(params)
    vref1 = float(params.vcc or cfg.get("vcc") or 1.8)
    raw_b = getattr(params, "vccb", None)
    vref2 = float(raw_b) if raw_b not in (None, "") else float(cfg.get("vccb") or 3.3)
    if vref1 > vref2:
        raise RuntimeError(f"RS0302: VREF1 {vref1} V must be < VREF2 {vref2} V")
    ilim = float(params.current_limit_a or cfg.get("current_limit") or 0.05)
    return vref1, vref2, ilim


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _power_down(instr) -> None:
    from generator_setup import stop_output
    from psu_setup import power_off

    try:
        stop_output(instr.gen)
    except Exception:
        pass
    try:
        power_off(instr.psu)
    except Exception:
        pass


def _avg_ua(dmm, n: int = 3) -> float:
    from dmm_setup import dmm_read, dmm_setup_current

    dmm_setup_current(dmm)
    vals = [float(dmm_read(dmm)) for _ in range(max(1, n))]
    return (sum(vals) / len(vals)) * 1e6


def _avg_v(dmm, n: int = 3) -> float:
    from dmm_setup import dmm_read, dmm_setup_voltage

    dmm_setup_voltage(dmm)
    vals = [float(dmm_read(dmm)) for _ in range(max(1, n))]
    return sum(vals) / len(vals)


def _run_ii(instr, params: RunParams) -> dict[str, Any]:
    """II: EN=0, VI=5 V on SCL1, DMM DCI. Extract max 5 uA."""
    if getattr(instr, "psu", None) is None or getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: PSU, DMM")
    from generator_setup import setup_dc, stop_output
    from psu_setup import power_off, power_on_protected

    cfg = _part_cfg(params)
    ilim = float(params.current_limit_a or cfg.get("current_limit") or 0.05)
    settle = float(cfg.get("dmm_settle_s") or cfg.get("timing", {}).get("settle_s") or 0.3)
    if not _pause(
        params,
        "RS0302 II: EN=GND (AWG CH1 DC 0). DMM DCI in series PSU CH1=5 V -> SCL1. "
        "VREF1/VREF2 off. Then Continue",
    ):
        return {"summary": "aborted", "data": {}}
    try:
        power_off(instr.psu)
        if getattr(instr, "gen", None) is not None:
            setup_dc(instr.gen, 1, 0.0)
        power_on_protected(instr.psu, 1, 5.0, ilim)
        time.sleep(settle)
        ua = _avg_ua(instr.dmm)
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        _power_down(instr)
    return {
        "summary": f"II={ua:.4f} uA EN=0 VI=5 V",
        "data": {"II_uA": ua, "EN_V": 0.0, "VI_V": 5.0},
        "measurements": [{"id": "II_uA", "value": round(ua, 4), "unit": "uA"}],
    }


def _run_ron(instr, params: RunParams) -> dict[str, Any]:
    """SCL1-SCL2 RON at 10 mA. Datasheet 64 mA is leftover-honest (DMM 10 mA class)."""
    if getattr(instr, "psu", None) is None or getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: PSU, DMM")
    from generator_setup import setup_dc, stop_output
    from psu_setup import OVP_ABS_MAX_V, OVP_MARGIN_V, power_off, power_on_protected

    cfg = _part_cfg(params)
    vref1, vref2, ilim = _rails(params)
    i_force = float(cfg.get("ron_force_a") or 0.01)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    settle = float(cfg.get("dmm_settle_s") or 0.3)
    if i_force <= 0:
        raise RuntimeError("ron_force_a must be > 0")
    if not _pause(
        params,
        "RS0302 RON: PSU CH1=VREF1 CH2=VREF2. AWG CH1=EN high. "
        "CH3 CC 10 mA into SCL1. DMM VDC Kelvin SCL1-SCL2. Then Continue",
    ):
        return {"summary": "aborted", "data": {}}
    v_force = min(float(vref2) + 0.4, OVP_ABS_MAX_V - OVP_MARGIN_V)
    try:
        power_off(instr.psu)
        power_on_protected(instr.psu, 1, vref1, ilim)
        power_on_protected(instr.psu, 2, vref2, ilim)
        if getattr(instr, "gen", None) is not None:
            setup_dc(instr.gen, 1, vref2)
        power_on_protected(instr.psu, 3, v_force, i_force)
        time.sleep(settle)
        vdrop = abs(_avg_v(instr.dmm))
        ron = vdrop / i_force
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        _power_down(instr)
    return {
        "summary": f"RON={ron:.4f} ohm @ {i_force * 1e3:.0f} mA (not 64 mA PDF)",
        "data": {
            "VREF1": vref1,
            "VREF2": vref2,
            "I_force_A": i_force,
            "Vdrop_V": round(vdrop, 6),
            "RON_ohm": round(ron, 4),
        },
        "measurements": [{"id": "RON_ohm", "value": round(ron, 4), "unit": "ohm"}],
    }


def _run_cioff(instr, params: RunParams) -> dict[str, Any]:
    """Ci(off) SCL1-GND, EN=0, VREF off. Extract typ 4 max 6 pF."""
    if getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: DMM")
    from dmm_setup import dmm_read, dmm_setup_cap
    from psu_setup import power_off

    if not _pause(
        params,
        "RS0302 Ci(off): EN=GND. VREF1/VREF2 off. DMM CAP SCL1 to GND. Then Continue",
    ):
        return {"summary": "aborted", "data": {}}
    try:
        power_off(instr.psu)
        dmm_setup_cap(instr.dmm)
        time.sleep(0.3)
        pf = float(dmm_read(instr.dmm)) * 1e12
    finally:
        _power_down(instr)
    return {
        "summary": f"Ci(off)={pf:.3f} pF",
        "data": {"CIOFF_pF": round(pf, 3)},
        "measurements": [{"id": "CIOFF_pF", "value": round(pf, 3), "unit": "pF"}],
    }


register(
    TestSpec(
        id="i2c_ii",
        label="RS0302 II (EN off)",
        required_instruments=frozenset({"PSU", "DMM", "AWG"}),
        fixture_mode=_FIXTURE,
        lab_sheet="II",
        run=_run_ii,
        dual_channel=False,
        notes=_NOTE,
    )
)
register(
    TestSpec(
        id="i2c_ron",
        label="RS0302 RON (10 mA)",
        required_instruments=frozenset({"PSU", "DMM", "AWG"}),
        fixture_mode=_FIXTURE,
        lab_sheet="RON",
        run=_run_ron,
        dual_channel=False,
        notes=_NOTE,
    )
)
register(
    TestSpec(
        id="i2c_cioff",
        label="RS0302 Ci(off)",
        required_instruments=frozenset({"PSU", "DMM"}),
        fixture_mode=_FIXTURE,
        lab_sheet="Cioff",
        run=_run_cioff,
        dual_channel=False,
        notes=_NOTE,
    )
)
