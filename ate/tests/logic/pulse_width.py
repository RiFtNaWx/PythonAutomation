"""RS1G123 monostable output pulse width. Q is a pulse, not a level follower.

Uses measure_single PWIDth (same token as RS0204 tw). RC on the board sets width.
"""
from __future__ import annotations

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams


def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook(
        "RS1G123 pulse: PSU CH1=VCC; AWG CH1=B trigger pulse; MSO CH2=Q; "
        "RC per datasheet; /RD high. Continue."
    ):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_pulse, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_single, scope_setup, set_threshold

    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    freq = 1000.0
    tw = float("nan")
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_pulse(instr.gen, 1, freq, vcc, vcc / 2.0, duty=50)
        scope_setup(instr.scope, 20e-6, vcc / 2.0)
        set_threshold(instr.scope, 2)
        tw = measure_single(instr.scope, "PWIDth", 2) * 1e9
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
        "summary": f"Q pulse={tw:.2f} ns",
        "data": {"VCC": vcc, "PULSE_ns": tw},
        "measurements": [{"id": "PULSE_ns", "value": round(tw, 3), "unit": "ns"}],
    }


register(
    TestSpec(
        id="pulse_width",
        label="Monostable Pulse Width",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="LOGIC",
        lab_sheet="TW",
        run=run,
        dual_channel=False,
        notes="RS1G123 Q pulse vs RC. Not combinational tp.",
    )
)
