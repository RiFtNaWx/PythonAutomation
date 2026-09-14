"""Eugene RS1G07 CPD / CIN -- VCC + AWG square, DMM current. No input().

RS0204 keeps pin-Cio Cpd; this body is for single-rail Logic (RS1G07).
Golden used stdin prompts; Continue is pause_hook.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_LOGIC = "LOGIC"
_MYT = timezone(timedelta(hours=8))
_NOTE = "Eugene RS1G07: PSU CH1=VCC, AWG CH1 square, DMM current -> C=I/(V*f). Not RS0204 pin Cio."


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _require(instr, *names: str) -> None:
    remap = {"MSO": "scope", "PSU": "psu", "AWG": "gen", "DMM": "dmm"}
    missing = [n for n in names if getattr(instr, remap[n], None) is None]
    if missing:
        raise RuntimeError(f"Missing instruments: {', '.join(missing)}")


def _ilim(params: RunParams) -> float:
    return float(getattr(params, "current_limit_a", None) or 0.10)


def _shot(instr, folder: str, tag: str, params: RunParams) -> str | None:
    if getattr(instr, "scope", None) is None:
        return None
    try:
        from ate.drivers.mso5072 import capture_jpeg
        from ate.reporting.lab_report import ensure_screenshot_dir

        dut = int(getattr(params, "unit_index", 1) or 1)
        dest = ensure_screenshot_dir(folder, dut)
        ts = datetime.now(_MYT).strftime("%Y-%m-%d_%H%M%S")
        path = dest / f"{folder}_DUT{dut}_{tag}_{ts}.jpg"
        return capture_jpeg(instr.scope, path)
    except Exception:
        return None


def _cap_pf(i_ua: float, vcc: float, freq: float) -> float | None:
    if not vcc or not freq:
        return None
    return (float(i_ua) * 1e-6) / (float(vcc) * float(freq)) * 1e12


def _power_awg(instr, vcc: float, freq: float, ilim: float) -> None:
    from generator_setup import setup_square
    from psu_setup import power_on_protected

    power_on_protected(instr.psu, 1, vcc, ilim, ovp=min(vcc + 0.2, 6.0))
    setup_square(instr.gen, 1, freq, vcc, vcc / 2.0)


def run_cpd(instr, params: RunParams) -> dict[str, Any]:
    """VCC corners 1.8/2.5/3.3/5.0 V, 10 MHz square, DMM current in uA."""
    _require(instr, "PSU", "AWG", "DMM")
    from dmm_setup import dmm_setup_current

    if not _pause(
        params,
        "CPD: PSU CH1=VCC, AWG CH1=Input A (square), DMM current. Continue.",
    ):
        return {"summary": "aborted", "data": {}}
    ilim = _ilim(params)
    vccs = [1.8, 2.5, 3.3, 5.0]
    rows: list[dict[str, Any]] = []
    shots: list[str] = []
    try:
        for vcc in vccs:
            _power_awg(instr, vcc, 10e6, ilim)
            time.sleep(0.5)
            icc_a = float(dmm_setup_current(instr.dmm))
            ua = icc_a * 1e6
            pf = _cap_pf(ua, vcc, 10e6)
            rows.append({"VCC": vcc, "I_uA": ua, "freq_hz": 10e6, "CPD_pF": pf})
            shot = _shot(instr, "CPD", f"{vcc}V", params)
            if shot:
                shots.append(shot)
    finally:
        try:
            from generator_setup import stop_output

            stop_output(instr.gen)
        except Exception:
            pass
    last = rows[-1] if rows else {}
    pf = last.get("CPD_pF")
    return {
        "summary": f"CPD n={len(rows)} last={pf} pF @ {last.get('VCC')} V",
        "data": {"rows": rows, "screenshots": shots},
        "measurements": [
            {"id": "CPD_pF", "value": pf, "unit": "pF"}
        ]
        if last and pf is not None
        else [],
    }


def run_cin(instr, params: RunParams) -> dict[str, Any]:
    """CIN at 3.3 V across 1/5/10 MHz, DMM current in uA."""
    _require(instr, "PSU", "AWG", "DMM")
    from dmm_setup import dmm_setup_current

    if not _pause(
        params,
        "CIN: PSU CH1=3.3 V, AWG CH1 square 1/5/10 MHz, DMM current. Continue.",
    ):
        return {"summary": "aborted", "data": {}}
    ilim = _ilim(params)
    vcc = 3.3
    freqs = [1e6, 5e6, 10e6]
    rows: list[dict[str, Any]] = []
    shots: list[str] = []
    try:
        for freq in freqs:
            _power_awg(instr, vcc, freq, ilim)
            time.sleep(0.5)
            icc_a = float(dmm_setup_current(instr.dmm))
            ua = icc_a * 1e6
            pf = _cap_pf(ua, vcc, freq)
            rows.append({"VCC": vcc, "I_uA": ua, "freq_hz": freq, "CIN_pF": pf})
            shot = _shot(instr, "CIN", f"{int(freq / 1e6)}MHz", params)
            if shot:
                shots.append(shot)
    finally:
        try:
            from generator_setup import stop_output

            stop_output(instr.gen)
        except Exception:
            pass
    last = rows[-1] if rows else {}
    pf = last.get("CIN_pF")
    return {
        "summary": f"CIN n={len(rows)} last={pf} pF @ {last.get('freq_hz', 0) / 1e6:.0f} MHz",
        "data": {"rows": rows, "screenshots": shots},
        "measurements": [
            {"id": "CIN_pF", "value": pf, "unit": "pF"}
        ]
        if last and pf is not None
        else [],
    }


register(
    TestSpec(
        id="cin",
        label="CIN (Eugene)",
        required_instruments=frozenset({"PSU", "AWG", "DMM"}),
        fixture_mode=_LOGIC,
        lab_sheet="CIN",
        run=run_cin,
        dual_channel=False,
        notes=_NOTE,
    )
)
register(
    TestSpec(
        id="cpd",
        label="CPD (Eugene)",
        required_instruments=frozenset({"PSU", "AWG", "DMM"}),
        fixture_mode=_LOGIC,
        lab_sheet="CPD",
        run=run_cpd,
        dual_channel=False,
        notes=_NOTE,
    )
)
