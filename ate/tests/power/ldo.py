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


def _arm_ldo(cfg: dict[str, Any]) -> None:
    """SIM DMM node = VOUT. Live USB ignores the bus."""
    from ate.instruments.sim import set_ldo_dut

    set_ldo_dut(True, _vout_nominal(cfg))


def _disarm_ldo() -> None:
    from ate.instruments.sim import set_ldo_dut

    set_ldo_dut(False)


def _power_off(psu) -> None:
    from psu_setup import power_off

    try:
        power_off(psu)
    except Exception:
        pass


def _psu_on(psu, ch: int, volts: float, ilim: float) -> None:
    """OVP/OCP = Vset+0.3 V / Iset+0.1 A. Do not pass a 6 V trip (too loose)."""
    from psu_setup import power_on_protected

    v = float(volts)
    kw: dict[str, float] = {}
    if v <= 0.05:
        kw["ovp"] = 5.3
    power_on_protected(psu, ch, v, float(ilim), **kw)


def _run_iq(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_current

    cfg = _part_cfg()
    if not _pause(
        params,
        "LDO IQ",
        [
            "PSU CH1 = VOUT bias (not VIN)",
            "PSU CH2 = VIN (2.0 / 3.3 / 5.0 V)",
            "CH3 OFF. Iset=100 mA. OVP=Vset+0.3 V (not 6 V)",
            "DMM current in IQ path",
        ],
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
        _arm_ldo(cfg)
        _psu_on(instr.psu, 1, vout, ilim)
        time.sleep(settle)
        for vin in vins:
            _psu_on(instr.psu, 2, vin, ilim)
            time.sleep(settle)
            i_ua = _avg(instr.dmm, n) * 1e6
            rows.append({"VIN_V": vin, "VOUT_bias_V": vout, "IQ_uA": round(i_ua, 4)})
    finally:
        _disarm_ldo()
        _power_off(instr.psu)
    worst = max(rows, key=lambda r: abs(r["IQ_uA"])) if rows else {}
    meas = []
    if worst.get("IQ_uA") is not None:
        meas.append({"id": "IQ_uA", "value": worst["IQ_uA"], "unit": "uA"})
    return {
        "summary": f"IQ n={len(rows)} worst={worst.get('IQ_uA')} uA",
        "data": {"Test": "IQ", "rows": rows, "worst": worst},
        "measurements": meas,
    }


def _run_vinmin(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage

    cfg = _part_cfg()
    if not _pause(
        params,
        "LDO VINMIN",
        [
            "PSU CH1 = VIN sweep",
            "PSU CH3 = EN 5.0 V / 50 mA (OVP 5.3 V)",
            "CH2 OFF. DMM on VOUT",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "VINMIN"}}
    dmm_setup_voltage(instr.dmm)
    _arm_ldo(cfg)
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
        _psu_on(instr.psu, 3, 5.0, 0.05)
        for vin in vins:
            _psu_on(instr.psu, 1, vin, ilim)
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
        _disarm_ldo()
        _power_off(instr.psu)
    passed = [r for r in rows if r.get("STATUS") == "PASS"]
    vinmin = float(passed[0]["VIN_V"]) if passed else float(rows[-1]["VIN_V"] if rows else float("nan"))
    return {
        "summary": f"VINMIN n={len(rows)} VINMIN={vinmin} V limit={limit:.3f} V",
        "data": {"Test": "VINMIN", "vout_limit_v": limit, "rows": rows, "VINMIN_V": vinmin},
        "measurements": [{"id": "VINMIN_V", "value": vinmin, "unit": "V"}],
    }


def _run_lir(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage

    cfg = _part_cfg()
    if not _pause(
        params,
        "LDO LIR",
        [
            "PSU CH1 = VIN",
            "PSU CH3 = EN 5.0 V / 50 mA",
            "CH2 OFF. No AWG 5.5 V. DMM on VOUT",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "LIR"}}
    dmm_setup_voltage(instr.dmm)
    _arm_ldo(cfg)
    vout = _vout_nominal(cfg)
    vins = _floats(cfg, "vin_lir", [3.4, 5.0])
    ilim = _ilim(cfg, "vin_current_limit") if cfg.get("vin_current_limit") else _ilim(cfg)
    n = _nread(cfg)
    settle = _settle(cfg)
    rows: list[dict[str, Any]] = []
    try:
        _psu_on(instr.psu, 3, 5.0, 0.05)
        time.sleep(settle)
        for vin in vins:
            _psu_on(instr.psu, 1, vin, ilim)
            time.sleep(settle)
            vout_avg = _avg(instr.dmm, n)
            rows.append({"VIN_V": vin, "VOUT_AVG_V": round(vout_avg, 5)})
    finally:
        _disarm_ldo()
        _power_off(instr.psu)
    dv = 0.0
    if len(rows) >= 2:
        dv = abs(float(rows[-1]["VOUT_AVG_V"]) - float(rows[0]["VOUT_AVG_V"]))
    lir_mv = round(dv * 1000.0, 3)
    return {
        "summary": f"LIR n={len(rows)} LIR={lir_mv} mV VOUT_nom={vout}",
        "data": {"Test": "LIR", "vout_nominal": vout, "rows": rows, "LIR_mV": lir_mv},
        "measurements": [{"id": "LIR_mV", "value": lir_mv, "unit": "mV"}],
    }


def _run_lor(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage

    cfg = _part_cfg()
    if not _pause(
        params,
        "LDO LOR",
        [
            "PSU CH1 = VIN (3.9 V typical, Iset=400 mA)",
            "PSU CH2 = load voltage",
            "PSU CH3 = EN 5.0 V / 50 mA. No AWG 5.5 V. DMM on VOUT",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "LOR"}}
    dmm_setup_voltage(instr.dmm)
    _arm_ldo(cfg)
    loads = _floats(cfg, "load_lor", [0.01, 0.5])
    vin = float(cfg.get("lor_vin") or 3.9)
    n = _nread(cfg)
    settle = _settle(cfg)
    rows: list[dict[str, Any]] = []
    try:
        _psu_on(instr.psu, 1, vin, float(cfg.get("vin_current_limit") or 0.4))
        _psu_on(instr.psu, 3, 5.0, 0.05)
        time.sleep(settle)
        for load_v in loads:
            load_a = round(load_v * 0.1, 3)
            _psu_on(instr.psu, 2, load_v, max(load_a, 0.001))
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
        _disarm_ldo()
        _power_off(instr.psu)
    dv = 0.0
    if len(rows) >= 2:
        dv = abs(float(rows[-1]["VOUT_AVG_V"]) - float(rows[0]["VOUT_AVG_V"]))
    lor_mv = round(dv * 1000.0, 3)
    return {
        "summary": f"LOR n={len(rows)} LOR={lor_mv} mV",
        "data": {"Test": "LOR", "rows": rows, "LOR_mV": lor_mv},
        "measurements": [{"id": "LOR_mV", "value": lor_mv, "unit": "mV"}],
    }


def _run_ioutmax(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_voltage

    cfg = _part_cfg()
    if not _pause(
        params,
        "LDO IOUTMAX",
        [
            "PSU CH1 = VIN",
            "PSU CH2 = load",
            "PSU CH3 = EN 5.0 V / 50 mA. No AWG 5.5 V. DMM on VOUT",
        ],
    ):
        return {"summary": "aborted", "data": {"Test": "IOUTMAX"}}
    dmm_setup_voltage(instr.dmm)
    _arm_ldo(cfg)
    vins = _floats(cfg, "iout_vin", [3.3, 5.0])
    loads = _floats(cfg, "load_iout", [0.01, 0.5])
    n = _nread(cfg)
    settle = _settle(cfg)
    rows: list[dict[str, Any]] = []
    try:
        _psu_on(instr.psu, 3, 5.0, 0.05)
        for vin in vins:
            _psu_on(instr.psu, 1, vin, float(cfg.get("vin_current_limit") or 0.4))
            time.sleep(settle)
            for load_v in loads:
                load_a = round(load_v * 0.1, 3)
                _psu_on(instr.psu, 2, load_v, max(load_a, 0.001))
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
        _disarm_ldo()
        _power_off(instr.psu)
    worst = min(rows, key=lambda r: float(r["VOUT_AVG_V"])) if rows else {}
    vout_min = float(worst.get("VOUT_AVG_V") or float("nan"))
    return {
        "summary": f"IOUTMAX n={len(rows)} VOUT_min={vout_min} V",
        "data": {"Test": "IOUTMAX", "rows": rows, "IOUTMAX_V": vout_min},
        "measurements": [{"id": "IOUTMAX_V", "value": vout_min, "unit": "V"}],
    }


def _run_enable(instr, params: RunParams) -> dict[str, Any]:
    _require(instr)
    from dmm_setup import dmm_setup_current

    cfg = _part_cfg()
    if not _pause(
        params,
        "LDO IEN",
        [
            "PSU CH1 = VIN",
            "PSU CH2 = VEN (0 V and 5.0 V)",
            "CH3 OFF. Iset=100 mA. DMM current on EN",
        ],
    ):
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
            _psu_on(instr.psu, 1, vin, ilim)
            time.sleep(settle)
            for ven in vens:
                _psu_on(instr.psu, 2, ven, ilim)
                time.sleep(settle)
                i_ua = _avg(instr.dmm, n) * 1e6
                rows.append({"VIN_V": vin, "VEN_V": ven, "IEN_uA": round(i_ua, 4)})
    finally:
        _power_off(instr.psu)
    mx = max(abs(float(r["IEN_uA"])) for r in rows) if rows else float("nan")
    return {
        "summary": f"IEN n={len(rows)} worst={mx} uA",
        "data": {"Test": "IEN", "rows": rows, "IEN_uA": mx},
        "measurements": [{"id": "IEN_uA", "value": mx, "unit": "uA"}],
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
