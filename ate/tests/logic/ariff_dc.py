"""Ariff / RS1G Logic DC TestSpecs (A09 + A12).

Native bodies modeled on Ariff Repo LabAutomation_v1 - Copy/logic_tests.py
(2026-09-03 16:41). Do not import Ariff.* / configurations.py / limits.py.
Limits and sweep tables live in part YAML.

Ids voh_load / vol_load avoid clobbering RS0204's voh / vol in the same
Logic registry. supply_current_sweep avoids clobbering Soo supply_current.
"""
from __future__ import annotations

import itertools
import time
from collections.abc import Callable
from typing import Any

import yaml

from ate.core.paths import PARTS_DIR
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_LOGIC_FIXTURE = "LOGIC"
_NOTE = "Ariff Logic DC (A12) — params from part YAML; no import Ariff.*"
# ponytail: DG822 has 2 AWG channels. n>2 needs pause_hook rewire / mux. Cap 8.
_AWG_DRIVE_CH = 2
_MAX_LOGIC_INPUTS = 8

# Defaults when part yaml omits tables (RS1G08-class)
_DEFAULT_VOH_ROWS = [
    {"vcc": 2.0, "vref": 0.0, "spec_min": 1.9, "ioh_a": 0.0001},
    {"vcc": 3.3, "vref": 0.0, "spec_min": 3.2, "ioh_a": 0.0001},
    {"vcc": 4.5, "vref": 0.0, "spec_min": 4.4, "ioh_a": 0.0001},
    {"vcc": 5.0, "vref": 0.0, "spec_min": 4.9, "ioh_a": 0.0001},
    {"vcc": 5.5, "vref": 0.0, "spec_min": 5.4, "ioh_a": 0.0001},
    {"vcc": 2.0, "vref": 0.080, "spec_min": 1.6, "ioh_a": 0.008},
    {"vcc": 3.3, "vref": 0.240, "spec_min": 2.5, "ioh_a": 0.024},
    {"vcc": 4.5, "vref": 0.320, "spec_min": 3.8, "ioh_a": 0.032},
    {"vcc": 5.0, "vref": 0.320, "spec_min": 4.2, "ioh_a": 0.032},
    {"vcc": 5.5, "vref": 0.320, "spec_min": 4.8, "ioh_a": 0.032},
]
_DEFAULT_VOL_ROWS = [
    {"vcc": 2.0, "vref": 4.92, "spec_max": 0.45, "iol_a": 0.008},
    {"vcc": 3.3, "vref": 4.76, "spec_max": 0.55, "iol_a": 0.024},
    {"vcc": 4.5, "vref": 4.68, "spec_max": 0.55, "iol_a": 0.032},
    {"vcc": 5.0, "vref": 4.68, "spec_max": 0.50, "iol_a": 0.032},
    {"vcc": 5.5, "vref": 4.68, "spec_max": 0.45, "iol_a": 0.032},
]


def _part_cfg(params: RunParams) -> dict[str, Any]:
    key = str(getattr(params, "part", None) or "rs1g08").strip().lower()
    path = PARTS_DIR / f"{key}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _current_limit(params: RunParams) -> float:
    cfg = _part_cfg(params)
    return float(
        getattr(params, "current_limit_a", None)
        or getattr(params, "current_limit", None)
        or cfg.get("current_limit")
        or 0.05
    )


def _require(instr, *names: str) -> None:
    remap = {"MSO": "scope", "PSU": "psu", "AWG": "gen", "DMM": "dmm"}
    missing = [n for n in names if getattr(instr, remap[n], None) is None]
    if missing:
        raise RuntimeError(f"Missing instruments: {', '.join(missing)}")


def _power_cycle(instr, vcc: float, current_limit: float, *, ovp: float | None = None) -> None:
    from psu_setup import OVP_ABS_MAX_V, power_on_protected

    kwargs = {}
    if ovp is not None:
        kwargs["ovp"] = min(float(ovp), OVP_ABS_MAX_V)
    power_on_protected(instr.psu, 1, vcc, current_limit, **kwargs)
    time.sleep(0.3)


def _y_invert(cfg: dict[str, Any]) -> bool:
    """Schmitt inverter (RS1G14). Do not invent invert on AND/OR/buffer/OE."""
    if "y_invert" in cfg:
        return bool(cfg.get("y_invert"))
    pm = cfg.get("product_model")
    if isinstance(pm, dict) and pm.get("schmitt"):
        tt = pm.get("truth_table")
        rows = tt.get("rows") if isinstance(tt, dict) else None
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                if str(row.get("A") or "").upper() == "H" and str(row.get("Y") or "").upper() == "L":
                    return True
    return False


def _set_y_invert(cfg: dict[str, Any]) -> None:
    from ate.instruments.sim import set_schmitt, set_y_invert

    set_y_invert(_y_invert(cfg))
    pm = cfg.get("product_model")
    set_schmitt(bool(isinstance(pm, dict) and pm.get("schmitt")))


def _power_down(instr) -> None:
    from ate.instruments.sim import set_schmitt, set_y_invert
    from generator_setup import stop_output
    from psu_setup import power_off

    set_y_invert(False)
    set_schmitt(False)
    try:
        if getattr(instr, "gen", None) is not None:
            stop_output(instr.gen)
    except Exception:
        pass
    try:
        power_off(instr.psu)
    except Exception:
        pass


def _avg_current_ua(dmm, n: int = 5) -> float:
    from dmm_setup import dmm_read, dmm_setup_current

    dmm_setup_current(dmm)
    readings = [float(dmm_read(dmm)) for _ in range(n)]
    return (sum(readings) / len(readings)) * 1e6


def _avg_voltage(dmm, n: int = 12, *, setup: bool = True) -> float:
    from dmm_setup import dmm_read, dmm_setup_voltage

    if setup:
        dmm_setup_voltage(dmm)
    readings = [float(dmm_read(dmm)) for _ in range(max(3, int(n)))]
    mean = sum(readings) / len(readings)
    rec = _record_v(mean)
    return 0.0 if rec is None else rec


def _raw_test_params(params: RunParams, test_id: str) -> dict[str, Any]:
    tp = getattr(params, "test_params", None) or {}
    if not isinstance(tp, dict):
        return {}
    block = tp.get(test_id) or {}
    return block if isinstance(block, dict) else {}


def _truthy(v: Any) -> bool:
    if v is True:
        return True
    if v in (False, None, "", 0, "0", "false", "False", "no", "off"):
        return False
    return bool(v)


def _include_100ua(params: RunParams, cfg: dict[str, Any], test_id: str) -> bool:
    """DP832 + 10 ohm cannot source/sink 100 uA. Off until Tests checkbox / yaml."""
    raw = _raw_test_params(params, test_id)
    for key in ("voh_100ua", "vol_100ua", "include_100ua"):
        if key in raw:
            return _truthy(raw[key])
    for key in ("voh_100ua", "vol_100ua", "include_100ua"):
        if key in cfg:
            return _truthy(cfg[key])
    return False


def _load_r_ohm(params: RunParams, cfg: dict[str, Any], test_id: str) -> float:
    raw = _raw_test_params(params, test_id)
    if raw.get("load_r_ohm") not in (None, ""):
        try:
            return float(raw["load_r_ohm"])
        except (TypeError, ValueError):
            pass
    return float(cfg.get("load_r_ohm") or 10.0)


def _skip_100ua_rows(rows_cfg: list[Any], *, include_100ua: bool, current_key: str) -> list[Any]:
    out: list[Any] = []
    for entry in rows_cfg:
        if not isinstance(entry, dict):
            continue
        i_a = abs(float(entry.get(current_key) or entry.get("ioh_a") or entry.get("iol_a") or 0))
        if i_a <= 0.00015 and not include_100ua:
            continue
        out.append(entry)
    return out


def _vcc_list(cfg: dict[str, Any], key: str, default: list[float]) -> list[float]:
    raw = cfg.get(key)
    if isinstance(raw, list) and raw:
        return [float(v) for v in raw]
    return list(default)


def _vcc_points(
    params: RunParams,
    cfg: dict[str, Any],
    *,
    default: list[float],
    part_key: str = "vcc_sweep_list",
) -> list[float]:
    """params.vcc_list -> part yaml list -> default (not blind 0..5 start/stop)."""
    overlay = list(getattr(params, "vcc_list", None) or [])
    if overlay:
        return [float(v) for v in overlay]
    part = _vcc_list(cfg, part_key, [])
    if part:
        return part
    return list(default)


def _record_v(v: Any) -> float | None:
    """Keep 6 decimal places (uV-class). Pass/fail uses this float vs datasheet limits."""
    if v is None:
        return None
    return round(float(v), 6)


def _interp_cross(x0: float, y0: float | None, x1: float, y1: float, mid: float) -> float | None:
    """Trip voltage between two VIN samples. Extra decimals beyond the sweep step."""
    if y0 is None:
        return None
    dy = float(y1) - float(y0)
    if abs(dy) < 1e-18:
        return _record_v(x1)
    frac = (float(mid) - float(y0)) / dy
    if frac < -1e-9 or frac > 1.0 + 1e-9:
        return None
    return _record_v(float(x0) + frac * (float(x1) - float(x0)))


def _record_i(v: Any) -> float:
    """Full DMM current. Do not round (uA/nA live in the fraction)."""
    return float(v)


def _vin_step(params: RunParams) -> float:
    raw = getattr(params, "vin_step", None)
    try:
        st = float(raw) if raw not in (None, "") else 0.0
    except (TypeError, ValueError):
        st = 0.0
    if st <= 0:
        st = 0.01
    return max(0.001, min(st, 0.5))


def _vin_step_ladder(hint: float, fine: float = 0.01) -> list[float]:
    """Coarse-to-fine VIN steps. First step scales with the datasheet limit.

    0.5, 0.2, 0.1, 0.05, 0.01 -- drop any step bigger than half the limit.
    Low VIH/VIL (e.g. 0.3 V) never starts at 0.5 V.
    """
    fine = max(0.001, min(float(fine or 0.01), 0.5))
    h = max(abs(float(hint) or 0.0), fine)
    cap = max(fine, min(0.5, 0.5 * h))
    out: list[float] = []
    for s in (0.5, 0.2, 0.1, 0.05, 0.01):
        if fine - 1e-12 <= s <= cap + 1e-12:
            out.append(float(s))
    cap_r = round(cap, 6)
    if cap_r >= fine and cap_r not in out:
        out.append(cap_r)
    if fine not in out:
        out.append(fine)
    return sorted(set(round(x, 6) for x in out), reverse=True)


def _y_trip_hit(vin_up: bool, invert: bool, prev: float | None, vout: float, mid: float) -> bool:
    if prev is None:
        return False
    if vin_up:
        if invert:
            return prev >= mid > vout
        return prev < mid <= vout
    if invert:
        return prev < mid <= vout
    return prev >= mid > vout


def _search_vin_trip(
    set_vin: Callable[[float], None],
    read_y: Callable[[], float],
    *,
    arm: float,
    stop: float,
    mid: float,
    vin_up: bool,
    invert: bool = False,
    hint: float = 0.0,
    fine: float = 0.01,
    dwell: float = 0.0,
    trace: list[float] | None = None,
) -> tuple[float | None, int]:
    """Same-direction coarse-to-fine trip. Arm rail, walk, hit, skip the rest.

    VIH: arm=0 walk up. VIL: arm=VCC walk down. After a hit, re-arm then
    restart 30% back on the approach side with the next smaller step.
    Stops at `fine` (default 0.01) + interpolate. Does not finish 0..VCC.
    """
    fine = max(0.001, min(float(fine or 0.01), 0.5))
    start = float(arm)
    end = float(stop)
    sign = 1.0 if vin_up else -1.0
    n = 0
    trip: float | None = None
    last_before = start
    last_after = end
    win_from = start
    hint_v = abs(float(hint) or 0.0)

    def _apply(v: float) -> float:
        nonlocal n
        vv = _record_v(v)
        v = float(vv if vv is not None else v)
        set_vin(v)
        if dwell:
            time.sleep(dwell)
        n += 1
        if trace is not None:
            trace.append(v)
        return float(read_y())

    def _clamp_dest(dest: float) -> float:
        if vin_up:
            return min(max(dest, start), end)
        return max(min(dest, start), end)

    first_dest = end
    if hint_v > 0:
        if vin_up and start < hint_v < end:
            first_dest = hint_v
        elif (not vin_up) and end < hint_v < start:
            first_dest = hint_v
    win_to = first_dest

    for step in _vin_step_ladder(hint_v or abs(end - start) or 1.0, fine):
        _apply(start)
        vin = _clamp_dest(win_from)
        y0 = _apply(vin)
        prev: float | None = y0
        prev_vin = vin
        dest = _clamp_dest(win_to)
        hit = False
        while True:
            nxt = float(prev_vin) + sign * step
            if vin_up:
                if nxt > dest + 1e-12:
                    nxt = dest
            elif nxt < dest - 1e-12:
                nxt = dest
            nxt_r = _record_v(nxt)
            nxt = float(nxt_r if nxt_r is not None else nxt)
            if abs(nxt - prev_vin) < 1e-12:
                if abs(dest - end) > 1e-9:
                    dest = end
                    continue
                break
            y1 = _apply(nxt)
            if _y_trip_hit(vin_up, invert, prev, y1, mid):
                trip = _interp_cross(float(prev_vin), prev, nxt, y1, mid)
                last_before = float(prev_vin)
                last_after = nxt
                hit = True
                break
            prev = y1
            prev_vin = nxt
            if abs(nxt - dest) < 1e-12:
                if abs(dest - end) > 1e-9:
                    dest = end
                    continue
                break
        if not hit:
            win_from = start
            win_to = end
            continue
        if step <= fine + 1e-12:
            return trip, n
        margin = max(step, 0.3 * (hint_v or abs(trip or step)))
        if vin_up:
            win_from = max(start, last_before - margin)
            win_to = min(end, last_after + fine)
        else:
            win_from = min(start, last_before + margin)
            win_to = max(end, last_after - fine)
    return trip, n


def _vin_points(vcc: float, step: float) -> list[float]:
    st = max(0.001, float(step) or 0.01)
    n = int(round(float(vcc) / st))
    out: list[float] = []
    for i in range(0, n + 1):
        v = _record_v(i * st)
        if v is not None:
            out.append(v)
    hi = _record_v(vcc)
    if hi is not None and (not out or abs(out[-1] - hi) > 1e-9):
        out.append(hi)
    return out


def _use_psu_mso(cfg: dict[str, Any]) -> bool:
    return str(cfg.get("vih_vil_stimulus") or "").strip().lower() in (
        "psu_mso",
        "psu",
        "mso",
    )


def _vih_vil_vcc_points(params: RunParams, cfg: dict[str, Any]) -> list[float]:
    """Yaml list below 4.5 V is the whole sweep unless vih_vil_vcc_range is set.

    AUP 1.8/2.5/3.3 must not grow a 4.5..5.5 band. 1G CMOS still appends that band
    when yaml has no explicit low-only list.
    """
    from ate.core.param_defaults import vcc_sweep_points

    yaml_raw = cfg.get("vih_vil_vcc_list")
    yaml_explicit = isinstance(yaml_raw, list) and bool(yaml_raw)
    rng = cfg.get("vih_vil_vcc_range")
    rng = rng if isinstance(rng, dict) else {}
    overlay = list(getattr(params, "vcc_list", None) or [])
    if yaml_explicit and not rng and not overlay:
        listed = [float(v) for v in yaml_raw]
        if listed and max(listed) < 4.5 - 1e-9:
            return listed
    raw_list = overlay or _vcc_list(cfg, "vih_vil_vcc_list", [2.0, 3.3])
    fixed = [float(v) for v in raw_list if float(v) < 4.5 - 1e-9]
    start = float(rng.get("start") or 4.5)
    stop = float(rng.get("stop") or 5.5)
    step = float(rng.get("step") or 0.01)
    ps = float(getattr(params, "vcc_start", 0.0) or 0.0)
    pe = float(getattr(params, "vcc_stop", 0.0) or 0.0)
    pt = float(getattr(params, "vcc_step", 0.0) or 0.0)
    if ps >= 4.0 and pe >= ps:
        start, stop = ps, pe
        if pt > 0:
            step = pt
    band = vcc_sweep_points(start, stop, step)
    out: list[float] = []
    seen: set[float] = set()
    for v in fixed + [float(x) for x in band]:
        k = round(v, 4)
        if k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out or [2.0, 3.3]


def _vih_vil_lim(vcc: float, cfg: dict[str, Any]) -> dict[str, Any]:
    limits = cfg.get("vih_vil_limits") if isinstance(cfg.get("vih_vil_limits"), dict) else {}
    tag = str(vcc)
    for key in (tag, f"{vcc:.1f}", f"{vcc:.2f}", round(vcc, 1), round(vcc, 2), vcc):
        lim = limits.get(key)
        if isinstance(lim, dict) and lim:
            return lim
    band = cfg.get("vih_vil_band_limits") if isinstance(cfg.get("vih_vil_band_limits"), dict) else {}
    lo = float(band.get("vcc_lo") or 4.5)
    hi = float(band.get("vcc_hi") or 5.5)
    if lo - 1e-9 <= vcc <= hi + 1e-9:
        if band:
            return {
                "vih_max": band.get("vih_max", 2.0),
                "vil_min": band.get("vil_min", 0.8),
            }
        return {"vih_max": 2.0, "vil_min": 0.8}
    return {}


def _mso_setup_dc_y(scope, vcc: float) -> None:
    scale = max(float(vcc) / 4.0, 0.5)
    scope.write(":CHAN1:DISP ON")
    scope.write(":CHAN1:COUP DC")
    scope.write(f":CHAN1:SCAL {scale:.4g}")
    scope.write(":CHAN1:OFFS 0")
    scope.write(":TIM:SCAL 0.005")
    scope.write(":TRIGger:SWEep AUTO")
    try:
        scope.write(":SYSTem:KEY:PRESs MOFF")
    except Exception:
        pass


def _mso_vavg_ch1(scope) -> float:
    scope.write(":MEAS:ITEM VAVG,CHAN1")
    return float(scope.query(":MEAS:ITEM? VAVG,CHAN1"))


def _logic_inputs(cfg: dict[str, Any], params: RunParams | None = None) -> int:
    """n inputs for 2^n corners. Default 2. Cap 8 (AWG drive still 2 CH)."""
    n: Any = None
    if params is not None and getattr(params, "logic_inputs", None) is not None:
        n = params.logic_inputs
    if n is None:
        n = cfg.get("logic_inputs") or 2
    try:
        n_i = int(n)
    except (TypeError, ValueError):
        n_i = 2
    return max(1, min(_MAX_LOGIC_INPUTS, n_i))


def _levels(params: RunParams, cfg: dict[str, Any], high: float) -> list[float]:
    overlay = list(getattr(params, "levels", None) or [])
    if overlay:
        return [float(v) for v in overlay]
    raw = cfg.get("levels")
    if isinstance(raw, list) and raw:
        return [float(v) for v in raw]
    return [0.0, float(high)]


def _input_corners(n_in: int, levels: list[float]) -> list[tuple[float, ...]]:
    """2^n corners via product(levels, repeat=n). n=1 -> 2 pts; n=2 -> 4."""
    lv = [float(v) for v in levels] or [0.0, 1.0]
    n = max(1, min(_MAX_LOGIC_INPUTS, int(n_in)))
    return list(itertools.product(lv, repeat=n))


def _input_pairs(n_in: int, high: float) -> list[tuple[float, float]]:
    """Compat: first two levels of each corner as (A, B) for AWG CH1/CH2."""
    corners = _input_corners(n_in, [0.0, float(high)])
    out: list[tuple[float, float]] = []
    for c in corners:
        a = float(c[0]) if c else 0.0
        b = float(c[1]) if len(c) > 1 else 0.0
        out.append((a, b))
    return out


def _drive_inputs(instr, n_in: int, a_v: float, b_v: float = 0.0) -> bool:
    from generator_setup import setup_dc

    gen = getattr(instr, "gen", None)
    if gen is None:
        return False
    ok = bool(setup_dc(gen, 1, a_v))
    if n_in > 1:
        ok = ok and bool(setup_dc(gen, 2, b_v))
    return ok


def _drive_corner(
    instr,
    params: RunParams,
    n_in: int,
    corner: tuple[float, ...],
    *,
    tag: str,
) -> bool:
    """Drive AWG CH1/CH2 from first two corner levels. n>2 -> pause_hook rewire."""
    a_v = float(corner[0]) if corner else 0.0
    b_v = float(corner[1]) if len(corner) > 1 else 0.0
    if n_in > _AWG_DRIVE_CH:
        hook = params.pause_hook
        extra = ", ".join(
            f"IN{i + 1}={corner[i]:.3f}V" for i in range(_AWG_DRIVE_CH, n_in)
        )
        msg = (
            f"{tag}: AWG drives IN1={a_v:.3f} IN2={b_v:.3f}. "
            f"n={n_in} > {_AWG_DRIVE_CH} AWG CH -- wire {extra}, then Continue."
        )
        if hook is not None and not hook(msg):
            return False
    return _drive_inputs(instr, min(n_in, _AWG_DRIVE_CH), a_v, b_v)


def _recipe_settle_s(params: RunParams, cfg: dict, *, key: str = "voh_vol_settle_s", default: float = 1.0) -> float:
    v = getattr(params, "settle_s", None)
    if v is not None:
        return float(v)
    return float(cfg.get(key) or default)


def _settle_ua(
    instr,
    *,
    tag: str,
    last_ua: float | None,
    hook=None,
    hook_id: str = "settle",
    params: RunParams | None = None,
):
    from ate.tests.logic.eugene_cap import _dmm_ua_after_settle, _recipe_dwell_s

    return _dmm_ua_after_settle(
        instr.dmm,
        tag=tag,
        last_ua=last_ua,
        hook=hook,
        hook_id=hook_id,
        dwell_s=_recipe_dwell_s(params),
    )


def _delta_vccs(params: RunParams, cfg: dict[str, Any] | None = None) -> list[float]:
    """Overlay vcc_list, else yaml low-only list, else resolved 0..5 sweep.

    AUP vih_vil_vcc_list 1.8/2.5/3.3 must not grow to 5.0. Parameters Write still wins.
    """
    overlay = list(getattr(params, "vcc_list", None) or [])
    if overlay:
        return [float(v) for v in overlay]
    data = cfg if isinstance(cfg, dict) else _part_cfg(params)
    raw = data.get("delta_vcc_list") or data.get("vih_vil_vcc_list")
    if isinstance(raw, list) and raw:
        listed = [float(v) for v in raw]
        if listed and max(listed) < 4.5 - 1e-9:
            return listed
    return list(params.resolved_vcc_sweep())


def _run_delta_supply_current(instr, params: RunParams) -> dict[str, Any]:
    _require(instr, "PSU", "AWG", "DMM")
    from dmm_setup import dmm_setup_current
    from generator_setup import setup_dc, stop_output

    cfg = _part_cfg(params)
    n_in = _logic_inputs(cfg, params)
    ilim = _current_limit(params)
    steps = _delta_vccs(params, cfg)
    rows: list[dict[str, Any]] = []
    hook = params.progress_hook
    last_ua: float | None = None
    try:
        dmm_setup_current(instr.dmm)
        setup_dc(instr.gen, 1, 0.0)
        if n_in > 1:
            setup_dc(instr.gen, 2, 0.0)
        for vcc in steps:
            _power_cycle(instr, vcc, ilim)
            # AWG CH1 / CH2 alternate: one high (VCC), the other 0.
            for a_v, b_v, tag in ((vcc, 0.0, "CH1"), (0.0, vcc, "CH2")):
                if n_in == 1 and tag == "CH2":
                    continue
                if hook:
                    hook("delta_idd", "running", f"DeltaIDD VCC={vcc} V AWG {tag} high")
                print(f"DeltaIDD VCC={vcc} AWG {tag} high", flush=True)
                if n_in == 1:
                    if not setup_dc(instr.gen, 1, a_v):
                        continue
                elif not setup_dc(instr.gen, 1, a_v) or not setup_dc(instr.gen, 2, b_v):
                    continue
                idd = _settle_ua(
                    instr,
                    tag=f"DeltaIDD VCC={vcc} {tag}",
                    last_ua=last_ua,
                    hook=hook,
                    hook_id="delta_idd",
                    params=params,
                )
                last_ua = idd
                rows.append(
                    {
                        "VCC": vcc,
                        "INPUT_A_V": a_v,
                        "INPUT_B_V": b_v,
                        "AWG": tag,
                        "IDD_uA": idd,
                    }
                )
        if not rows:
            raise RuntimeError("delta_supply_current: no successful AWG DC setups")
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        _power_down(instr)
    last = rows[-1]
    mx = max(abs(float(r["IDD_uA"])) for r in rows)
    return {
        "summary": (
            f"DeltaIDD n={len(rows)} last={last['IDD_uA']:.3f} uA "
            f"@ {last['VCC']} V AWG {last.get('AWG')}"
        ),
        "data": {"rows": rows, "vcc_sweep": steps},
        "measurements": [{"id": "DELTA_ICC_uA", "value": mx, "unit": "uA"}],
    }


def _run_off_current(instr, params: RunParams) -> dict[str, Any]:
    """VCC=0; drive A/B via AWG and Y via PSU CH2 — 8 Ariff combos."""
    _require(instr, "PSU", "AWG", "DMM")
    from generator_setup import setup_dc, stop_output
    from psu_setup import power_on_protected

    ilim = _current_limit(params)
    combos = [
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 5.5),
        (0.0, 5.5, 0.0),
        (0.0, 5.5, 5.5),
        (5.5, 0.0, 0.0),
        (5.5, 0.0, 5.5),
        (5.5, 5.5, 0.0),
        (5.5, 5.5, 5.5),
    ]
    rows: list[dict[str, Any]] = []
    try:
        power_on_protected(instr.psu, 1, 0.0, ilim, ovp=5.6)
        time.sleep(0.5)
        for a_v, b_v, y_v in combos:
            if not setup_dc(instr.gen, 1, a_v) or not setup_dc(instr.gen, 2, b_v):
                continue
            power_on_protected(instr.psu, 2, y_v, ilim, ovp=5.6)
            time.sleep(0.5)
            idd = _avg_current_ua(instr.dmm)
            rows.append(
                {
                    "VCC": 0.0,
                    "INPUT_A_V": a_v,
                    "INPUT_B_V": b_v,
                    "OUTPUT_Y_V": y_v,
                    "IDD_uA": idd,
                }
            )
        if not rows:
            raise RuntimeError("off_current: no successful setups")
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        _power_down(instr)
    last = rows[-1]
    mx = max(abs(float(r["IDD_uA"])) for r in rows)
    return {
        "summary": f"OffCurrent n={len(rows)} worst={mx:.3f} uA last={last['IDD_uA']:.3f} uA",
        "data": {"rows": rows, "OFF_uA": mx},
        "measurements": [{"id": "OFF_uA", "value": _record_i(mx), "unit": "uA"}],
    }


def _run_input_thresholds(instr, params: RunParams) -> dict[str, Any]:
    """AWG VIN steps (default 0.01 V); return VIH/VIL + hysteresis."""
    _require(instr, "PSU", "AWG", "DMM")
    from dmm_setup import dmm_read, dmm_setup_voltage
    from generator_setup import setup_dc, stop_output

    vcc = float(params.vcc)
    ilim = _current_limit(params)
    invert = False
    mid = vcc / 2.0
    fine = _vin_step(params)
    vih = None
    vil = None
    n_vih = n_vil = 0
    try:
        _power_cycle(instr, vcc, ilim)
        dmm_setup_voltage(instr.dmm)

        def _set_vin(vin: float) -> None:
            setup_dc(instr.gen, 1, vin)

        def _read_y() -> float:
            return float(dmm_read(instr.dmm))

        vih, n_vih = _search_vin_trip(
            _set_vin,
            _read_y,
            arm=0.0,
            stop=vcc,
            mid=mid,
            vin_up=True,
            invert=invert,
            hint=0.4 * vcc,
            fine=fine,
            dwell=0.05,
        )
        vil, n_vil = _search_vin_trip(
            _set_vin,
            _read_y,
            arm=vcc,
            stop=0.0,
            mid=mid,
            vin_up=False,
            invert=invert,
            hint=0.2 * vcc,
            fine=fine,
            dwell=0.05,
        )
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        _power_down(instr)
    hyst = None
    vih = _record_v(vih)
    vil = _record_v(vil)
    if vih is not None and vil is not None:
        hyst = _record_v(float(vih) - float(vil))
    data = {"VCC": _record_v(vcc), "VIH": vih, "VIL": vil, "HYSTERESIS_V": hyst, "vin_sets": n_vih + n_vil}
    meas: list[dict[str, Any]] = []
    if vih is not None:
        meas.append({"id": "VIH_V", "value": float(vih), "unit": "V"})
    if vil is not None:
        meas.append({"id": "VIL_V", "value": float(vil), "unit": "V"})
    if hyst is not None:
        meas.append({"id": "HYST_V", "value": float(hyst), "unit": "V"})
    return {
        "summary": f"VIH={vih} VIL={vil} Hyst={hyst} @ {vcc} V",
        "data": data,
        "measurements": meas,
    }


def _run_ioff_leakage(instr, params: RunParams) -> dict[str, Any]:
    """IOFF at VCC list with 8 pin-force combos (A/B AWG, Y PSU CH2)."""
    _require(instr, "PSU", "AWG", "DMM")
    from generator_setup import setup_dc, stop_output
    from psu_setup import power_on_protected

    cfg = _part_cfg(params)
    ilim = _current_limit(params)
    vcc_values = _vcc_list(cfg, "ioff_vcc_list", [0.0, 5.5])
    combos = [
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 5.5),
        (0.0, 5.5, 0.0),
        (0.0, 5.5, 5.5),
        (5.5, 0.0, 0.0),
        (5.5, 0.0, 5.5),
        (5.5, 5.5, 0.0),
        (5.5, 5.5, 5.5),
    ]
    rows: list[dict[str, Any]] = []
    try:
        for vcc in vcc_values:
            power_on_protected(instr.psu, 1, float(vcc), ilim, ovp=5.6)
            time.sleep(0.5)
            any_ok = False
            for a_v, b_v, y_v in combos:
                ok_a = setup_dc(instr.gen, 1, a_v)
                ok_b = setup_dc(instr.gen, 2, b_v)
                power_on_protected(instr.psu, 2, y_v, ilim, ovp=5.6)
                time.sleep(0.5)
                if not (ok_a and ok_b):
                    continue
                any_ok = True
                ioff = _avg_current_ua(instr.dmm)
                rows.append(
                    {
                        "VCC": float(vcc),
                        "Voltage_A": a_v,
                        "Voltage_B": b_v,
                        "Voltage_Y": y_v,
                        "IOFF_uA": ioff,
                    }
                )
                try:
                    stop_output(instr.gen)
                except Exception:
                    pass
                power_on_protected(instr.psu, 2, 0.0, ilim)
            if not any_ok:
                raise RuntimeError(f"ioff_leakage: setup failed at VCC={vcc}")
    finally:
        _power_down(instr)
    last = rows[-1]
    mx = max(abs(float(r["IOFF_uA"])) for r in rows)
    return {
        "summary": f"IoffLeakage n={len(rows)} last={last['IOFF_uA']:.3f} uA",
        "data": {"rows": rows},
        "measurements": [{"id": "IOFF_uA", "value": mx, "unit": "uA"}],
    }


def _run_input_leakage_sweep(instr, params: RunParams) -> dict[str, Any]:
    """IDD-style leakage vs VCC list x 4 input combos (YAML-capped by default)."""
    _require(instr, "PSU", "AWG", "DMM")
    from generator_setup import setup_dc, stop_output

    from dmm_setup import dmm_setup_current

    cfg = _part_cfg(params)
    n_in = _logic_inputs(cfg, params)
    ilim = _current_limit(params)
    hook = params.progress_hook
    last_ua: float | None = None
    # Default short list; full 0..5.6/0.1 via part yaml vcc_sweep_list or overlay vcc_list
    vcc_values = _vcc_points(
        params, cfg, default=[0.0, 1.65, 3.3, 5.0, 5.5]
    )
    levels = _levels(params, cfg, 5.5)
    corners = _input_corners(n_in, levels)
    rows: list[dict[str, Any]] = []
    try:
        dmm_setup_current(instr.dmm)
        for vcc in vcc_values:
            _power_cycle(instr, float(vcc), ilim, ovp=5.6)
            for corner in corners:
                if not _drive_corner(
                    instr, params, n_in, corner, tag=f"Ileak VCC={vcc}"
                ):
                    continue
                a_v = float(corner[0]) if corner else 0.0
                b_v = float(corner[1]) if len(corner) > 1 else 0.0
                i_ua = _settle_ua(
                    instr,
                    tag=f"Ileak VCC={vcc} A={a_v}",
                    last_ua=last_ua,
                    hook=hook,
                    hook_id="ileak",
                    params=params,
                )
                last_ua = i_ua
                rows.append(
                    {
                        "VCC": float(vcc),
                        "INPUT_A_V": a_v,
                        "INPUT_B_V": b_v,
                        "corner": list(corner),
                        "ILEAK_uA": i_ua,
                    }
                )
        if not rows:
            raise RuntimeError("input_leakage_sweep: no points measured")
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        _power_down(instr)
    last = rows[-1]
    mx = max(abs(float(r["ILEAK_uA"])) for r in rows)
    return {
        "summary": f"IleakSweep n={len(rows)} last={last['ILEAK_uA']:.3f} uA",
        "data": {"rows": rows},
        "measurements": [{"id": "II_uA", "value": mx, "unit": "uA"}],
    }


def _run_supply_current_sweep(instr, params: RunParams) -> dict[str, Any]:
    """Ariff IDD vs VCC x 4 input combos. Distinct from Soo supply_current."""
    _require(instr, "PSU", "AWG", "DMM")
    from generator_setup import setup_dc, stop_output

    from dmm_setup import dmm_setup_current

    cfg = _part_cfg(params)
    n_in = _logic_inputs(cfg, params)
    ilim = _current_limit(params)
    hook = params.progress_hook
    last_ua: float | None = None
    vcc_values = _vcc_points(params, cfg, default=[1.65, 3.3, 5.0, 5.5])
    levels = _levels(params, cfg, 5.5)
    corners = _input_corners(n_in, levels)
    rows: list[dict[str, Any]] = []
    try:
        dmm_setup_current(instr.dmm)
        for vcc in vcc_values:
            _power_cycle(instr, float(vcc), ilim, ovp=5.6)
            any_ok = False
            for corner in corners:
                if not _drive_corner(
                    instr, params, n_in, corner, tag=f"SupplySweep VCC={vcc}"
                ):
                    continue
                any_ok = True
                a_v = float(corner[0]) if corner else 0.0
                b_v = float(corner[1]) if len(corner) > 1 else 0.0
                idd = _settle_ua(
                    instr,
                    tag=f"SupplySweep VCC={vcc} A={a_v}",
                    last_ua=last_ua,
                    hook=hook,
                    hook_id="idd_sweep",
                    params=params,
                )
                last_ua = idd
                rows.append(
                    {
                        "VCC": float(vcc),
                        "INPUT_A_V": a_v,
                        "INPUT_B_V": b_v,
                        "corner": list(corner),
                        "IDD_uA": idd,
                    }
                )
            if not any_ok:
                raise RuntimeError(f"supply_current_sweep: setup failed at VCC={vcc}")
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        _power_down(instr)
    last = rows[-1]
    mx = max(abs(float(r["IDD_uA"])) for r in rows)
    return {
        "summary": f"SupplySweep n={len(rows)} last={last['IDD_uA']:.3f} uA",
        "data": {"rows": rows},
        "measurements": [{"id": "ICC_uA", "value": mx, "unit": "uA"}],
    }


def _run_vih_vil(instr, params: RunParams) -> dict[str, Any]:
    """VIH/VIL at fixed VCC points plus optional 4.5-5.5 band.

    Default Ariff path: PSU CH1=VCC, AWG CH1=VIN, DMM=Y.
    rs1gt34 `vih_vil_stimulus: psu_mso`: PSU CH1=VCC, PSU CH2=A, MSO CH1=Y.
    No AWG/freq on the PSU+MSO path.
    """
    from psu_setup import OVP_ABS_MAX_V, power_on_protected

    cfg = _part_cfg(params)
    psu_mso = _use_psu_mso(cfg)
    if psu_mso:
        _require(instr, "PSU", "MSO")
    else:
        _require(instr, "PSU", "AWG", "DMM")
    n_in = _logic_inputs(cfg, params)
    invert = _y_invert(cfg)
    _set_y_invert(cfg)
    ilim = _current_limit(params)
    vcc_list = _vih_vil_vcc_points(params, cfg)
    sim = bool(getattr(getattr(instr, "psu", None), "simulated", False))
    dwell = 0.0 if sim else 0.03
    rows: list[dict[str, Any]] = []
    try:
        if not psu_mso:
            from dmm_setup import dmm_setup_voltage
            from generator_setup import setup_dc

            dmm_setup_voltage(instr.dmm)
        for vcc in vcc_list:
            vcc = float(vcc)
            ovp = min(OVP_ABS_MAX_V, max(5.6, vcc + 0.3))
            _power_cycle(instr, vcc, ilim, ovp=ovp)
            ch2_armed = False
            if psu_mso:
                _mso_setup_dc_y(instr.scope, vcc)
            elif n_in > 1:
                from generator_setup import setup_dc

                setup_dc(instr.gen, 2, vcc)
            mid = vcc / 2.0
            lim = _vih_vil_lim(vcc, cfg)
            vih_max = lim.get("vih_max") if isinstance(lim, dict) else None
            vil_min = lim.get("vil_min") if isinstance(lim, dict) else None
            fine = _vin_step(params)

            def _set_vin(vin: float) -> None:
                nonlocal ch2_armed
                if psu_mso:
                    if not ch2_armed:
                        power_on_protected(instr.psu, 2, vin, ilim, ovp=ovp)
                        ch2_armed = True
                    else:
                        # ponytail: protect already armed this VCC; VOLT-only. Do not
                        # re-run power_on_protected (1.7 s/step). Upgrade: dedicated
                        # psu_setup.set_volt if another sweep needs it.
                        instr.psu.write(f":SOUR2:VOLT {vin}")
                else:
                    from generator_setup import setup_dc

                    setup_dc(instr.gen, 1, vin)

            def _read_y() -> float:
                if psu_mso:
                    return float(_mso_vavg_ch1(instr.scope))
                from dmm_setup import dmm_read

                return float(dmm_read(instr.dmm))

            vih, n_vih = _search_vin_trip(
                _set_vin,
                _read_y,
                arm=0.0,
                stop=vcc,
                mid=mid,
                vin_up=True,
                invert=invert,
                hint=float(vih_max or (0.4 * vcc)),
                fine=fine,
                dwell=dwell,
            )
            vil, n_vil = _search_vin_trip(
                _set_vin,
                _read_y,
                arm=vcc,
                stop=0.0,
                mid=mid,
                vin_up=False,
                invert=invert,
                hint=float(vil_min or (0.2 * vcc)),
                fine=fine,
                dwell=dwell,
            )
            vin_sets = n_vih + n_vil
            vih = _record_v(vih)
            vil = _record_v(vil)
            vih_pass = None
            vil_pass = None
            if vih is not None and vih_max is not None:
                vih_pass = float(vih) <= float(vih_max)
            if vil is not None and vil_min is not None:
                vil_pass = float(vil) >= float(vil_min)
            overall = None
            if vih_pass is not None and vil_pass is not None:
                overall = "PASS" if (vih_pass and vil_pass) else "FAIL"
            elif vih_pass is False or vil_pass is False:
                overall = "FAIL"
            hyst = None
            if vih is not None and vil is not None:
                hyst = _record_v(float(vih) - float(vil))
            rows.append(
                {
                    "VCC": _record_v(vcc),
                    "VIH": vih,
                    "VIL": vil,
                    "VIH_max": vih_max,
                    "VIL_min": vil_min,
                    "HYSTERESIS_V": hyst,
                    "VIH_pass": vih_pass,
                    "VIL_pass": vil_pass,
                    "Result": overall,
                    "vin_sets": vin_sets,
                    "drive": "psu_ch2_mso_ch1" if psu_mso else "awg_dmm",
                }
            )
    finally:
        if not psu_mso:
            try:
                from generator_setup import stop_output

                stop_output(instr.gen)
            except Exception:
                pass
        _power_down(instr)
    if not rows:
        raise RuntimeError("vih_vil: no VCC points measured")
    meas: list[dict[str, Any]] = []
    for r in rows:
        tag = str(r["VCC"]).replace(".", "p")
        if r.get("VIH") is not None:
            meas.append({"id": f"VIH_{tag}V", "value": r["VIH"], "unit": "V"})
        if r.get("VIL") is not None:
            meas.append({"id": f"VIL_{tag}V", "value": r["VIL"], "unit": "V"})
    return {
        "summary": f"VIH/VIL n={len(rows)} last VCC={rows[-1]['VCC']}",
        "data": {"rows": rows, "stimulus": "psu_mso" if psu_mso else "awg_dmm"},
        "measurements": meas,
    }


def _load_meas_id(vcc: float, i_a: float, *, high: bool) -> str:
    """Build measurement ids VOH_{vcc}V / VOH_{vcc}V_100uA (or VOL_*)."""
    vtag = str(vcc).replace(".", "p")
    prefix = "VOH" if high else "VOL"
    if abs(float(i_a)) <= 0.00015:
        return f"{prefix}_{vtag}V_100uA"
    return f"{prefix}_{vtag}V"


def _run_voh_load(instr, params: RunParams) -> dict[str, Any]:
    """Functional VOH vs YAML table (PSU CH1=VCC, CH2=Vref IOH, CH3=V+).

    VOL uses a different load/Vref. Always Continue-wait before power.
    100 uA is off unless Tests checkbox / part yaml voh_100ua.
    """
    _require(instr, "PSU", "DMM")
    if not _pause_voh_vol(params, high=True):
        return {"summary": "aborted", "data": {}}
    from dmm_setup import dmm_setup_voltage
    from psu_setup import power_on_protected

    cfg = _part_cfg(params)
    n_in = _logic_inputs(cfg, params)
    invert = _y_invert(cfg)
    _set_y_invert(cfg)
    include_100ua = _include_100ua(params, cfg, "voh_load")
    load_r = _load_r_ohm(params, cfg, "voh_load")
    rows_cfg = cfg.get("voh_table") if isinstance(cfg.get("voh_table"), list) else _DEFAULT_VOH_ROWS
    want_vcc = list(getattr(params, "vcc_list", None) or [])
    if want_vcc:
        allow = {round(float(v), 6) for v in want_vcc}
        rows_cfg = [
            e
            for e in rows_cfg
            if isinstance(e, dict) and round(float(e.get("vcc", -1)), 6) in allow
        ] or rows_cfg
    rows_cfg = _skip_100ua_rows(rows_cfg, include_100ua=include_100ua, current_key="ioh_a")
    vplus = float(cfg.get("vplus_v") or 5.0)
    ilim = _current_limit(params)
    settle = _recipe_settle_s(params, cfg)
    rows: list[dict[str, Any]] = []
    try:
        power_on_protected(instr.psu, 3, vplus, ilim)
        dmm_setup_voltage(instr.dmm)
        for entry in rows_cfg:
            if not isinstance(entry, dict):
                continue
            vcc = float(entry["vcc"])
            ioh = abs(float(entry.get("ioh_a") or 0.032))
            if entry.get("vref") in (None, ""):
                vref = ioh * load_r
            else:
                vref = float(entry.get("vref") or 0.0)
            spec = float(entry["spec_min"]) if entry.get("spec_min") is not None else (vcc - 0.1)
            power_on_protected(instr.psu, 1, vcc, ilim)
            time.sleep(0.2)
            a_voh = 0.0 if invert else vcc
            _drive_inputs(instr, n_in, a_voh, a_voh)
            vcc_act = vcc
            if ioh <= 0.00015:
                time.sleep(max(0.3, settle * 0.5))
                vcc_act = _avg_voltage(instr.dmm, n=8, setup=False)
                spec = round(float(vcc_act) - 0.1, 6)
            power_on_protected(instr.psu, 2, vref, ioh, ocp=max(0.001, ioh * 2.0))
            time.sleep(settle)
            measured = _avg_voltage(instr.dmm, n=12, setup=False)
            rows.append(
                {
                    "VCC": vcc,
                    "VCC_meas": vcc_act,
                    "IOH_A": ioh,
                    "Load_R_ohm": load_r,
                    "Vref": vref,
                    "Vplus": vplus,
                    "INPUT_A_V": a_voh,
                    "Measured": measured,
                    "Spec_min": spec,
                }
            )
    finally:
        _power_down(instr)
    if not rows:
        raise RuntimeError("voh_load: empty table (tick 100 uA or check voh_table)")
    n_pass = sum(1 for r in rows if float(r["Measured"]) >= float(r["Spec_min"]))
    meas = [
        {
            "id": _load_meas_id(float(r["VCC"]), float(r["IOH_A"]), high=True),
            "value": r["Measured"],
            "unit": "V",
        }
        for r in rows
        if r.get("Measured") is not None
    ]
    return {
        "summary": f"VOH {n_pass}/{len(rows)} PASS",
        "data": {"rows": rows, "include_100ua": include_100ua, "load_r_ohm": load_r},
        "measurements": meas,
    }


def _run_vol_load(instr, params: RunParams) -> dict[str, Any]:
    """Functional VOL vs YAML table. Not the VOH load -- Vref/IOL wiring differs."""
    _require(instr, "PSU", "DMM")
    if not _pause_voh_vol(params, high=False):
        return {"summary": "aborted", "data": {}}
    from dmm_setup import dmm_setup_voltage
    from psu_setup import power_on_protected

    cfg = _part_cfg(params)
    n_in = _logic_inputs(cfg, params)
    invert = _y_invert(cfg)
    _set_y_invert(cfg)
    include_100ua = _include_100ua(params, cfg, "vol_load")
    load_r = _load_r_ohm(params, cfg, "vol_load")
    rows_cfg = cfg.get("vol_table") if isinstance(cfg.get("vol_table"), list) else _DEFAULT_VOL_ROWS
    want_vcc = list(getattr(params, "vcc_list", None) or [])
    if want_vcc:
        allow = {round(float(v), 6) for v in want_vcc}
        rows_cfg = [
            e
            for e in rows_cfg
            if isinstance(e, dict) and round(float(e.get("vcc", -1)), 6) in allow
        ] or rows_cfg
    rows_cfg = _skip_100ua_rows(rows_cfg, include_100ua=include_100ua, current_key="iol_a")
    vplus = float(cfg.get("vplus_v") or 5.0)
    ilim = _current_limit(params)
    settle = _recipe_settle_s(params, cfg)
    rows: list[dict[str, Any]] = []
    try:
        dmm_setup_voltage(instr.dmm)
        for entry in rows_cfg:
            if not isinstance(entry, dict):
                continue
            vcc = float(entry["vcc"])
            iol = abs(float(entry.get("iol_a") or 0.032))
            if entry.get("vref") in (None, ""):
                vref = max(0.0, vplus - iol * load_r)
            else:
                vref = float(entry["vref"])
            spec = float(entry["spec_max"])
            power_on_protected(instr.psu, 1, vcc, ilim)
            time.sleep(0.2)
            a_vol = vcc if invert else 0.0
            _drive_inputs(instr, n_in, a_vol, a_vol)
            power_on_protected(instr.psu, 2, vref, iol, ocp=0.05)
            time.sleep(settle)
            power_on_protected(instr.psu, 3, vplus, ilim)
            time.sleep(0.5)
            measured = _avg_voltage(instr.dmm, n=12, setup=False)
            rows.append(
                {
                    "VCC": vcc,
                    "IOL_A": iol,
                    "Load_R_ohm": load_r,
                    "Vref": vref,
                    "Vplus": vplus,
                    "INPUT_A_V": a_vol,
                    "Measured": measured,
                    "Spec_max": spec,
                }
            )
    finally:
        _power_down(instr)
    if not rows:
        raise RuntimeError("vol_load: empty table (tick 100 uA or check vol_table)")
    n_pass = sum(1 for r in rows if float(r["Measured"]) <= float(r["Spec_max"]))
    meas = [
        {
            "id": _load_meas_id(float(r["VCC"]), float(r["IOL_A"]), high=False),
            "value": r["Measured"],
            "unit": "V",
        }
        for r in rows
        if r.get("Measured") is not None
    ]
    return {
        "summary": f"VOL {n_pass}/{len(rows)} PASS",
        "data": {"rows": rows, "include_100ua": include_100ua, "load_r_ohm": load_r},
        "measurements": meas,
    }


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _pause_voh_vol(params: RunParams, *, high: bool) -> bool:
    """Every logic board: VOH and VOL setups differ. Wait before each."""
    cfg = _part_cfg(params)
    tid = "voh_load" if high else "vol_load"
    include_100ua = _include_100ua(params, cfg, tid)
    load_r = _load_r_ohm(params, cfg, tid)
    ua = "100 uA ON" if include_100ua else "100 uA OFF (10 ohm until resolder)"
    if high:
        title = (
            f"VOH load (not VOL): {ua}. Corners 8/24/32 mA through {load_r:g} ohm. "
            "PSU CH1=VCC, CH2=Vref IOH, CH3=V+, DMM on Y, AWG A=high. Then Continue."
        )
    else:
        title = (
            f"VOL load (not VOH): {ua}. Corners 8/24/32 mA through {load_r:g} ohm. "
            "PSU CH1=VCC, CH2=Vref IOL (~4.7-5.0 V), CH3=V+, DMM on Y, "
            "AWG A=low (inverter A=VCC). Then Continue."
        )
    return _pause(params, title)


def _ioz_points(cfg: dict[str, Any]) -> list[float]:
    start = float(cfg.get("ioz_vout_start") or 0.0)
    stop = float(cfg.get("ioz_vout_stop") or 5.5)
    step = float(cfg.get("ioz_vout_step") or 0.5)
    if step <= 0:
        step = 0.5
    pts: list[float] = []
    v = start
    while v <= stop + 1e-9:
        pts.append(round(v, 3))
        v += step
    if not pts or abs(pts[-1] - stop) > 1e-9:
        pts.append(round(stop, 3))
    return pts


def _run_ioz(instr, params: RunParams) -> dict[str, Any]:
    """3-state Hi-Z output leakage. See Lin RS1G126 test_ioz, pause_hook not input()."""
    _require(instr, "PSU", "DMM")
    from psu_setup import power_on_protected

    cfg = _part_cfg(params)
    ilim = _current_limit(params)
    vcc = float(cfg.get("ioz_vcc") or 3.6)
    oe_active = str(cfg.get("oe_active") or "high").strip().lower()
    oe_hiz_v = 0.0 if oe_active != "low" else vcc
    if not _pause(
        params,
        "IOZ: DMM in series with Y; OE at Hi-Z; A=GND; then Continue",
    ):
        return {"summary": "aborted", "data": {}}
    points = _ioz_points(cfg)
    rows: list[dict[str, Any]] = []
    try:
        gen = getattr(instr, "gen", None)
        if gen is not None:
            from generator_setup import setup_dc

            setup_dc(gen, 1, 0.0)
        for y_v in points:
            power_on_protected(instr.psu, 1, vcc, ilim, ovp=5.6)
            power_on_protected(instr.psu, 3, oe_hiz_v, ilim, ovp=5.6)
            power_on_protected(instr.psu, 2, y_v, ilim, ovp=5.6)
            time.sleep(0.3)
            i_ua = _avg_current_ua(instr.dmm)
            rows.append({"VCC": vcc, "Y_V": y_v, "IOZ_uA": _record_i(i_ua)})
    finally:
        _power_down(instr)
    if not rows:
        raise RuntimeError("ioz: no readings")
    mx = max(abs(float(r["IOZ_uA"])) for r in rows)
    return {
        "summary": f"IOZ n={len(rows)} worst={mx:.3f} uA @ VCC={vcc}",
        "data": {"rows": rows, "oe_hiz_v": oe_hiz_v, "oe_active": oe_active},
        "measurements": [{"id": "IOZ_uA", "value": mx, "unit": "uA"}],
    }


def _register(
    test_id: str,
    label: str,
    lab_sheet: str,
    required: frozenset[str],
    run,
) -> None:
    register(
        TestSpec(
            id=test_id,
            label=label,
            required_instruments=required,
            fixture_mode=_LOGIC_FIXTURE,
            lab_sheet=lab_sheet,
            run=run,
            dual_channel=False,
            notes=_NOTE,
        )
    )


_register(
    "delta_supply_current",
    "Delta Supply Current",
    "DeltaIDD",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_delta_supply_current,
)
_register(
    "off_current",
    "Off-State Current",
    "OffCurrent",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_off_current,
)
_register(
    "input_thresholds",
    "Input Thresholds (VIH/VIL AWG)",
    "InputThresholds",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_input_thresholds,
)
_register(
    "ioff_leakage",
    "I/O Off Leakage",
    "IoffLeakage",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_ioff_leakage,
)
_register(
    "input_leakage_sweep",
    "Input Leakage Sweep",
    "InputLeakageSweep",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_input_leakage_sweep,
)
_register(
    "supply_current_sweep",
    "Supply Current Sweep (Ariff)",
    "Supply_Current",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_supply_current_sweep,
)
_register(
    "vih_vil",
    "VIH/VIL (multi-VCC)",
    "VIH_VIL",
    frozenset({"PSU"}),
    _run_vih_vil,
)
_register(
    "voh_load",
    "VOH (loaded)",
    "VOH",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_voh_load,
)
_register(
    "vol_load",
    "VOL (loaded)",
    "VOL",
    frozenset({"PSU", "AWG", "DMM"}),
    _run_vol_load,
)
_register(
    "ioz",
    "High-Z output leakage (IOZ)",
    "IOZ",
    frozenset({"PSU", "DMM"}),
    _run_ioz,
)
