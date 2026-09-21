"""OE/EN enable-disable time.

RS1G126 OE active-high. RS1G125 /OE active-low. 3-state Y + pull R.
RS29511 is an I2C hot-swap buffer: EN -> READY (tIDLE / tDISABLE).
Not Ariff/Soo wrap. Not RS0204 tsu/th. Same-edge RRDelay/FFDelay only.
"""
from __future__ import annotations

from typing import Any

import yaml

from ate.core.paths import PARTS_DIR
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_LOGIC = "LOGIC"
_HOTSWAP = frozenset({"rs29511"})


def _part_key(params: RunParams) -> str:
    return str(getattr(params, "part", "") or "").strip().lower()


def _part_cfg(params: RunParams) -> dict[str, Any]:
    pk = _part_key(params)
    path = PARTS_DIR / f"{pk}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _oe_active_low(params: RunParams) -> bool:
    cfg = _part_cfg(params)
    raw = cfg.get("oe_active")
    if raw is None:
        pm = cfg.get("product_model")
        if isinstance(pm, dict):
            oe = pm.get("oe")
            if isinstance(oe, dict):
                raw = oe.get("active")
    return str(raw or "high").strip().lower() == "low"


def _hotswap(params: RunParams) -> bool:
    return _part_key(params) in _HOTSWAP


def _measure_ns(instr, params: RunParams, *, item: str, freq_hz: float, timebase_s: float) -> float:
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    ns = float("nan")
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_square(instr.gen, 1, freq_hz, vcc, vcc / 2.0)
        scope_setup(instr.scope, timebase_s, vcc / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        ns = abs(measure_delay(instr.scope, item, 1, 2)) * 1e9
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
    return ns


def _run_en_ready(instr, params: RunParams, *, enable: bool) -> dict[str, Any]:
    """RS29511: EN to READY. tIDLE ~95-150 us enable; tDISABLE ~30-50 ns disable."""
    hook = params.pause_hook
    wire = (
        "RS29511 I2C hot-swap: PSU CH1=VCC; 10k pull-up READY/SDAIN/SCLIN/"
        "SDAOUT/SCLOUT to VCC; AWG CH1=EN square; MSO CH1=EN CH2=READY. "
        "Not 3-state Y. Continue."
    )
    if hook is not None and not hook(wire):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    vcc = float(params.vcc or 5.0)
    item = "RRDelay" if enable else "FFDelay"
    # Enable: 500 Hz so EN-high window (~1 ms) > tIDLE max 150 us.
    # Disable: 10 kHz; tDISABLE is tens of ns.
    freq = 500.0 if enable else 10000.0
    tb = 50e-6 if enable else 1e-6
    ns = _measure_ns(instr, params, item=item, freq_hz=freq, timebase_s=tb)
    mid = "TEN_ns" if enable else "TDIS_ns"
    name = "TEN" if enable else "TDIS"
    return {
        "summary": f"{name}={ns:.2f} ns EN->READY {item}",
        "data": {
            "VCC": vcc,
            "hotswap": True,
            "item": item,
            mid: ns,
        },
        "measurements": [{"id": mid, "value": round(ns, 3), "unit": "ns"}],
    }


def _run_oe(instr, params: RunParams, *, enable: bool) -> dict[str, Any]:
    if _hotswap(params):
        return _run_en_ready(instr, params, enable=enable)
    hook = params.pause_hook
    low = _oe_active_low(params)
    if low:
        wire = (
            "3-state /OE (active-low): PSU CH1=VCC; AWG CH1=A DC 0 V; AWG CH2=/OE square; "
            "MSO CH1=/OE CH2=Y; 10k pull-up Y to VCC. Continue."
        )
    else:
        wire = (
            "3-state OE (active-high): PSU CH1=VCC; AWG CH1=A DC VCC; AWG CH2=OE square; "
            "MSO CH1=OE CH2=Y; 10k pull-down Y to GND. Continue."
        )
    if hook is not None and not hook(wire):
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
    # Active-high: A high, Y rises on OE rise (RR) and falls on OE fall (FF).
    # Active-low: A low, Y falls on /OE fall (FF) and rises on /OE rise (RR).
    if enable:
        item = "FFDelay" if low else "RRDelay"
    else:
        item = "RRDelay" if low else "FFDelay"
    a_dc = 0.0 if low else vcc
    ns = float("nan")
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_dc(instr.gen, 1, a_dc)
        setup_square(instr.gen, 2, 10000.0, vcc, vcc / 2.0)
        scope_setup(instr.scope, 1e-6, vcc / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        ns = abs(measure_delay(instr.scope, item, 1, 2)) * 1e9
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass
    mid = "TEN_ns" if enable else "TDIS_ns"
    name = "TEN" if enable else "TDIS"
    return {
        "summary": f"{name}={ns:.2f} ns oe_low={low} {item}",
        "data": {
            "VCC": vcc,
            "hotswap": False,
            "oe_active_low": low,
            "item": item,
            mid: ns,
        },
        "measurements": [{"id": mid, "value": round(ns, 3), "unit": "ns"}],
    }


def run_ten(instr, params: RunParams) -> dict[str, Any]:
    return _run_oe(instr, params, enable=True)


def run_tdis(instr, params: RunParams) -> dict[str, Any]:
    return _run_oe(instr, params, enable=False)


register(
    TestSpec(
        id="ten",
        label="Output Enable Time (TEN)",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode=_LOGIC,
        lab_sheet="TEN",
        run=run_ten,
        dual_channel=False,
        notes="3-state OE->Y or RS29511 EN->READY tIDLE. Not Ariff wrap.",
        short_tag="TEN",
    )
)
register(
    TestSpec(
        id="tdis",
        label="Output Disable Time (TDIS)",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode=_LOGIC,
        lab_sheet="TDIS",
        run=run_tdis,
        dual_channel=False,
        notes="3-state OE->Y or RS29511 EN->READY tDISABLE. Not Ariff wrap.",
        short_tag="TDIS",
    )
)
