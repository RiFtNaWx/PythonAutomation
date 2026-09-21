"""G201 closed-loop AC gain. MSO CHAN2 = DUT VOUT, not CHAN1=AWG.

GAIN_VV = VPP_CHAN2 / amp_cmd at 500 Hz. Not BUFFER/G11 AOL_dB.
Do not wrap opa_tests.test_ac_gain_check (CHAN1=OutB on a board where CHAN1 is VIN).
"""
from __future__ import annotations

import time
from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_WIRE = (
    "AC gain G201: research Av~201, not BUFFER/G11. "
    "PSU CH1=+Vs CH2=-Vs (both |VCC|/2). AWG CH1=IN sine, MSO CHAN1=IN CHAN2=VOUT. Continue."
)


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _meas(scope, item: str, ch: int) -> float:
    scope.write(f":MEAS:ITEM {item},CHAN{ch}")
    return float(scope.query(f":MEAS:ITEM? {item},CHAN{ch}"))


def _run(instr, params: RunParams) -> dict[str, Any]:
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import set_output_load, setup_sine, stop_output
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
    chan2_scale = max(0.02, (amp * gain) / 3.0)
    time_scale = (1.0 / freq) * 4.0 / 10.0 if freq else 0.001
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
        setup_sine(instr.gen, 1, freq, amp, 0)
        time.sleep(0.3)
        vin_vpp = _meas(scope, "VPP", 1)
        vout_vpp = _meas(scope, "VPP", 2)
        gain_vv = (vout_vpp / amp) if amp else float("nan")
        print(
            f"AC gain G201: freq={freq:g} Hz amp={amp * 1000:.3f} mVpp "
            f"VIN={vin_vpp:.6f} V VOUT={vout_vpp:.6f} V GAIN={gain_vv:.2f} V/V "
            f"(CHAN2, Av~{gain:g})",
            flush=True,
        )
        return {
            "summary": f"GAIN={gain_vv:.2f} V/V (CHAN2, cmd {gain:g})",
            "data": {
                "g201_ac": True,
                "gain": gain,
                "freq_hz": freq,
                "amp_vpp": amp,
                "vin_vpp": vin_vpp,
                "vout_vpp": vout_vpp,
                "gain_vv": gain_vv,
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
        id="ac_gain_check",
        label="AC Gain Check",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="G201",
        lab_sheet="VOS",
        run=_run,
        notes="RESEARCH G201 Av~201. MSO CHAN2=VOUT. Closed-loop GAIN_VV, not AOL_dB.",
    )
)
