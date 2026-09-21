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


def _is_usb() -> bool:
    return _active_part() == "rs2227"


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


def _sweep_points(cfg: dict[str, Any], params: RunParams | None = None) -> list[float]:
    if params is not None:
        start = float(getattr(params, "vcc_start", 0.0) or 0.0)
        stop = float(getattr(params, "vcc_stop", 5.0) or 5.0)
        step = float(getattr(params, "vcc_step", 0.5) or 0.5)
        custom = abs(start) > 1e-9 or abs(stop - 5.0) > 1e-9 or abs(step - 0.5) > 1e-9
        if custom:
            return params.resolved_vcc_sweep()
    raw = cfg.get("vcc_sweep") or [1.8, 3.3, 5.0]
    return [float(x) for x in raw]


def _avg_ua(dmm, n: int) -> float:
    from dmm_setup import dmm_read, dmm_setup_current

    dmm_setup_current(dmm)
    vals = [float(dmm_read(dmm)) for _ in range(max(1, n))]
    return (sum(vals) / len(vals)) * 1e6


def _avg_v(dmm, n: int) -> float:
    from dmm_setup import dmm_read, dmm_setup_voltage

    dmm_setup_voltage(dmm)
    vals = [float(dmm_read(dmm)) for _ in range(max(1, n))]
    return sum(vals) / len(vals)


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
    for vcc in _sweep_points(cfg, params):
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
    if _is_usb():
        subs = [
            (
                "I+ (S=GND, OE=GND)",
                "Iplus_S_LOW",
                ["OE=GND (paths on). S=GND (HSD1)."],
            ),
            (
                "I+ (S=V+, OE=GND)",
                "Iplus_S_HIGH",
                ["OE=GND (paths on). S=V+ (HSD2)."],
            ),
        ]
    else:
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
    usb = _is_usb()
    if usb:
        subs = [
            (
                "IOZ D+ (OE=V+, Hi-Z)",
                "IOZ_DP",
                [
                    "OE=V+ (all off). S=GND.",
                    "CH2(0.3V)->DMM->D+; HSD1/HSD2/D- open",
                ],
            ),
            (
                "IOZ D- (OE=V+, Hi-Z)",
                "IOZ_DM",
                [
                    "OE=V+ (all off). S=GND.",
                    "CH2(0.3V)->DMM->D-; HSD1/HSD2/D+ open",
                ],
            ),
        ]
    else:
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

        def program(vcc: float, _ilim=ilim, _bilim=bilim, _blow=blow, _usb=usb) -> None:
            power_on_protected(instr.psu, 1, vcc, _ilim)
            power_on_protected(instr.psu, 2, _blow, _bilim)
            if not _usb:
                power_on_protected(instr.psu, 3, round(vcc / 2, 3), _bilim)

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
        "summary": f"LeakOFF subs={len(worst)} worst={mx} uA",
        "data": {"Test": "Leakage_OFF", "Sub_results": worst},
        "measurements": [{"id": "IOZ_uA", "value": mx, "unit": "uA"}] if mx is not None else [],
    }


def _run_leakage_on(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or 0.1)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    blow = float(cfg.get("bias_low_v") or 0.3)
    if _is_usb():
        subs = [
            (
                "ION D+ (HSD1 ON)",
                "ION_DP_HSD1",
                [
                    "OE=GND. S=GND (HSD1 ON).",
                    "CH2(0.3V)->DMM->D+; HSD2/D- open",
                ],
                2,
                lambda vcc: blow,
            ),
            (
                "ION HSD2+ (HSD1 ON, HSD2 OFF)",
                "ION_HSD2_OFF",
                [
                    "OE=GND. S=GND (HSD1 ON / HSD2 OFF).",
                    "CH2(0.3V)->DMM->HSD2+; D+/D-/HSD1 open",
                ],
                2,
                lambda vcc: blow,
            ),
        ]
    else:
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
    vals = [
        float(s["worst_uA"])
        for s in worst.values()
        if isinstance(s, dict) and s.get("worst_uA") is not None
    ]
    mx = max(vals, key=lambda x: abs(x)) if vals else last.get("worst_uA")
    return {
        "summary": f"LeakON subs={len(worst)} worst={mx} uA",
        "data": {"Test": "Leakage_ON", "Sub_results": worst},
        "measurements": [{"id": "ION_uA", "value": mx, "unit": "uA"}] if mx is not None else [],
    }


def _run_input_leakage(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or 0.1)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    if _is_usb():
        subs = [
            (
                "IIN S = V+",
                "IIN_S_HIGH",
                ["CH1 -> V+.", "CH2(=V+)->DMM->S; OE=GND; D+/HSD open"],
                True,
            ),
            (
                "IIN S = 0",
                "IIN_S_LOW",
                ["CH1 -> V+.", "GND->DMM->S; OE=GND; D+/HSD open"],
                False,
            ),
        ]
    else:
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
    vals = [
        float(s["worst_uA"])
        for s in worst.values()
        if isinstance(s, dict) and s.get("worst_uA") is not None
    ]
    mx = max(vals, key=lambda x: abs(x)) if vals else last.get("worst_uA")
    return {
        "summary": f"IIN subs={len(worst)} worst={mx} uA",
        "data": {"Test": "IIN", "Sub_results": worst},
        "measurements": [{"id": "IIN_uA", "value": mx, "unit": "uA"}] if mx is not None else [],
    }


def _run_ron(instr, params: RunParams) -> dict[str, Any]:
    """ON-resistance: DMM Vdrop / programmed I_force. No ohms SCPI (not in dmm_setup).

    Lab book: V+ supply, Icom = 10 mA, sweep VNO/VNC 0 to V+.
    CH1 = V+. CH3 = VCOM bias on NO/NC. CH2 = CC force into COM (Vset > VCOM).
    Datasheet rON min/max is a PDF image -- limits stay typ 0.6.
    """
    _require(instr)
    from psu_setup import OVP_ABS_MAX_V, OVP_MARGIN_V, power_off, power_on_protected

    cfg = _part_cfg()
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    i_force = float(cfg.get("ron_force_a") or 0.01)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    settle = float(cfg.get("dmm_settle_s") or 0.2)
    n = int(cfg.get("dmm_readings") or 3)
    fracs = cfg.get("ron_vcom_fracs") or [0.0, 0.5, 1.0]
    if i_force <= 0:
        raise RuntimeError("ron_force_a must be > 0")
    subs = [
        (
            "RON NO (IN=V+)",
            "RON_NO",
            [
                "IN1 -> V+ (NO ON).",
                "CH3 VCOM -> NO1; CH2 CC -> COM1; DMM Kelvin COM1-NO1; NC open",
            ],
        ),
        (
            "RON NC (IN=GND)",
            "RON_NC",
            [
                "IN1 -> GND (NC ON).",
                "CH3 VCOM -> NC1; CH2 CC -> COM1; DMM Kelvin COM1-NC1; NO open",
            ],
        ),
    ]
    worst: dict[str, Any] = {}
    worst_ohm = 0.0
    for label, param, wiring in subs:
        _power_off(instr.psu)
        if not _pause(params, label, wiring):
            return {"summary": "aborted", "data": {"Test": "RON", "Sub_results": worst}}
        rows: list[dict[str, Any]] = []
        max_ron = 0.0
        for vcc in _sweep_points(cfg, params):
            v_force = min(float(vcc) + 0.4, OVP_ABS_MAX_V - OVP_MARGIN_V)
            power_on_protected(instr.psu, 1, vcc, ilim)
            for frac in fracs:
                vcom = round(float(vcc) * float(frac), 3)
                power_on_protected(instr.psu, 3, vcom, bilim)
                power_on_protected(instr.psu, 2, v_force, i_force)
                time.sleep(settle)
                vdrop = abs(_avg_v(instr.dmm, n))
                ron = vdrop / i_force
                rows.append(
                    {
                        "VCC": vcc,
                        "VCOM": vcom,
                        "Vdrop_V": round(vdrop, 6),
                        "I_force_A": i_force,
                        "RON_ohm": round(ron, 4),
                    }
                )
                if ron > max_ron:
                    max_ron = ron
        try:
            power_off(instr.psu)
        except Exception:
            pass
        worst[param] = {"worst_ohm": round(max_ron, 4), "rows": rows}
        if max_ron > worst_ohm:
            worst_ohm = max_ron
    return {
        "summary": f"RON worst={worst_ohm} ohm @ {i_force * 1e3:.0f} mA",
        "data": {"Test": "RON", "I_force_A": i_force, "Sub_results": worst},
        "measurements": [{"id": "RON_ohm", "value": round(worst_ohm, 4), "unit": "ohm"}],
    }


def _run_ton_toff(instr, params: RunParams) -> dict[str, Any]:
    """IN-to-COM delay. Same measure_delay FFDelay/RRDelay as logic tpd.

    TON = RRDelay (IN rise -> analog path ON). TOFF = FFDelay (IN fall -> OFF).
    Banner typical 50 ns -- no invented min/max.
    """
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    cfg = _part_cfg()
    vcc = float(params.vcc or cfg.get("vcc") or 5.0)
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    freq = 100000.0
    t_on = t_off = float("nan")
    if not _pause(
        params,
        "TON/TOFF",
        [
            "AWG CH1 -> IN1 (0..V+ square).",
            "MSO CH1=IN1 CH2=COM1 (or NO1 ON path); PSU CH1=V+",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "TON_TOFF"}}
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_square(instr.gen, 1, freq, vcc, vcc / 2.0)
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
        "summary": f"TON={t_on:.2f} ns TOFF={t_off:.2f} ns",
        "data": {"Test": "TON_TOFF", "VCC": vcc, "TON_ns": t_on, "TOFF_ns": t_off},
        "measurements": [
            {"id": "TON_ns", "value": round(t_on, 3), "unit": "ns"},
            {"id": "TOFF_ns", "value": round(t_off, 3), "unit": "ns"},
        ],
    }


def _run_vth(instr, params: RunParams) -> dict[str, Any]:
    """IN threshold: COM at V+/2, DMM on NO, sweep AWG DC on IN. No invented min/max."""
    _require(instr)
    if getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: AWG")
    from generator_setup import setup_dc, stop_output
    from psu_setup import power_off, power_on_protected

    cfg = _part_cfg()
    vcc = float(params.vcc or cfg.get("vcc") or 5.0)
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    bilim = float(cfg.get("bias_current_limit") or 0.05)
    settle = float(cfg.get("dmm_settle_s") or 0.2)
    n = int(cfg.get("dmm_readings") or 3)
    vcom = round(vcc * 0.5, 3)
    if not _pause(
        params,
        "VTH",
        [
            "CH3=V+/2 -> COM1; DMM VDC NO1; NC open.",
            "AWG CH1 DC -> IN1. Continue.",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "VTH"}}
    thresh = vcom * 0.5
    vth = float("nan")
    rows: list[dict[str, float]] = []
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        power_on_protected(instr.psu, 3, vcom, bilim)
        for i in range(11):
            vin = round(vcc * i / 10.0, 3)
            setup_dc(instr.gen, 1, vin)
            time.sleep(settle)
            vno = _avg_v(instr.dmm, n)
            rows.append({"VIN": vin, "VNO": round(vno, 6)})
            if vth != vth and vno >= thresh:
                vth = vin
        if vth != vth:
            vth = vcc
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
        "summary": f"VTH={vth:.3f} V (COM={vcom} V)",
        "data": {"Test": "VTH", "VCC": vcc, "VCOM": vcom, "VTH_V": vth, "rows": rows},
        "measurements": [{"id": "VTH_V", "value": round(float(vth), 3), "unit": "V"}],
    }


def _read_pf(dmm) -> float:
    from dmm_setup import dmm_read, dmm_setup_cap

    dmm_setup_cap(dmm)
    return float(dmm_read(dmm)) * 1e12


def _run_con_coff(instr, params: RunParams) -> dict[str, Any]:
    """CIN/CON/COFF via DMM CAP (same helper as RS0204 Cio). No ohms SCPI."""
    if getattr(instr, "dmm", None) is None:
        raise RuntimeError("Missing instruments: DMM")
    if getattr(instr, "psu", None) is None:
        raise RuntimeError("Missing instruments: PSU")
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    vcc = float(params.vcc or cfg.get("vcc") or 5.0)
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    out: dict[str, float] = {}
    meas: list[dict[str, Any]] = []

    _power_off(instr.psu)
    if not _pause(params, "CIN", ["DUT V+ OFF.", "DMM CAP IN1 to GND"]):
        return {"summary": "aborted", "data": {"Test": "CON_COFF"}}
    out["CIN_pF"] = round(_read_pf(instr.dmm), 3)
    meas.append({"id": "CIN_pF", "value": out["CIN_pF"], "unit": "pF"})

    _power_off(instr.psu)
    if not _pause(
        params,
        "CON",
        ["IN1 -> V+ (NO ON).", "PSU CH1=V+; DMM CAP COM1-NO1; NC open"],
    ):
        return {"summary": "aborted", "data": {"Test": "CON_COFF", **out}, "measurements": meas}
    power_on_protected(instr.psu, 1, vcc, ilim)
    time.sleep(float(cfg.get("dmm_settle_s") or 0.2))
    out["CON_pF"] = round(_read_pf(instr.dmm), 3)
    meas.append({"id": "CON_pF", "value": out["CON_pF"], "unit": "pF"})
    _power_off(instr.psu)

    if not _pause(
        params,
        "COFF",
        ["IN1 -> GND (NO OFF).", "PSU CH1=V+; DMM CAP COM1-NO1; NC open"],
    ):
        return {"summary": "aborted", "data": {"Test": "CON_COFF", **out}, "measurements": meas}
    power_on_protected(instr.psu, 1, vcc, ilim)
    time.sleep(float(cfg.get("dmm_settle_s") or 0.2))
    out["COFF_pF"] = round(_read_pf(instr.dmm), 3)
    meas.append({"id": "COFF_pF", "value": out["COFF_pF"], "unit": "pF"})
    _power_off(instr.psu)
    return {
        "summary": f"CIN={out.get('CIN_pF')} CON={out.get('CON_pF')} COFF={out.get('COFF_pF')} pF",
        "data": {"Test": "CON_COFF", **out},
        "measurements": meas,
    }


def _run_tbbm(instr, params: RunParams) -> dict[str, Any]:
    """Break-before-make: delay between NO and NC edges (measure_delay)."""
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    cfg = _part_cfg()
    vcc = float(params.vcc or cfg.get("vcc") or 5.0)
    ilim = float(cfg.get("current_limit") or params.current_limit_a or 0.1)
    tbbm = float("nan")
    if not _pause(
        params,
        "tBBM",
        [
            "AWG CH1 -> IN1.",
            "MSO CH1=NO1 CH2=NC1; PSU CH1=V+; COM open or mid-bias",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "TBBM"}}
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_square(instr.gen, 1, 100000.0, vcc, vcc / 2.0)
        scope_setup(instr.scope, 50e-9, vcc / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        t_rr = abs(measure_delay(instr.scope, "RRDelay", 1, 2))
        t_ff = abs(measure_delay(instr.scope, "FFDelay", 1, 2))
        tbbm = min(t_rr, t_ff) * 1e9
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
        "summary": f"tBBM={tbbm:.2f} ns",
        "data": {"Test": "TBBM", "VCC": vcc, "TBBM_ns": tbbm},
        "measurements": [{"id": "TBBM_ns", "value": round(tbbm, 3), "unit": "ns"}],
    }


def _reg(
    test_id: str,
    label: str,
    lab_sheet: str,
    run,
    steps: list[dict[str, Any]],
    required: frozenset[str] | None = None,
) -> None:
    register(
        TestSpec(
            id=test_id,
            label=label,
            required_instruments=required or frozenset({"PSU", "DMM"}),
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
_reg(
    "ron",
    "ON-Resistance",
    "Ron",
    _run_ron,
    [
        {"id": "wire_no", "label": "Wire NO ON then Continue", "phase": "operator"},
        {"id": "sweep_no", "label": "Sweep RON NO vs VCOM", "phase": "measure"},
        {"id": "wire_nc", "label": "Wire NC ON then Continue", "phase": "operator"},
        {"id": "sweep_nc", "label": "Sweep RON NC vs VCOM", "phase": "measure"},
    ],
)
_reg(
    "vth",
    "Switch Input Threshold",
    "Vth",
    _run_vth,
    [
        {"id": "wire", "label": "Wire COM/NO + AWG IN then Continue", "phase": "operator"},
        {"id": "sweep", "label": "Sweep VIN, read VNO", "phase": "measure"},
    ],
    required=frozenset({"PSU", "DMM", "AWG"}),
)
_reg(
    "ton_toff",
    "Switching Time (TON/TOFF)",
    "TON",
    _run_ton_toff,
    [
        {"id": "wire", "label": "Wire IN + MSO then Continue", "phase": "operator"},
        {"id": "measure", "label": "Measure TON/TOFF", "phase": "measure"},
    ],
    required=frozenset({"PSU", "AWG", "MSO"}),
)
_reg(
    "con_coff",
    "CIN / CON / COFF",
    "CinConCoff",
    _run_con_coff,
    [
        {"id": "wire_cin", "label": "Wire CIN CAP then Continue", "phase": "operator"},
        {"id": "wire_con", "label": "Wire CON then Continue", "phase": "operator"},
        {"id": "wire_coff", "label": "Wire COFF then Continue", "phase": "operator"},
    ],
)
_reg(
    "tbbm",
    "Break-Before-Make (tBBM)",
    "TBBM",
    _run_tbbm,
    [
        {"id": "wire", "label": "Wire NO/NC + MSO then Continue", "phase": "operator"},
        {"id": "measure", "label": "Measure tBBM", "phase": "measure"},
    ],
    required=frozenset({"PSU", "AWG", "MSO"}),
)
