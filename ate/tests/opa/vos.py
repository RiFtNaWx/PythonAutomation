"""VOS DC sweep on G201 closed-loop. MSO CHAN2 = DUT VOUT, not CHAN1=AWG.

VOUT = G*(VIN + Vos). Null Vos_mV = -intercept/slope * 1000.
Do not wrap the golden CHAN1 AWG sweep. Not BUFFER AOL_dB.
"""
from __future__ import annotations

import time
from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_WIRE = (
    "VOS G201: research gain module (Av~201), not BUFFER/G11. "
    "PSU CH1=+Vs CH2=-Vs (both |VCC|/2). AWG CH1=IN DC, MSO CHAN1=IN CHAN2=VOUT. Continue."
)


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    n = len(xs)
    if n < 2:
        raise RuntimeError("VOS: need at least 2 sweep points")
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xx = sum(x * x for x in xs)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        raise RuntimeError("VOS: zero variance in VIN")
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot else float("nan")
    return slope, intercept, r_squared


def _meas(scope, item: str, ch: int) -> float:
    scope.write(f":MEAS:ITEM {item},CHAN{ch}")
    return float(scope.query(f":MEAS:ITEM? {item},CHAN{ch}"))


def _run(instr, params: RunParams) -> dict[str, Any]:
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import enable_output, set_offset, set_output_load, setup_dc, stop_output
    from psu_setup import power_off, power_on_protected

    if not _pause(params, _WIRE):
        return {"summary": "aborted", "data": {}}
    gain = float(params.gain) if params.gain and float(params.gain) >= 50.0 else 201.0
    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    v_half = vcc / 2.0
    ovp = v_half + 0.3
    ocp = ilim + 0.1
    vin_mV = [round(-5.0 + i * 0.1, 4) for i in range(101)]
    max_vout = abs(vin_mV[-1]) * gain * 1e-3
    chan2_scale = max(0.02, max_vout / 3.0)
    vin_v: list[float] = []
    vout_v: list[float] = []
    try:
        power_on_protected(instr.psu, 1, v_half, ilim, ovp=ovp, ocp=ocp)
        power_on_protected(instr.psu, 2, v_half, ilim, ovp=ovp, ocp=ocp)
        set_output_load(instr.gen, 1, "INF")
        scope = instr.scope
        scope.write(":CHAN1:DISP ON")
        scope.write(":CHAN2:DISP ON")
        scope.write(":CHAN1:COUP DC")
        scope.write(":CHAN2:COUP DC")
        scope.write(":CHAN1:SCAL 0.002")
        scope.write(f":CHAN2:SCAL {chan2_scale}")
        scope.write(":CHAN1:OFFS 0")
        scope.write(":CHAN2:OFFS 0")
        scope.write(":TIM:SCAL 0.01")
        scope.write(":TRIGger:SWEep AUTO")
        scope.write(":TRIGger:MODE EDGE")
        scope.write(":TRIGger:EDGE:SOURce CHAN1")
        scope.write(":SYSTem:KEY:PRESs MOFF")
        for idx, mv in enumerate(vin_mV):
            vin = mv / 1000.0
            if idx == 0:
                setup_dc(instr.gen, 1, vin)
                enable_output(instr.gen, 1)
                time.sleep(0.3)
                _meas(scope, "VAVG", 2)
            else:
                set_offset(instr.gen, 1, vin)
                enable_output(instr.gen, 1)
                time.sleep(0.3)
            vin_v.append(vin)
            vout_v.append(_meas(scope, "VAVG", 2))
        slope, intercept, r2 = _linear_fit(vin_v, vout_v)
        vos_mV = (-intercept / slope * 1000.0) if slope else float("nan")
        if vos_mV == vos_mV and abs(vos_mV) < 1e-9:
            vos_mV = 0.0
        if vos_mV != vos_mV:
            meas: list[dict[str, Any]] = []
        else:
            meas = [{"id": "VOS_mV", "value": vos_mV, "unit": "mV"}]
        print(
            f"Linear fit: slope={slope:.4f} V/V, intercept={intercept:.6f} V, "
            f"R2={r2:.6f}, VOS~{vos_mV:.4f} mV (CHAN2 VOUT, G={gain:g})",
            flush=True,
        )
        return {
            "summary": f"VOS={vos_mV:.4f} mV  slope={slope:.2f}  R2={r2:.6f}",
            "data": {
                "g201_vos": True,
                "gain": gain,
                "slope": slope,
                "intercept": intercept,
                "r_squared": r2,
                "vos_mV": vos_mV,
                "n": len(vin_v),
            },
            "fit": {
                "slope": slope,
                "intercept": intercept,
                "r_squared": r2,
                "vos_mV": vos_mV,
            },
            "lab_sheet": "VOS",
            "measurements": meas,
        }
    finally:
        try:
            stop_output(instr.gen)
        except Exception:
            pass
        try:
            power_off(instr.psu)
        except Exception:
            pass


register(
    TestSpec(
        id="vos_sweep",
        label="VOS DC Sweep",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="G201",
        lab_sheet="VOS",
        run=_run,
        notes="RESEARCH G201 Av~201. MSO CHAN2=VOUT. Not BUFFER AOL. Not CHAN1=AWG.",
    )
)
