"""Power-on time: MSO delay from VCC rail (CH1) to VOUT (CH2).

Not a screenshot. No datasheet min/max in the RS62X extract -- stamp only.
"""
from __future__ import annotations

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams


def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook(
        "PowerOn: BUFFER DUT; PSU CH1=+Vs/2 CH2=-Vs/2; AWG CH1 DC 0 V; "
        "MSO CH1=VCC rail CH2=VOUT. Continue."
    ):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_dc, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    rail = vcc / 2.0
    t_ns = float("nan")
    try:
        setup_dc(instr.gen, 1, 0.0)
        power_on_protected(instr.psu, 1, rail, ilim)
        power_on_protected(instr.psu, 2, rail, ilim)
        scope_setup(instr.scope, 20e-6, rail / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        t_ns = abs(measure_delay(instr.scope, "RRDelay", 1, 2)) * 1e9
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
        "summary": f"PowerOn={t_ns:.1f} ns (rail to VOUT)",
        "data": {"VCC": vcc, "POWERON_ns": t_ns},
        "measurements": [{"id": "POWERON_ns", "value": round(t_ns, 3), "unit": "ns"}],
    }


register(
    TestSpec(
        id="power_on_time",
        label="Power On Time",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="BUFFER",
        lab_sheet="PowerOnTime",
        run=run,
        dual_channel=False,
        notes="MSO RRDelay VCC to VOUT. No invented min/max.",
        fixed_steps=[{"id": "measure", "label": "Measure rail-to-VOUT delay", "phase": "measure"}],
    )
)
