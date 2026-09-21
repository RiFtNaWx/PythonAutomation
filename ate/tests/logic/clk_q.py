"""RS1G74 clock-to-Q. Q follows D only on CLK edge -- not combinational tp.

Same measure_delay FFDelay/RRDelay as logic tpd. Do not copy RS1G08 AND wiring.
"""
from __future__ import annotations

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams


def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    pk = str(getattr(params, "part", "") or "").lower()
    if pk == "rs164":
        msg = (
            "RS164 CLK->Q0: PSU CH1=VCC; strap B=/MR=VCC; AWG CH1=CLK CH2=A=VCC; "
            "MSO CH1=CLK CH2=Q0. A AND B must both be high to shift a 1. Continue."
        )
    else:
        msg = (
            "RS1G74 CLK->Q: PSU CH1=VCC; AWG CH1=CLK 0..VCC; AWG CH2=D=VCC; "
            "MSO CH1=CLK CH2=Q; /CLR and /PRE high. Continue."
        )
    if hook is not None and not hook(msg):
        return {"summary": "aborted", "data": {}}
    if getattr(instr, "psu", None) is None or getattr(instr, "gen", None) is None:
        raise RuntimeError("Missing instruments: PSU, AWG")
    if getattr(instr, "scope", None) is None:
        raise RuntimeError("Missing instruments: MSO")
    from generator_setup import setup_dc, setup_square, stop_output
    from psu_setup import power_off, power_on_protected
    from scope_setup import measure_delay, scope_setup, set_threshold

    vcc = float(params.vcc or 5.0)
    ilim = float(params.current_limit_a or 0.1)
    freq = 400000.0
    try:
        power_on_protected(instr.psu, 1, vcc, ilim)
        setup_dc(instr.gen, 2, vcc)
        setup_square(instr.gen, 1, freq, vcc, vcc / 2.0)
        scope_setup(instr.scope, 50e-9, vcc / 2.0)
        set_threshold(instr.scope, 1)
        set_threshold(instr.scope, 2)
        t_hl = measure_delay(instr.scope, "FFDelay", 1, 2) * 1e9
        t_lh = measure_delay(instr.scope, "RRDelay", 1, 2) * 1e9
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
        "summary": f"CLK->Q tHL={t_hl:.2f} ns tLH={t_lh:.2f} ns",
        "data": {"VCC": vcc, "CLKQ_PHL_ns": t_hl, "CLKQ_PLH_ns": t_lh},
        "measurements": [
            {"id": "CLKQ_PHL_ns", "value": round(t_hl, 3), "unit": "ns"},
            {"id": "CLKQ_PLH_ns", "value": round(t_lh, 3), "unit": "ns"},
        ],
    }


register(
    TestSpec(
        id="clk_q",
        label="Clock-to-Q (DFF)",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode="LOGIC",
        lab_sheet="TP",
        run=run,
        dual_channel=False,
        notes="CLK to Q (DFF or shift Q0). D/A held high. Not AND-gate tp.",
    )
)
