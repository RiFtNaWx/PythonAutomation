"""Fail-closed: DEMO/SIM runs Logic, Analog SW, Level, Power, OpAmp slew.

Run: python -m ate.core.check_demo_families
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path


def main() -> int:
    errors: list[str] = []
    root = Path(__file__).resolve().parents[2]
    runner = (root / "ate" / "core" / "runner.py").read_text(encoding="utf-8")
    js = (root / "ate" / "ui" / "web" / "app.js").read_text(encoding="utf-8")
    worker = (root / "ate" / "worker" / "server.py").read_text(encoding="utf-8")

    if "def claim_async_run" not in runner:
        errors.append("runner must claim busy before the DEMO thread starts")
    if "time.sleep = lambda" not in runner:
        errors.append("SIM run_sequence must skip time.sleep")
    if "waitForRunComplete(epoch0)" not in js or "run_epoch" not in js:
        errors.append("app.js must wait for run_epoch before treating DEMO as done")
    if "claim_async_run" not in worker:
        errors.append("run_sequence_async must call claim_async_run")

    tmp = Path(tempfile.mkdtemp(prefix="ate_demo_fam_"))
    from ate.core import database as dbmod
    from ate.core import paths as pathmod
    from ate.core.database import set_context
    from ate.core.runner import ATECore, RunParams

    old_root = pathmod.TEST_DB_ROOT
    old_db = dbmod.TEST_DB_ROOT
    old_sleep = time.sleep
    time.sleep = lambda *_a, **_k: None
    pathmod.TEST_DB_ROOT = tmp / "#Test_Database"
    dbmod.TEST_DB_ROOT = pathmod.TEST_DB_ROOT
    core = None
    cases = (
        ("logic", "Logic", "RS1G07", "SOT23", "rs1g07", ["cin", "cpd"]),
        ("switch", "AnalogSwitch", "RS2323", "MSOP", "rs2323", ["iplus"]),
        ("level", "Level", "RS0204", "TSSOP14", "rs0204", ["vih"]),
        ("power", "Power", "RS3213", "SOT23-5", "rs3213", ["iq"]),
        ("opamp", "OpAmp", "RS622", "TTSOP8", "rs622", ["slew"]),
    )
    try:
        pathmod.TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
        core = ATECore(emit=lambda _e: None)
        for family, component, part, package, part_key, ids in cases:
            set_context(
                component=component,
                part=part,
                package=package,
                operator="Eugene",
                version="Version_1",
                model=part,
                part_key=part_key,
                sample_size=1,
            )
            core.load_family(family)
            core.open_session(sim=True)
            rp = RunParams(
                vcc=3.3 if family not in ("power", "opamp") else 5.0,
                vccb=3.3 if part_key == "rs0204" else None,
                part=part_key,
                dut_indices=[1],
                channels=["CHA"],
                current_limit_a=0.1,
                auto_continue=True,
            )
            results = core.run_sequence(ids, rp)
            if core.last_run_error:
                errors.append(f"{part} run_error: {core.last_run_error}")
            got = {r.test_id: r for r in results}
            for tid in ids:
                row = got.get(tid)
                if row is None:
                    errors.append(f"{part} missing {tid}")
                elif not row.success:
                    errors.append(f"{part} {tid} failed: {row.error or row.summary}")
            recs = list(pathmod.TEST_DB_ROOT.rglob("records/*.json"))
            if not any(ids[0] in p.name for p in recs):
                errors.append(f"{part} must write records/ for {ids[0]}")
            core.close_session()
    except Exception as exc:
        errors.append(f"DEMO families crashed: {exc}")
    finally:
        time.sleep = old_sleep
        pathmod.TEST_DB_ROOT = old_root
        dbmod.TEST_DB_ROOT = old_db
        try:
            if core is not None:
                core.close_session()
        except Exception:
            pass

    if errors:
        print("FAIL check_demo_families:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        "OK check_demo_families: SIM cin+cpd, iplus, vih, iq, slew; "
        "busy claimed before thread; sleep skipped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
