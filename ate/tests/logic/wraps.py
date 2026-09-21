"""Logic TestSpec ids. Path B bodies live in cmos_prop / rs29511_* / eugene_cap / oe_timing.

Do not import repo-root logic goldens. No input().
"""
from __future__ import annotations

from contextlib import nullcontext

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.tests.logic.product_model import has_product_model, load_product_model, path_b_handoff

_LOGIC_FIXTURE = "LOGIC"
# Scale-wave UNCONFIRMED: no eugene_cap IDD body (check_logic_dc._NEXT_WAVE_SKUS).
_SUPPLY_CURRENT_LEFTOVER_DRAFT = frozenset(
    {"rs1g00", "rs1g02", "rs1g04", "rs1g86", "rs2g08", "rs2g32"}
)


def _part(params: RunParams) -> str:
    return str(getattr(params, "part", "") or "").strip().lower()


def _run_tp(instr, params: RunParams):
    pk = _part(params)
    model = load_product_model(pk) if has_product_model(pk) else None
    ctx = path_b_handoff(params, model, "tp") if model is not None else nullcontext()
    with ctx:
        if pk == "rs29511":
            from ate.tests.logic.rs29511_prop import run_tp

            return run_tp(instr, params)
        from ate.tests.logic.cmos_prop import run_tp as cmos_tp

        return cmos_tp(instr, params)


def _run_tidle(instr, params: RunParams):
    pk = _part(params)
    if pk == "rs29511":
        from ate.tests.logic.rs29511_prop import run_tidle

        return run_tidle(instr, params)
    from ate.tests.logic.cmos_prop import run_tidle as cmos_tidle

    return cmos_tidle(instr, params)


def _run_supply_current(instr, params: RunParams):
    from ate.tests.logic.eugene_cap import _IDD_PARTS, run_idd

    pk = _part(params)
    if pk == "rs29511":
        from ate.tests.logic.rs29511_dc import run_icc

        return run_icc(instr, params)
    if pk in _IDD_PARTS:
        return run_idd(instr, params)
    if pk in _SUPPLY_CURRENT_LEFTOVER_DRAFT:
        return {
            "summary": (
                f"{pk}: supply_current LEFTOVER "
                "(no eugene_cap IDD; UNCONFIRMED DRAFT numbers HOLD)"
            ),
            "data": {"status": "LEFTOVER", "greenable": False},
            "measurements": [
                {
                    "id": "ICC_uA",
                    "value": 0.0,
                    "unit": "uA",
                    "greenable": False,
                    "status": "LEFTOVER",
                }
            ],
        }
    raise RuntimeError(f"{pk}: supply_current has no Path B body (logic_tests wrap blocked)")


def _run_output_voltage(instr, params: RunParams):
    pk = _part(params)
    if pk == "rs29511":
        from ate.tests.logic.rs29511_dc import run_vout

        return run_vout(instr, params)
    raise RuntimeError(f"{pk}: output_voltage has no Path B body (logic_tests wrap blocked)")


def _run_cap_load(instr, params: RunParams):
    pk = _part(params)
    if pk == "rs29511":
        from ate.tests.logic.rs29511_dc import run_cap

        return run_cap(instr, params)
    raise RuntimeError(f"{pk}: cap_load has no Path B body (logic_tests wrap blocked)")


register(
    TestSpec(
        id="tp",
        label="Propagation Delay (TP)",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode=_LOGIC_FIXTURE,
        lab_sheet="TP",
        run=_run_tp,
        dual_channel=False,
    )
)
register(
    TestSpec(
        id="tidle",
        label="Idle Propagation Delay (TIDLE)",
        required_instruments=frozenset({"MSO", "PSU", "AWG"}),
        fixture_mode=_LOGIC_FIXTURE,
        lab_sheet="TIDLE",
        run=_run_tidle,
        dual_channel=False,
    )
)
register(
    TestSpec(
        id="supply_current",
        label="Supply Current (IDD)",
        required_instruments=frozenset({"PSU", "DMM"}),
        fixture_mode=_LOGIC_FIXTURE,
        lab_sheet="IDD",
        run=_run_supply_current,
        dual_channel=False,
    )
)
register(
    TestSpec(
        id="output_voltage",
        label="Output Voltage",
        required_instruments=frozenset({"PSU", "DMM"}),
        fixture_mode=_LOGIC_FIXTURE,
        lab_sheet="VOUT",
        run=_run_output_voltage,
        dual_channel=False,
    )
)
register(
    TestSpec(
        id="cap_load",
        label="Capacitive Load",
        required_instruments=frozenset({"DMM"}),
        fixture_mode=_LOGIC_FIXTURE,
        lab_sheet="CapLoad",
        run=_run_cap_load,
        dual_channel=False,
    )
)
