"""G201 AC+DC Vin sweep. MSO CHAN2 = DUT VOUT, not CHAN1=AWG.

GAIN_VV = mean(VPP_CHAN2 / amp_cmd). Slope of VAVG_CHAN2 vs VIN is leftover
proof of Av (same board as vos_sweep). Not AOL_dB. No research xlsx write.
"""
from __future__ import annotations

import time
from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.tests.opa.vos import _linear_fit, _meas, _pause

_WIRE = (
    "AC Vin G201: research Av~201, not BUFFER/G11. "
    "PSU CH1=+Vs CH2=-Vs. AWG CH1=IN sine+offset, MSO CHAN1=IN CHAN2=VOUT. Continue."
)


def _run(instr, params: RunParams) -> dict[str, Any]:
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import set_offset, set_output_load, setup_sine, stop_output
    from psu_setup import power_off, power_on_protected

    if not _pause(params, _WIRE):
        return {"summary": "aborted", "data": {}}
    gain = float(params.gain) if params.gain and float(params.gain) >= 50.0 else 201.0
    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    amp = float(params.amp_vpp or 0.004)
    freq = float(params.freq_hz or 500.0)
    v_half = vcc / 2.0
    ovp = v_half + 0.3
    ocp = ilim + 0.1
    vin_mV = [round(-5.0 + i * 0.1, 4) for i in range(101)]
    max_dc = abs(vin_mV[-1]) * gain * 1e-3
    chan2_scale = max(0.02, (max_dc + amp * gain) / 3.0)
    time_scale = (1.0 / freq) * 4.0 / 10.0 if freq else 0.001
    vin_v: list[float] = []
    vout_v: list[float] = []
    gain_ratios: list[float] = []
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
        scope.write(f":TIM:SCAL {time_scale}")
        scope.write(":TRIGger:SWEep AUTO")
        scope.write(":TRIGger:MODE EDGE")
        scope.write(":TRIGger:EDGE:SOURce CHAN1")
        scope.write(":SYSTem:KEY:PRESs MOFF")
        for idx, mv in enumerate(vin_mV):
            vin = mv / 1000.0
            if idx == 0:
                setup_sine(instr.gen, 1, freq, amp, vin)
                time.sleep(0.3)
                _meas(scope, "VAVG", 2)
            else:
                set_offset(instr.gen, 1, vin)
                time.sleep(0.3)
            vavg = _meas(scope, "VAVG", 2)
            vpp = _meas(scope, "VPP", 2)
            vin_v.append(vin)
            vout_v.append(vavg)
            if amp:
                gain_ratios.append(vpp / amp)
        slope, intercept, r2 = _linear_fit(vin_v, vout_v)
        gain_vv = (sum(gain_ratios) / len(gain_ratios)) if gain_ratios else float("nan")
        print(
            f"AC Vin G201: slope={slope:.4f} V/V R2={r2:.6f} "
            f"GAIN={gain_vv:.2f} V/V (CHAN2 VPP/amp, Av~{gain:g})",
            flush=True,
        )
        return {
            "summary": f"GAIN={gain_vv:.2f} V/V slope={slope:.2f}",
            "data": {
                "g201_ac": True,
                "gain": gain,
                "slope": slope,
                "intercept": intercept,
                "r_squared": r2,
                "gain_vv": gain_vv,
                "n": len(vin_v),
            },
            "measurements": [{"id": "GAIN_VV", "value": gain_vv, "unit": "V/V"}],
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
        id="ac_vin_sweep",
        label="AC Vin Sweep (-5...+5 mV)",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="G201",
        lab_sheet="VOS",
        run=_run,
        notes="RESEARCH G201 Av~201. MSO CHAN2=VOUT. Closed-loop GAIN_VV, not AOL_dB.",
    )
)
