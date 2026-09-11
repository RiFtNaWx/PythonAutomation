"""LDO TestSpecs (RS3213 / RS3235).

Platform wraps of Ariff LDO_tests.py. Do not import that file.
Wiring uses pause_hook (Continue). power_on_protected only.
Sweep points come from the selected part yaml so each SKU runs separately.
"""
from __future__ import annotations

import re
import time
from typing import Any

import yaml

from ate.core.paths import PARTS_DIR
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_FIXTURE = "LDO"
_VOUT_RE = re.compile(r"-(\d+(?:\.\d+)?)", re.I)


def _part_key() -> str:
    try:
        from ate.core.database import get_context

        pk = str(get_context().part_key or "").strip()
        if pk:
            return pk
    except Exception:
        pass
    return "rs3213"


def _part_cfg() -> dict[str, Any]:
    path = PARTS_DIR / f"{_part_key()}.yaml"
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
        return True
    detail = title + " | " + " ; ".join(checklist[:4])
    return bool(hook(detail))


def _vout_nominal(cfg: dict[str, Any]) -> float:
    raw = cfg.get("vout_nominal")
    if raw not in (None, ""):
        return float(raw)
    model = str(cfg.get("model") or "")
    m = _VOUT_RE.search(model)
    if m:
        return float(m.group(1))
    return 3.3


def _floats(cfg: dict[str, Any], key: str, default: list[float]) -> list[float]:
    raw = cfg.get(key)
    if not raw:
        return list(default)
    return [float(x) for x in raw]


def _settle(cfg: dict[str, Any]) -> float:
    return float(cfg.get("dmm_settle_s") or 0.3)


def _nread(cfg: dict[str, Any]) -> int:
    return max(1, int(cfg.get("dmm_readings") or 3))


def _ilim(cfg: dict[str, Any], key: str = "current_limit") -> float:
    return float(cfg.get(key) or 0.1)


def _avg(dmm, n: int) -> float:
    from dmm_setup import dmm_read

    vals = [float(dmm_read(dmm)) for _ in range(n)]
    return sum(vals) / len(vals)


def _power_off(psu) -> None:
    from psu_setup import power_off

    try:
        power_off(psu)
    except Exception:
        pass


def _enable_dc(instr, volts: float) -> None:
    gen = getattr(instr, "gen", None)
    if gen is None:
        return
    from generator_setup import setup_dc

    setup_dc(gen, 1, volts)


def _run_iq(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_current
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    if not _pause(
        params,
        "LDO IQ",
        ["PSU CH1 = VOUT sense/bias", "PSU CH2 = VIN", "DMM current in IQ path"],
    ):
        return {"summary": "aborted", "data": {"Test": "IQ"}}
    dmm_setup_current(instr.dmm)
    vout = _vout_nominal(cfg)
    ilim = _ilim(cfg)
    settle = _settle(cfg)
    n = _nread(cfg)
    vins = _floats(cfg, "vin_iq", [2.0, 3.3, 5.0])
    rows: list[dict[str, Any]] = []
    try:
        power_on_protected(instr.psu, 1, vout, ilim, ovp=vout + 0.5)
        time.sleep(settle)
        for vin in vins:
            power_on_protected(instr.psu, 2, vin, ilim, ovp=max(vins) + 0.5)
            time.sleep(settle)
            i_ua = _avg(instr.dmm, n) * 1e6
            rows.append({"VIN_V": vin, "VOUT_V": vout, "IQ_uA": round(i_ua, 4)})
    finally:
        _power_off(instr.psu)
    worst = max(rows, key=lambda r: abs(r["IQ_uA"])) if rows else {}
    meas = []
    if worst.get("IQ_uA") is not None:
        meas.append({"id": "IQ_uA", "value": worst["IQ_uA"], "unit": "uA"})
    meas.append({"id": "VOUT_V", "value": vout, "unit": "V"})
    return {
        "summary": f"IQ n={len(rows)} worst={worst.get('IQ_uA')} uA",
        "data": {"Test": "IQ", "rows": rows, "worst": worst},
        "measurements": meas,
    }


def _run_vinmin(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    if not _pause(params, "LDO VINMIN", ["PSU CH1 = VIN sweep", "DMM on VOUT"]):
        return {"summary": "aborted", "data": {"Test": "VINMIN"}}
    dmm_setup_voltage(instr.dmm)
    vout = _vout_nominal(cfg)
    margin = float(cfg.get("vin_min_margin") or 0.4)
    step = float(cfg.get("vin_min_step") or 0.2)
    start = round(vout - margin, 2)
    stop = round(vout + margin, 2)
    limit = vout * 0.98
    n = _nread(cfg)
    settle = _settle(cfg)
    ilim = float(cfg.get("vin_current_limit") or 0.4)
    vins: list[float] = []
    v = start
    while v <= stop + 1e-9:
        vins.append(round(v, 2))
        v += step
    rows: list[dict[str, Any]] = []
    try:
        power_on_protected(instr.psu, 3, 5.0, 0.05, ovp=5.5)
        for vin in vins:
            power_on_protected(instr.psu, 1, vin, ilim, ovp=stop + 0.5)
            time.sleep(settle)
            vout_avg = _avg(instr.dmm, n)
            rows.append(
                {
                    "VIN_V": vin,
                    "VOUT_AVG_V": round(vout_avg, 5),
                    "STATUS": "PASS" if vout_avg >= limit else "FAIL",
                }
            )
    finally:
        _power_off(instr.psu)
    return {
        "summary": f"VINMIN n={len(rows)} limit={limit:.3f} V",
        "data": {"Test": "VINMIN", "vout_limit_v": limit, "rows": rows},
    }


def _run_lir(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    if not _pause(params, "LDO LIR", ["PSU CH1 = VIN", "DMM on VOUT", "EN biased"]):
        return {"summary": "aborted", "data": {"Test": "LIR"}}
    dmm_setup_voltage(instr.dmm)
    vout = _vout_nominal(cfg)
    vins = _floats(cfg, "vin_lir", [3.4, 5.0])
    ilim = _ilim(cfg, "vin_current_limit") if cfg.get("vin_current_limit") else _ilim(cfg)
    n = _nread(cfg)
    settle = _settle(cfg)
    rows: list[dict[str, Any]] = []
    try:
        power_on_protected(instr.psu, 3, 5.0, 0.05, ovp=5.5)
        _enable_dc(instr, 5.5)
        time.sleep(settle)
        for vin in vins:
            power_on_protected(instr.psu, 1, vin, ilim, ovp=max(vins) + 0.5)
            time.sleep(settle)
            vout_avg = _avg(instr.dmm, n)
            rows.append({"VIN_V": vin, "VOUT_AVG_V": round(vout_avg, 5)})
    finally:
        _power_off(instr.psu)
    return {
        "summary": f"LIR n={len(rows)} VOUT_nom={vout}",
        "data": {"Test": "LIR", "vout_nominal": vout, "rows": rows},
    }


def _run_lor(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    if not _pause(params, "LDO LOR", ["PSU CH1 = VIN", "PSU CH2 = load", "DMM on VOUT"]):
        return {"summary": "aborted", "data": {"Test": "LOR"}}
    dmm_setup_voltage(instr.dmm)
    loads = _floats(cfg, "load_lor", [0.01, 0.5])
    vin = float(cfg.get("lor_vin") or 3.9)
    n = _nread(cfg)
    settle = _settle(cfg)
    rows: list[dict[str, Any]] = []
    try:
        power_on_protected(instr.psu, 1, vin, float(cfg.get("vin_current_limit") or 0.4), ovp=6.0)
        power_on_protected(instr.psu, 3, 5.0, 0.05, ovp=5.5)
        _enable_dc(instr, 5.5)
        time.sleep(settle)
        for load_v in loads:
            load_a = round(load_v * 0.1, 3)
            power_on_protected(instr.psu, 2, load_v, max(load_a, 0.001), ovp=5.6)
            time.sleep(settle)
            vout_avg = _avg(instr.dmm, n)
            rows.append(
                {
                    "LOAD_V": load_v,
                    "LOAD_A": load_a,
                    "VOUT_AVG_V": round(vout_avg, 5),
                }
            )
    finally:
        _power_off(instr.psu)
    return {"summary": f"LOR n={len(rows)}", "data": {"Test": "LOR", "rows": rows}}


def _run_ioutmax(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    if not _pause(params, "LDO IOUTMAX", ["PSU CH1 = VIN", "PSU CH2 = load", "DMM on VOUT"]):
        return {"summary": "aborted", "data": {"Test": "IOUTMAX"}}
    dmm_setup_voltage(instr.dmm)
    vins = _floats(cfg, "iout_vin", [3.3, 5.0])
    loads = _floats(cfg, "load_iout", [0.01, 0.5])
    n = _nread(cfg)
    settle = _settle(cfg)
    rows: list[dict[str, Any]] = []
    try:
        power_on_protected(instr.psu, 3, 5.0, 0.05, ovp=6.0)
        _enable_dc(instr, 5.5)
        for vin in vins:
            power_on_protected(instr.psu, 1, vin, float(cfg.get("vin_current_limit") or 0.4), ovp=vin + 0.5)
            time.sleep(settle)
            for load_v in loads:
                load_a = round(load_v * 0.1, 3)
                power_on_protected(instr.psu, 2, load_v, max(load_a, 0.001), ovp=5.6)
                time.sleep(settle)
                vout_avg = _avg(instr.dmm, n)
                rows.append(
                    {
                        "VIN_V": vin,
                        "LOAD_A": load_a,
                        "VOUT_AVG_V": round(vout_avg, 5),
                    }
                )
    finally:
        _power_off(instr.psu)
    return {"summary": f"IOUTMAX n={len(rows)}", "data": {"Test": "IOUTMAX", "rows": rows}}


def _run_enable(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_current
    from psu_setup import power_on_protected

    cfg = _part_cfg()
    if not _pause(params, "LDO IEN", ["PSU CH1 = VIN", "PSU CH2 = VEN", "DMM current on EN"]):
        return {"summary": "aborted", "data": {"Test": "IEN"}}
    dmm_setup_current(instr.dmm)
    vins = _floats(cfg, "enable_vin", [3.4, 5.0])
    vens = _floats(cfg, "enable_ven", [0.0, 5.0])
    ilim = _ilim(cfg)
    n = _nread(cfg)
    settle = _settle(cfg)
    rows: list[dict[str, Any]] = []
    try:
        for vin in vins:
            power_on_protected(instr.psu, 1, vin, ilim, ovp=vin + 0.5)
            time.sleep(settle)
            for ven in vens:
                power_on_protected(instr.psu, 2, ven, ilim, ovp=6.5)
                time.sleep(settle)
                i_ua = _avg(instr.dmm, n) * 1e6
                rows.append({"VIN_V": vin, "VEN_V": ven, "IEN_uA": round(i_ua, 4)})
    finally:
        _power_off(instr.psu)
    return {"summary": f"IEN n={len(rows)}", "data": {"Test": "IEN", "rows": rows}}


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
            notes="LDO / Linear Regulator -- Continue for wiring; no Ariff import",
            short_tag=lab_sheet,
        )
    )


_reg(
    "iq",
    "Quiescent current (IQ)",
    "IQ",
    _run_iq,
    [
        {"id": "wire", "label": "Wire IQ path then Continue", "phase": "operator"},
        {"id": "sweep", "label": "Sweep VIN for IQ", "phase": "measure"},
    ],
)
_reg(
    "vinmin",
    "Minimum input voltage (VINMIN)",
    "VINMIN",
    _run_vinmin,
    [
        {"id": "wire", "label": "Wire VIN/VOUT then Continue", "phase": "operator"},
        {"id": "sweep", "label": "Sweep VIN around VOUT", "phase": "measure"},
    ],
)
_reg(
    "lir",
    "Line regulation (LIR)",
    "LIR",
    _run_lir,
    [
        {"id": "wire", "label": "Wire line-regulation then Continue", "phase": "operator"},
        {"id": "sweep", "label": "Sweep VIN", "phase": "measure"},
    ],
)
_reg(
    "lor",
    "Load regulation (LOR)",
    "LOR",
    _run_lor,
    [
        {"id": "wire", "label": "Wire load path then Continue", "phase": "operator"},
        {"id": "sweep", "label": "Sweep load", "phase": "measure"},
    ],
)
_reg(
    "ioutmax",
    "Max output current (IOUTMAX)",
    "IOUTMAX",
    _run_ioutmax,
    [
        {"id": "wire", "label": "Wire IOUTMAX then Continue", "phase": "operator"},
        {"id": "sweep", "label": "Sweep VIN and load", "phase": "measure"},
    ],
)
_reg(
    "enable_current",
    "Enable pin current (IEN)",
    "IEN",
    _run_enable,
    [
        {"id": "wire", "label": "Wire EN current then Continue", "phase": "operator"},
        {"id": "sweep", "label": "Sweep VIN and VEN", "phase": "measure"},
    ],
)
