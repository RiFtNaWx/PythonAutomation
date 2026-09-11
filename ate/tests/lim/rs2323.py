"""Lim RS2323 current TestSpecs (A10).

Platform sweeps using this repo's PSU/DMM helpers + part YAML.
Wiring re-jumps use RunParams.pause_hook (operator Continue) -- never stdin prompts.
Do not import LabAutomation-1 Lim.* .
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from ate.core.paths import PARTS_DIR
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_FIXTURE = "LIM_RS2323"
_PART = "rs2323"


def _active_part() -> str:
    try:
        from ate.core.database import get_context

        pk = str(get_context().part_key or "").strip()
        if pk:
            return pk
    except Exception:
        pass
    return _PART


def _part_cfg() -> dict[str, Any]:
    path = PARTS_DIR / f"{_active_part()}.yaml"
    if not path.is_file():
        path = PARTS_DIR / f"{_PART}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _require(instr) -> None:
    if getattr(instr, "psu", None) is None or getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: PSU, DMM")


def _pause(params: RunParams, title: str, checklist: list[str]) -> bool:
    hook = params.pause_hook
    if hook is None:
        # Headless / no gate: proceed (checks never hang)
        return True
    # pause_hook signature in runner is (title) -> bool; checklist shown via title
    detail = title + " | " + " ; ".join(checklist[:4])
    return bool(hook(detail))


def _sweep_points(cfg: dict[str, Any]) -> list[float]:
    raw = cfg.get("vcc_sweep") or [1.8, 3.3, 5.0]
    return [float(x) for x in raw]


def _avg_ua(dmm, n: int) -> float:
    from dmm_setup import dmm_read, dmm_setup_current

    dmm_setup_current(dmm)
    vals = [float(dmm_read(dmm)) for _ in range(max(1, n))]
    return (sum(vals) / len(vals)) * 1e6


def _power_off(psu) -> None:
    from psu_setup import power_off

    try:
        power_off(psu)
    except Exception:
        pass


def _run_sweep(
    *,
    instr,
    params: RunParams,
    label: str,
    parameter: str,
    program: Callable[[float], None],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    from psu_setup import power_off

    settle = float(cfg.get("dmm_settle_s") or 0.2)
    n = int(cfg.get("dmm_readings") or 3)
    worst_ua, worst_vcc = 0.0, None
    rows: list[dict[str, Any]] = []
    for vcc in _sweep_points(cfg):
        program(vcc)
        time.sleep(settle)
        i_ua = _avg_ua(instr.dmm, n)
        rows.append({"VCC": vcc, "I_uA": round(i_ua, 4), "parameter": parameter})
        if abs(i_ua) > abs(worst_ua):
            worst_ua, worst_vcc = i_ua, vcc
    try:
        power_off(instr.psu)
    except Exception:
        pass
    return {
        "parameter": parameter,
        "label": label,
        "worst_uA": round(worst_ua, 4),
        "at_vcc": worst_vcc,
        "rows": rows,
    }


def _run_iplus(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    subs = [
        ("I+ (VIN = GND)", "Iplus_VIN_LOW", ["Set IN1 jumper to GND."]),
        ("I+ (VIN = V+)", "Iplus_VIN_HIGH", ["Set IN1 jumper to V+."]),
    ]
    worst: dict[str, Any] = {}
    for label, param, wiring in subs:
        _power_off(instr.psu)
        if not _pause(params, label, ["PSU CH1 --> DMM (A) --> V+", *wiring]):
            return {"summary": "aborted", "data": {"Test": "I+", "Sub_results": worst}}

        def program(vcc: float, _ilim=ilim) -> None:
            power_on_protected(instr.psu, 1, vcc, _ilim)

        worst[param] = _run_sweep(
            instr=instr, params=params, label=label, parameter=param, program=program, cfg=cfg
        )
    last = list(worst.values())[-1] if worst else {}
    vals = [
        float(s["worst_uA"])
        for s in worst.values()
        if isinstance(s, dict) and s.get("worst_uA") is not None
    ]
    mx = max(vals, key=lambda x: abs(x)) if vals else last.get("worst_uA")
    return {
        "summary": f"I+ subs={len(worst)} worst={mx} uA",
        "data": {"Test": "I+", "Sub_results": worst},
        "measurements": [{"id": "IPLUS_uA", "value": mx, "unit": "uA"}] if mx is not None else [],
    }


def _run_leakage_off(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or 0.1)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    blow = float(cfg.get("bias_low_v") or 0.3)
    subs = [
        (
            "INO(OFF), NO=0.3V / COM=V+/2",
            "INO_OFF_pin03",
            ["IN1 -> GND (NO OFF).", "CH2(0.3V)->DMM->NO1; CH3(V+/2)->COM1"],
        ),
        (
            "INC(OFF), NC=0.3V / COM=V+/2",
            "INC_OFF_pin03",
            ["IN1 -> V+ (NC OFF).", "CH2(0.3V)->DMM->NC1; CH3(V+/2)->COM1"],
        ),
    ]
    worst: dict[str, Any] = {}
    for label, param, wiring in subs:
        _power_off(instr.psu)
        if not _pause(params, label, wiring):
            return {"summary": "aborted", "data": {"Test": "Leakage_OFF", "Sub_results": worst}}

        def program(vcc: float, _ilim=ilim, _bilim=bilim, _blow=blow) -> None:
            power_on_protected(instr.psu, 1, vcc, _ilim)
            power_on_protected(instr.psu, 2, _blow, _bilim)
            power_on_protected(instr.psu, 3, round(vcc / 2, 3), _bilim)

        worst[param] = _run_sweep(
            instr=instr, params=params, label=label, parameter=param, program=program, cfg=cfg
        )
    last = list(worst.values())[-1] if worst else {}
    return {
        "summary": f"LeakOFF subs={len(worst)} worst={last.get('worst_uA')} uA",
        "data": {"Test": "Leakage_OFF", "Sub_results": worst},
    }


def _run_leakage_on(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or 0.1)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    blow = float(cfg.get("bias_low_v") or 0.3)
    subs = [
        (
            "INO(ON), NO=0.3V",
            "INO_ON_03",
            ["IN1 -> V+ (NO ON).", "CH2(0.3V)->DMM->NO1; leave COM/NC OPEN"],
            2,
            lambda vcc: blow,
        ),
        (
            "INC(ON), NC=0.3V",
            "INC_ON_03",
            ["IN1 -> GND (NC ON).", "CH2(0.3V)->DMM->NC1; leave COM/NO OPEN"],
            2,
            lambda vcc: blow,
        ),
        (
            "ICOM(ON), COM=V+/2",
            "ICOM_ON_VH",
            ["IN1 -> V+.", "CH3(V+/2)->DMM->COM1; leave NO/NC OPEN"],
            3,
            lambda vcc: round(vcc / 2, 3),
        ),
    ]
    worst: dict[str, Any] = {}
    for label, param, wiring, bias_ch, bias_fn in subs:
        _power_off(instr.psu)
        if not _pause(params, label, wiring):
            return {"summary": "aborted", "data": {"Test": "Leakage_ON", "Sub_results": worst}}

        def program(
            vcc: float,
            _ch=bias_ch,
            _fn=bias_fn,
            _ilim=ilim,
            _bilim=bilim,
        ) -> None:
            power_on_protected(instr.psu, 1, vcc, _ilim)
            power_on_protected(instr.psu, _ch, _fn(vcc), _bilim)

        worst[param] = _run_sweep(
            instr=instr, params=params, label=label, parameter=param, program=program, cfg=cfg
        )
    last = list(worst.values())[-1] if worst else {}
    return {
        "summary": f"LeakON subs={len(worst)} worst={last.get('worst_uA')} uA",
        "data": {"Test": "Leakage_ON", "Sub_results": worst},
    }


def _run_input_leakage(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or 0.1)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    subs = [
        (
            "IIN (VIN = V+)",
            "IIN_HIGH",
            ["CH1 -> V+ pin.", "CH2(=V+)->DMM->IN1; NO/NC/COM open"],
            True,
        ),
        (
            "IIN (VIN = 0)",
            "IIN_LOW",
            ["CH1 -> V+ pin.", "GND->DMM->IN1; NO/NC/COM open"],
            False,
        ),
    ]
    worst: dict[str, Any] = {}
    for label, param, wiring, vin_high in subs:
        _power_off(instr.psu)
        if not _pause(params, label, wiring):
            return {"summary": "aborted", "data": {"Test": "IIN", "Sub_results": worst}}

        def program(vcc: float, _high=vin_high, _ilim=ilim, _bilim=bilim) -> None:
            power_on_protected(instr.psu, 1, vcc, _ilim)
            if _high:
                power_on_protected(instr.psu, 2, vcc, _bilim)

        worst[param] = _run_sweep(
            instr=instr, params=params, label=label, parameter=param, program=program, cfg=cfg
        )
    last = list(worst.values())[-1] if worst else {}
    return {
        "summary": f"IIN subs={len(worst)} worst={last.get('worst_uA')} uA",
        "data": {"Test": "IIN", "Sub_results": worst},
    }


def _reg(test_id: str, label: str, lab_sheet: str, run, steps: list[dict[str, Any]]) -> None:
    register(
        TestSpec(
            id=test_id,
            label=label,
            required_instruments=frozenset({"PSU", "DMM"}),
            fixture_mode=_FIXTURE,
            lab_sheet=lab_sheet,
            run=run,
            dual_channel=False,
            fixed_steps=steps,
            notes="Lim RS2323 (A10) -- Continue gates for wiring; no Lim.* import",
            short_tag=lab_sheet,
        )
    )


_reg(
    "iplus",
    "I+ Quiescent Supply Current",
    "Iplus",
    _run_iplus,
    [
        {"id": "wire_gnd", "label": "Wire IN1=GND then Continue", "phase": "operator"},
        {"id": "sweep_gnd", "label": "Sweep I+ (VIN=GND)", "phase": "measure"},
        {"id": "wire_vplus", "label": "Wire IN1=V+ then Continue", "phase": "operator"},
        {"id": "sweep_vplus", "label": "Sweep I+ (VIN=V+)", "phase": "measure"},
    ],
)
_reg(
    "leakage_off",
    "OFF-State Leakage",
    "LeakageOff",
    _run_leakage_off,
    [
        {"id": "wire", "label": "Rewire OFF leakage sub-condition", "phase": "operator"},
        {"id": "sweep", "label": "Sweep OFF leakage", "phase": "measure"},
    ],
)
_reg(
    "leakage_on",
    "ON-State Leakage",
    "LeakageOn",
    _run_leakage_on,
    [
        {"id": "wire", "label": "Rewire ON leakage sub-condition", "phase": "operator"},
        {"id": "sweep", "label": "Sweep ON leakage", "phase": "measure"},
    ],
)
_reg(
    "input_leakage",
    "Input Leakage (IIN)",
    "InputLeakage",
    _run_input_leakage,
    [
        {"id": "wire", "label": "Rewire IIN sub-condition", "phase": "operator"},
        {"id": "sweep", "label": "Sweep IIN", "phase": "measure"},
    ],
)
