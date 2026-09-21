"""Imported TestSpec wrap for input_off_leakage (F23 / A16).

Source (reference only, not imported at runtime):
  C:/Users/OoiJianHong/LabAutomation_14.7/Eugene/RS1G07_test.py:263

Do not call input(). Use params.pause_hook for Continue gates.
Fill the measurement body when the golden recipe is ready.
"""
from __future__ import annotations

from typing import Any

from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

_FIXTURE = 'LOGIC'
_NOTE = "Imported from golden; fill measurement body. Source: C:/Users/OoiJianHong/LabAutomation_14.7/Eugene/RS1G07_test.py"


def _pause(params: RunParams, title: str) -> bool:
    hook = params.pause_hook
    if hook is None:
        return True
    return bool(hook(title))


def _run(instr, params: RunParams) -> dict[str, Any]:
    if not _pause(params, f"Input Off Leakage: confirm wiring from imported golden, then Continue"):
        return {"summary": "aborted", "data": {}}
    return {
        "summary": f"input_off_leakage imported scaffold -- fill body",
        "data": {"imported_from": 'C:/Users/OoiJianHong/LabAutomation_14.7/Eugene/RS1G07_test.py', "fn": 'test_input_off_leakage'},
    }


register(
    TestSpec(
        id='input_off_leakage',
        label='Input Off Leakage',
        required_instruments=frozenset({"PSU"}),
        fixture_mode=_FIXTURE,
        lab_sheet='Input Off Leakage',
        run=_run,
        dual_channel=False,
        notes=_NOTE,
    )
)
