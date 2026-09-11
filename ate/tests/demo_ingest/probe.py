"""Tiny local ATE family for ingest dry-test (not opamp)."""
from ate.core.registry import TestSpec, register


def _run(_instr, _params):
    return {"summary": "demo_ingest ok"}


register(
    TestSpec(
        id="demo_probe",
        label="Demo probe",
        required_instruments=frozenset(),
        fixture_mode="LOGIC",
        lab_sheet="Demo",
        run=_run,
        dual_channel=False,
        notes="Local-folder ingest dry-test",
    )
)
