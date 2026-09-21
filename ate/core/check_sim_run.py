"""Fail-closed: START plan must not UnboundLocalError get_context; SIM PyVISA runs.

Run: python -m ate.core.check_sim_run
"""
from __future__ import annotations

import ast
import sys
import tempfile
import time
from pathlib import Path


def _assert_no_local_get_context() -> None:
    src = Path(__file__).resolve().parent / "runner.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "run_sequence":
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.ImportFrom):
                names = [a.name for a in child.names]
                if "get_context" in names:
                    raise AssertionError(
                        "run_sequence must not re-import get_context "
                        "(UnboundLocalError: Building plan stuck, PSU never ON)"
                    )


def _assert_no_rs622_worker_fallback() -> None:
    src = (
        Path(__file__).resolve().parents[2] / "ate" / "worker" / "server.py"
    ).read_text(encoding="utf-8")
    if 'or "rs622"' in src:
        raise AssertionError(
            'worker must not default part to rs622 (Logic START would stamp RS622 limits)'
        )


def _assert_sim_skips_photo_paste() -> None:
    src = (Path(__file__).resolve().parent / "database.py").read_text(encoding="utf-8")
    if "paste_session_photos" not in src:
        raise AssertionError("end_session must still paste photos on live USB")
    if 'startswith("SIM::")' not in src and "startswith('SIM::')" not in src:
        raise AssertionError("end_session must detect SIM:: instrument_map")
    if "if not sim:" not in src:
        raise AssertionError("end_session must skip photo paste when SIM")


def _assert_sim_measure(errors: list[str]) -> None:
    from ate.instruments.sim import SimResource, reset_bus
    from psu_setup import power_on_protected

    reset_bus()
    awg = SimResource("AWG")
    scope = SimResource("MSO")
    dmm = SimResource("DMM")
    dmm.dmm_func = "CURR"
    i_off = float(dmm.query(":READ?"))
    if i_off >= 1e-7:
        errors.append(f"SIM DMM must not assume PSU powered, got {i_off}")
    awg.write(":SOUR1:APPL:SQU 1000,1,0,0")
    awg.write(":OUTP1 ON")
    cnt = float(scope.query(":MEASure:STATistic:ITEM? COUNt,PSLewrate,CHAN2"))
    vpp = float(scope.query(":MEASure:STATistic:ITEM? CURRent,VPP,CHAN1"))
    if cnt < 80:
        errors.append(f"SIM COUNT must be >=80 after AWG ON, got {cnt}")
    if abs(vpp - 1.0) > 0.05:
        errors.append(f"SIM CHAN1 VPP must follow AWG 1 Vpp, got {vpp}")
    scope.write("TIMebase:MAIN:SCAle 1e-6")
    d_ns = float(scope.query(":MEASure:STATistic:ITEM? AVERages,RRDelay,CHAN1,CHAN2"))
    if abs(d_ns - 50e-9) > 10e-9:
        errors.append(f"SIM ns-window DELAY must be ~50 ns, got {d_ns}")
    scope.write("TIMebase:MAIN:SCAle 50e-6")
    d_us = float(scope.query(":MEASure:STATistic:ITEM? AVERages,RRDelay,CHAN1,CHAN2"))
    if abs(d_us - 100e-6) > 20e-6:
        errors.append(f"SIM us-window DELAY must be ~100 us (tIDLE class), got {d_us}")
    scope.write("TIMebase:MAIN:SCAle 1e-6")
    awg.write(":OUTP1 OFF")
    cnt_off = float(scope.query(":MEASure:STATistic:ITEM? COUNt,PSLewrate,CHAN2"))
    if cnt_off >= 10:
        errors.append(f"SIM COUNT must drop when AWG OFF, got {cnt_off}")
    psu = SimResource("PSU")
    power_on_protected(psu, 1, 5.0, 0.1)
    static = float(dmm.query(":READ?"))
    if not (1e-8 < static < 2e-6):
        errors.append(f"SIM static DMM current should be ~0.8 uA with PSU ON, got {static}")
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    awg.write(":SOUR1:APPL:DC DEF,DEF,0")
    awg.write(":OUTP1 ON")
    v_low = float(dmm.query(":READ?"))
    if v_low > 0.2:
        errors.append(f"SIM buffer VOL must be low when VIN=0, got {v_low}")
    awg.write(":SOUR1:APPL:DC DEF,DEF,5")
    v_high = float(dmm.query(":READ?"))
    if abs(v_high - 5.0) > 0.25:
        errors.append(f"SIM buffer VOH must follow VCC when VIN high, got {v_high}")
    psu.volt[1] = 2.0
    psu.volt[2] = 0.08
    psu.outp[1] = "ON"
    psu.outp[2] = "ON"
    psu._sync_psu_bus()
    awg.write(":SOUR1:APPL:DC DEF,DEF,2")
    v_load = float(dmm.query(":READ?"))
    if abs(v_load - 2.0) > 0.25:
        errors.append(f"SIM Ariff VOH must follow VCC not CH2 Vref, got {v_load}")
    psu.volt[1] = 1.8
    psu.volt[2] = 3.3
    psu._sync_psu_bus()
    awg.write(":SOUR1:APPL:DC DEF,DEF,1.8")
    v_xlat = float(dmm.query(":READ?"))
    if abs(v_xlat - 3.3) > 0.25:
        errors.append(f"SIM RS0204 VOH must follow VCCB, got {v_xlat}")
    psu.outp[2] = "OFF"
    psu.volt[1] = 5.0
    psu._sync_psu_bus()
    dmm.write(":SENS:FUNC 'CURR:DC'")
    awg.write(":SOUR1:APPL:DC DEF,DEF,0")
    awg.write(":OUTP1 ON")
    i_dc0 = float(dmm.query(":READ?"))
    awg.write(":SOUR1:APPL:DC DEF,DEF,5")
    i_dc5 = float(dmm.query(":READ?"))
    if i_dc5 <= i_dc0:
        errors.append(
            f"SIM DC VIN high must raise DMM current vs VIN=0, got {i_dc0} then {i_dc5}"
        )
    awg.write(":OUTP1 OFF")
    psu.volt[1] = 1.65
    psu._sync_psu_bus()
    i_lowv = float(dmm.query(":READ?"))
    psu.volt[1] = 5.5
    psu._sync_psu_bus()
    i_highv = float(dmm.query(":READ?"))
    if i_highv <= i_lowv:
        errors.append(f"SIM ICC must rise with VCC, got {i_lowv} then {i_highv}")
    psu.volt[1] = 3.3
    psu._sync_psu_bus()
    awg.write(":SOUR1:APPL:DC DEF,DEF,3.3")
    awg.write(":OUTP1 ON")
    awg.write(":SOUR2:APPL:DC DEF,DEF,0")
    awg.write(":OUTP2 ON")
    i_a = float(dmm.query(":READ?"))
    awg.write(":SOUR1:APPL:DC DEF,DEF,0")
    awg.write(":SOUR2:APPL:DC DEF,DEF,3.3")
    i_b = float(dmm.query(":READ?"))
    if abs(i_a - i_b) < 1e-9:
        errors.append(f"SIM CH1 vs CH2 DC must differ (DeltaICC), got {i_a} {i_b}")
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    psu.volt[1] = 5.0
    psu._sync_psu_bus()
    awg.write(":SOUR1:APPL:SQU 1000,5,2.5,0")
    awg.write(":OUTP1 ON")
    awg.write(":SOUR2:APPL:DC DEF,DEF,5")
    awg.write(":OUTP2 ON")
    q_hi = float(dmm.query(":READ?"))
    awg.write(":SOUR2:APPL:DC DEF,DEF,0")
    q_lo = float(dmm.query(":READ?"))
    if abs(q_hi - 5.0) > 0.25:
        errors.append(f"SIM Q7 with A=VCC must be high, got {q_hi}")
    if q_lo > 0.2:
        errors.append(f"SIM Q7 with A=0 after CLK must be low, not VCC, got {q_lo}")
    dmm.write(":SENS:FUNC 'CURR:DC'")
    awg.write(":OUTP1 OFF")
    awg.write(":OUTP2 OFF")
    psu.outp[2] = "ON"
    psu.outp[3] = "ON"
    psu.volt[2] = 1.8
    psu.volt[3] = 0.0
    psu._sync_psu_bus()
    i_ioz = float(dmm.query(":READ?"))
    psu.outp[2] = "OFF"
    psu.outp[3] = "OFF"
    psu._sync_psu_bus()
    i_icc = float(dmm.query(":READ?"))
    if not (i_ioz < i_icc * 0.5 and i_ioz < 5e-7):
        errors.append(f"SIM IOZ (CH2+CH3) must be Hi-Z vs ICC, ioz={i_ioz} icc={i_icc}")
    psu.volt[1] = 3.3
    psu._sync_psu_bus()
    awg.write(":SOUR1:APPL:SQU 1000000,3.3,1.65,0")
    awg.write(":OUTP1 ON")
    i_1m = float(dmm.query(":READ?"))
    awg.write(":SOUR1:APPL:SQU 10000000,3.3,1.65,0")
    i_10m = float(dmm.query(":READ?"))
    if i_1m < 5e-6 or (i_10m / i_1m) < 6:
        errors.append(f"SIM I=CVf: 10 MHz / 1 MHz ~10x, got {i_1m} {i_10m}")
    awg.write(":SOUR1:APPL:SQU 1000,1,0,0")
    pwid = float(scope.query(":MEASure:STATistic:ITEM? CURRent,PWIDth,CHAN1"))
    if abs(pwid - 5e-4) > 5e-5:
        errors.append(f"SIM CHAN1 PWID must be 0.5/freq at 1 kHz, got {pwid}")
    pwid2 = float(scope.query(":MEASure:STATistic:ITEM? CURRent,PWIDth,CHAN2"))
    if abs(pwid2 - 5e-4) > 5e-5:
        errors.append(
            f"SIM CHAN2 PWID must follow CH1 0.5/f not 500 ns dummy, got {pwid2}"
        )
    awg.write(":OUTP1 OFF")
    psu.outp[1] = "ON"
    psu.outp[2] = "ON"
    psu.volt[1] = 3.3
    psu.volt[2] = 0.0
    psu._sync_psu_bus()
    dmm.write(":SENS:FUNC 'VOLT:DC'")
    y_low = float(dmm.query(":READ?"))
    psu.volt[2] = 3.3
    psu._sync_psu_bus()
    y_high = float(dmm.query(":READ?"))
    psu.volt[2] = 0.0
    psu._sync_psu_bus()
    y_back = float(dmm.query(":READ?"))
    if y_low > 0.5:
        errors.append(f"SIM Y must be LOW when PSU CH2=0, got {y_low}")
    if abs(y_high - 3.3) > 0.25:
        errors.append(f"SIM Y must follow VCC when PSU CH2=VCC, got {y_high}")
    if y_back > 0.5:
        errors.append(f"SIM Schmitt Y must fall LOW at CH2=0, got {y_back}")
    psu.outp[2] = "OFF"
    psu._sync_psu_bus()
    dmm.write(":SENS:FUNC 'CURR:DC'")
    psu.volt[1] = 5.0
    psu._sync_psu_bus()
    awg.write(":SOUR1:APPL:SQU 10000000,5,2.5,0")
    awg.write(":OUTP1 ON")
    dyn = float(dmm.query(":READ?"))
    if abs(dyn - 300e-6) > 50e-6:
        errors.append(f"SIM 5V 10MHz DMM current should be ~300 uA (6pF Cpd), got {dyn}")
    awg.write(":SOUR1:APPL:SIN 1000,0.05,0,0")
    v1k = float(scope.query(":MEAS:ITEM? VPP,CHAN2"))
    awg.write(":SOUR1:APPL:SIN 700000,0.05,0,0")
    v700 = float(scope.query(":MEAS:ITEM? VPP,CHAN2"))
    if not (v700 < v1k * 0.75):
        errors.append(f"SIM GBW CHAN2 must roll off, 1kHz={v1k} 700kHz={v700}")
    awg.write(":SOUR1:APPL:SIN 1000,6,0,0")
    v_npr = float(scope.query(":MEAS:ITEM? VPP,CHAN2"))
    if v_npr > 12.0:
        errors.append(f"SIM BUFFER NPR CHAN2 must not be G11*6 V, got {v_npr}")
    ov = float(scope.query(":MEAS:ITEM? OVERSHOOT,CHAN2"))
    if abs(ov - 0.12) < 1e-9:
        errors.append("SIM OVERSHOOT must not be the 0.12 unknown-item dummy")
    per = float(scope.query(":MEAS:ITEM? PERIod,CHAN1"))
    if abs(per - 0.12) < 1e-9 or abs(per) < 1e10:
        errors.append(
            f"SIM unknown ITEM must be Rigol invalid not 0.12 dummy, got {per}"
        )
    awg.write(":SOUR1:APPL:DC DEF,DEF,-0.005")
    awg.write(":OUTP1 ON")
    vavg0 = float(scope.query(":MEAS:ITEM? VAVG,CHAN1"))
    awg.write(":SOUR1:VOLT:OFFS 0.005")
    vavg1 = float(scope.query(":MEAS:ITEM? VAVG,CHAN1"))
    if abs(vavg0 - (-0.005)) > 0.001:
        errors.append(f"SIM VAVG must follow DC level, got {vavg0}")
    if abs(vavg1 - 0.005) > 0.001:
        errors.append(f"SIM VOLT:OFFS must move VAVG, got {vavg1}")
    awg.write(":OUTP1 OFF")
    psu.volt[1] = 1.8
    psu.volt[2] = 3.3
    psu.outp[1] = "ON"
    psu.outp[2] = "ON"
    psu._sync_psu_bus()
    awg.write(":SOUR1:APPL:SQU 1000000,1.8,0.9,0")
    awg.write(":OUTP1 ON")
    awg.write(":SOUR2:APPL:DC DEF,DEF,1.8")
    awg.write(":OUTP2 ON")
    y_vpp = float(scope.query(":MEAS:ITEM? VPP,CHAN2"))
    if abs(y_vpp - 3.3) > 0.35:
        errors.append(
            f"SIM CHAN2 with OE DC must be translator B VPP~VCCB, got {y_vpp}"
        )
    rt = float(scope.query(":MEASure:STATistic:ITEM? AVERages,RTime,CHAN2"))
    if not (1e-9 < rt < 1e-6):
        errors.append(f"SIM RTime must be MSO-ns class not 0.12 s, got {rt}")
    awg.write(":OUTP2 OFF")
    awg.write(":OUTP1 OFF")
    psu.outp[2] = "OFF"
    psu._sync_psu_bus()
    try:
        from ate.drivers.mso5072 import wait_slew_statistics

        wait_slew_statistics(SimResource("MSO"), "PSLewrate", timeout_s=6.0)
    except Exception as exc:
        errors.append(f"SIM wait_slew must not raise on fake scope: {exc}")


def main() -> int:
    errors: list[str] = []
    try:
        _assert_no_local_get_context()
        _assert_no_rs622_worker_fallback()
        _assert_sim_skips_photo_paste()
    except AssertionError as exc:
        errors.append(str(exc))

    from ate.instruments.sim import SimResource
    from psu_setup import power_on_protected

    old_sleep = time.sleep
    time.sleep = lambda *_a, **_k: None

    psu = SimResource("PSU")
    try:
        power_on_protected(psu, 1, 3.3, 0.1)
        if psu.outp.get(1) != "ON":
            errors.append("SIM PSU CH1 did not turn ON")
        _assert_sim_measure(errors)
        from ate.instruments.sim import loopback_check

        lb = loopback_check()
        if not lb.get("ok"):
            errors.append(f"SIM loopback failed: {lb}")
    except Exception as exc:
        errors.append(f"SIM loopback/setup crashed: {exc}")
        time.sleep = old_sleep
        print("FAIL check_sim_run:")
        for e in errors:
            print(f"  - {e}")
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="ate_sim_run_"))
    from ate.core import database as dbmod
    from ate.core import paths as pathmod
    from ate.core.database import set_context
    from ate.core.registry import group_by_fixture
    from ate.core.runner import ATECore, RunParams

    old_root = pathmod.TEST_DB_ROOT
    old_db = dbmod.TEST_DB_ROOT
    pathmod.TEST_DB_ROOT = tmp / "#Test_Database"
    dbmod.TEST_DB_ROOT = pathmod.TEST_DB_ROOT
    core = None
    try:
        pathmod.TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
        set_context(
            component="Logic",
            part="RS1G07",
            package="SOT23",
            operator="Eugene",
            version="Version_1",
            model="RS622",
            part_key="rs1g07",
            sample_size=1,
        )
        from ate.core.database import get_context as _gc

        if "RS1G07" not in str(_gc().model or "").upper():
            errors.append(
                f"stale RS622 model must not stick on RS1G07, got {_gc().model!r}"
            )
        core = ATECore(emit=lambda _e: None)
        core.load_family("logic")
        core.open_session(sim=True)
        if not core.simulated:
            errors.append("open_session(sim=True) must set simulated")
        if core.gate.auto_continue:
            errors.append("Open SIM must not auto-continue START; only DEMO/auto_continue")
        rp = RunParams(
            vcc=3.3,
            part="rs1g07",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        g07_ids = [
            "supply_current",
            "delta_supply_current",
            "ioff_leakage",
            "input_leakage_sweep",
            "cpd",
            "cin",
        ]
        results = core.run_sequence(g07_ids, rp)
        if core.last_run_error:
            errors.append(f"run_sequence error: {core.last_run_error}")
        ids = {r.test_id: r for r in results}
        for tid in g07_ids:
            row = ids.get(tid)
            if row is None:
                errors.append(f"SIM missing result {tid}")
            elif not row.success:
                errors.append(f"SIM {tid} failed: {row.error or row.summary}")
        psu_sim = core._instr.psu if core._instr is not None else None
        writes = getattr(psu_sim, "writes", []) if psu_sim is not None else []
        if not any("OUTP" in str(w).upper() and "ON" in str(w).upper() for w in writes):
            errors.append("SIM cin must send PSU OUTP ON")
        g07_pdfs = list((pathmod.TEST_DB_ROOT / "Logic").rglob("sessions/datalog.pdf"))
        if not g07_pdfs:
            errors.append("SIM RS1G07 must write sessions/datalog.pdf")
        else:
            blob = g07_pdfs[0].read_bytes()
            for token in (b"ICC_uA", b"CPD_pF", b"CIN_pF", b"Status"):
                if token not in blob:
                    errors.append(f"RS1G07 STS PDF missing {token.decode()}")
        g07_log = list((pathmod.TEST_DB_ROOT / "Logic").rglob("sessions/run_log.txt"))
        if not g07_log:
            errors.append("SIM RS1G07 must write sessions/run_log.txt")
        from ate.reporting.session_values import fill_workbook_from_report

        filled = fill_workbook_from_report(demo=True)
        if filled.get("status") == "error":
            errors.append(f"SIM fill demo crashed: {filled}")

        from ate.core.database import get_context, load_test_params, save_test_params

        ctx = get_context()
        ctx.ensure_tree()
        save_test_params(
            "cin",
            {"freq_start": 2.0, "freq_stop": 2.0, "freq_step": 1.0},
            ctx=ctx,
        )
        disk = load_test_params(ctx).get("tests") or {}
        if (disk.get("cin") or {}).get("freq_start") != 2.0:
            errors.append(f"SIM test_params.yaml cin not written, got {disk}")
        rp_ov = RunParams(
            vcc=3.3,
            part="rs1g07",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
            test_params=disk,
        )
        ov_results = core.run_sequence(["cin"], rp_ov)
        if core.last_run_error:
            errors.append(f"overlay cin error: {core.last_run_error}")
        cin_ov = next((r for r in ov_results if r.test_id == "cin"), None)
        if cin_ov is None or not cin_ov.success:
            errors.append(f"overlay cin failed: {cin_ov}")
        else:
            inner = cin_ov.data.get("data") if isinstance(cin_ov.data, dict) else {}
            rows = (inner or {}).get("rows") if isinstance(inner, dict) else None
            if not isinstance(rows, list):
                rows = (cin_ov.data or {}).get("rows") if isinstance(cin_ov.data, dict) else []
            freqs = [float(r.get("freq_hz") or 0) for r in (rows or []) if isinstance(r, dict)]
            if len(freqs) != 1 or abs(freqs[0] - 2e6) > 1:
                errors.append(f"START overlay must run CIN at 2 MHz only, got {freqs}")

        core.close_session()
        set_context(
            component="Logic",
            part="RS1GT34",
            package="SOT23-5",
            operator="Eugene",
            version="Version_1",
            model="RS1GT34XC5",
            part_key="rs1gt34",
            sample_size=1,
        )
        core.load_family("logic")
        core.open_session(sim=True)
        rp34 = RunParams(
            vcc=5.0,
            part="rs1gt34",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        ids34 = ["vih_vil", "voh_load", "vol_load", "supply_current_sweep"]
        results34 = core.run_sequence(ids34, rp34)
        if core.last_run_error:
            errors.append(f"RS1GT34 run_error: {core.last_run_error}")
        got34 = {r.test_id: r for r in results34}
        for tid in ids34:
            row = got34.get(tid)
            if row is None:
                errors.append(f"SIM RS1GT34 missing {tid}")
            elif not row.success:
                errors.append(f"SIM RS1GT34 {tid} failed: {row.error or row.summary}")
        vih_meas = (got34.get("vih_vil").data or {}).get("measurements") if got34.get("vih_vil") else None
        if not any(
            str(m.get("id") or "").startswith("VIH_")
            for m in (vih_meas or [])
            if isinstance(m, dict)
        ):
            errors.append(f"SIM RS1GT34 vih_vil missing VIH_* got {vih_meas}")
        voh_meas = (got34.get("voh_load").data or {}).get("measurements") if got34.get("voh_load") else None
        if not any(
            m.get("id") == "VOH_2p0V"
            for m in (voh_meas or [])
            if isinstance(m, dict)
        ):
            errors.append(f"SIM RS1GT34 voh_load missing VOH_2p0V got {voh_meas}")

        core.close_session()
        set_context(
            component="OpAmp",
            part="RS622",
            package="TTSOP8",
            operator="Eugene",
            version="Version_1",
            model="RS622",
            part_key="rs622",
            sample_size=1,
        )
        core.load_family("opamp")
        modes = [m for m, _ in group_by_fixture(["slew", "psrr"])]
        if modes != ["BUFFER", "ATE"]:
            errors.append(f"slew/psrr must be separate fixture batches, got {modes}")
        core.open_session(sim=True)
        rp2 = RunParams(
            vcc=5.0,
            part="rs622",
            dut_indices=[1],
            channels=["CHA"],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results2 = core.run_sequence(["slew", "psrr"], rp2)
        if core.last_run_error:
            errors.append(f"RS622 run_sequence error: {core.last_run_error}")
        ids2 = {r.test_id: r for r in results2}
        for tid in ("slew", "psrr"):
            row = ids2.get(tid)
            if row is None:
                errors.append(f"SIM RS622 missing result {tid}")
            elif not row.success:
                errors.append(f"SIM {tid} failed: {row.error or row.summary}")
        gen = core._instr.gen if core._instr is not None else None
        scope = core._instr.scope if core._instr is not None else None
        gen_w = getattr(gen, "writes", []) if gen is not None else []
        scope_w = getattr(scope, "writes", []) if scope is not None else []
        if not any("APPL" in str(w).upper() for w in gen_w):
            errors.append("SIM RS622 must send AWG APPL")
        if not any("OUTP" in str(w).upper() and "ON" in str(w).upper() for w in gen_w):
            errors.append("SIM RS622 must send AWG OUTP ON")
        if not any("TRIG" in str(w).upper() or "MEASURE" in str(w).upper() for w in scope_w):
            errors.append("SIM RS622 must send scope TRIG or MEASURE")
        recs = list(pathmod.TEST_DB_ROOT.rglob("records/*.json"))
        if not any("slew" in p.name for p in recs):
            errors.append("SIM RS622 must write independent slew records/")
        if not any("psrr" in p.name for p in recs):
            errors.append("SIM RS622 must write independent psrr records/")
        shots = list((pathmod.TEST_DB_ROOT / "OpAmp").rglob("screenshots/*"))
        if not shots:
            errors.append("SIM RS622 slew must write screenshots")
        if not any(
            "Eugene" in str(p) and "Version_1" in str(p) for p in recs
        ):
            errors.append("SIM RS622 logs must stay in this operator Version_1 folder")
        reports = list(pathmod.TEST_DB_ROOT.rglob("sessions/report.json"))
        if not reports:
            errors.append("SIM RS622 must merge sessions/report.json")
        pdfs = list(pathmod.TEST_DB_ROOT.rglob("sessions/datalog.pdf"))
        if not pdfs:
            errors.append("SIM RS622 must write sessions/datalog.pdf")
        else:
            blob = pdfs[0].read_bytes()
            if b"Parameter" not in blob:
                errors.append("STS PDF must contain Parameter column")
            if b"SR_Vus" not in blob and b"slew" not in blob:
                errors.append("STS PDF must include slew SR_Vus (or slew id)")
            if b"Status" not in blob and b"Total" not in blob:
                errors.append("STS PDF must show Status/Total like the STS sheet")

        results_vos = core.run_sequence(["vos_sweep"], rp2)
        if core.last_run_error:
            errors.append(f"rs622 vos_sweep run_error: {core.last_run_error}")
        row_vos = next((r for r in results_vos if r.test_id == "vos_sweep"), None)
        if row_vos is None or not row_vos.success:
            errors.append(f"SIM rs622 vos_sweep failed: {row_vos}")
        else:
            blob_vos = row_vos.data or {}
            inner_vos = blob_vos.get("data") if isinstance(blob_vos, dict) else {}
            meas_vos = blob_vos.get("measurements") if isinstance(blob_vos, dict) else None
            if not isinstance(meas_vos, list):
                meas_vos = (
                    inner_vos.get("measurements") if isinstance(inner_vos, dict) else []
                )
            vos_m = next(
                (
                    m
                    for m in (meas_vos or [])
                    if isinstance(m, dict) and m.get("id") == "VOS_mV"
                ),
                None,
            )
            if vos_m is None:
                errors.append("SIM rs622 vos_sweep must stamp VOS_mV")
            else:
                try:
                    vos_v = float(vos_m.get("value"))
                except (TypeError, ValueError):
                    vos_v = 99.0
                if abs(vos_v) > 0.05:
                    errors.append(
                        f"SIM G201 Vos_dut=0 must extract ~0 mV, got {vos_m}"
                    )
            if not isinstance(inner_vos, dict) or inner_vos.get("g201_vos") is not True:
                errors.append(f"SIM rs622 vos must take G201 CHAN2 Path B, got {inner_vos}")
            slope_v = float((inner_vos or {}).get("slope") or 0) if isinstance(inner_vos, dict) else 0.0
            if slope_v < 180.0 or slope_v > 220.0:
                errors.append(
                    f"SIM G201 CHAN2 slope must be ~201 V/V, got {slope_v}"
                )

        results_ac = core.run_sequence(["ac_gain_check"], rp2)
        if core.last_run_error:
            errors.append(f"rs622 ac_gain_check run_error: {core.last_run_error}")
        row_ac = next((r for r in results_ac if r.test_id == "ac_gain_check"), None)
        if row_ac is None or not row_ac.success:
            errors.append(f"SIM rs622 ac_gain_check failed: {row_ac}")
        else:
            blob_ac = row_ac.data or {}
            inner_ac = blob_ac.get("data") if isinstance(blob_ac, dict) else {}
            meas_ac = blob_ac.get("measurements") if isinstance(blob_ac, dict) else None
            if not isinstance(meas_ac, list):
                meas_ac = (
                    inner_ac.get("measurements") if isinstance(inner_ac, dict) else []
                )
            gain_m = next(
                (
                    m
                    for m in (meas_ac or [])
                    if isinstance(m, dict) and m.get("id") == "GAIN_VV"
                ),
                None,
            )
            if gain_m is None:
                errors.append("SIM rs622 ac_gain_check must stamp GAIN_VV")
            else:
                try:
                    gain_v = float(gain_m.get("value"))
                except (TypeError, ValueError):
                    gain_v = 0.0
                if gain_v < 180.0 or gain_v > 220.0:
                    errors.append(
                        f"SIM G201 CHAN2 GAIN_VV must be ~201 not G11/CHAN1, got {gain_m}"
                    )
            if not isinstance(inner_ac, dict) or inner_ac.get("g201_ac") is not True:
                errors.append(f"SIM rs622 ac_gain must take G201 CHAN2 Path B, got {inner_ac}")

        results_st = core.run_sequence(["settling"], rp2)
        if core.last_run_error:
            errors.append(f"rs622 settling run_error: {core.last_run_error}")
        row_st = next((r for r in results_st if r.test_id == "settling"), None)
        if row_st is None or not row_st.success:
            errors.append(f"SIM rs622 settling failed: {row_st}")
        else:
            blob_st = row_st.data or {}
            meas_st = blob_st.get("measurements") if isinstance(blob_st, dict) else None
            if not isinstance(meas_st, list):
                inner_st = blob_st.get("data") if isinstance(blob_st, dict) else {}
                meas_st = inner_st.get("measurements") if isinstance(inner_st, dict) else []
            ids_st = [m.get("id") for m in (meas_st or []) if isinstance(m, dict)]
            if "SETTLE_us" in ids_st:
                errors.append("SIM settling must not stamp SETTLE_us")
            vpp_m = next(
                (
                    m
                    for m in (meas_st or [])
                    if isinstance(m, dict) and m.get("id") == "SETTLE_VPP_V"
                ),
                None,
            )
            if vpp_m is None:
                errors.append("SIM leftover settling must stamp SETTLE_VPP_V")
            else:
                try:
                    vpp_v = float(vpp_m.get("value"))
                except (TypeError, ValueError):
                    vpp_v = 0.0
                if vpp_v < 0.4 or vpp_v > 3.0:
                    errors.append(
                        f"SIM settling SETTLE_VPP_V must be BUFFER ~2 Vpp, got {vpp_m}"
                    )

        core.close_session()
        set_context(
            component="AnalogSwitch",
            part="RS2323",
            package="MSOP",
            operator="Eugene",
            version="Version_1",
            model="RS2323",
            part_key="rs2323",
            sample_size=1,
        )
        core.load_family("switch")
        core.open_session(sim=True)
        rp_iso = RunParams(
            vcc=5.0,
            part="rs2323",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_iso = core.run_sequence(["iso", "xtalk"], rp_iso)
        if core.last_run_error:
            errors.append(f"RS2323 iso/xtalk run_error: {core.last_run_error}")
        row_iso = next((r for r in results_iso if r.test_id == "iso"), None)
        if row_iso is None or not row_iso.success:
            errors.append(f"SIM RS2323 iso failed: {row_iso}")
        else:
            meas = (row_iso.data or {}).get("measurements") if isinstance(row_iso.data, dict) else None
            if not isinstance(meas, list):
                inner = (row_iso.data or {}).get("data") if isinstance(row_iso.data, dict) else {}
                meas = (inner or {}).get("measurements") if isinstance(inner, dict) else []
            iso_m = next(
                (m for m in (meas or []) if isinstance(m, dict) and m.get("id") == "ISO_dB"),
                None,
            )
            iso_v = float(iso_m.get("value") or 0) if iso_m else 0.0
            if iso_m is None or iso_v > -20.0:
                errors.append(
                    f"SIM iso must be isolated (not G11 CHAN2 gain), got {iso_m}"
                )
        row_xt = next((r for r in results_iso if r.test_id == "xtalk"), None)
        if row_xt is None or not row_xt.success:
            errors.append(f"SIM RS2323 xtalk failed: {row_xt}")
        else:
            meas = (row_xt.data or {}).get("measurements") if isinstance(row_xt.data, dict) else None
            if not isinstance(meas, list):
                inner = (row_xt.data or {}).get("data") if isinstance(row_xt.data, dict) else {}
                meas = (inner or {}).get("measurements") if isinstance(inner, dict) else []
            xt_m = next(
                (m for m in (meas or []) if isinstance(m, dict) and m.get("id") == "XTALK_dB"),
                None,
            )
            xt_v = float(xt_m.get("value") or 0) if xt_m else 0.0
            if xt_m is None or xt_v > -20.0:
                errors.append(
                    f"SIM xtalk must be isolated (not G11 CHAN2 gain), got {xt_m}"
                )
        set_context(
            component="AnalogSwitch",
            part="RS2227",
            package="MSOP",
            operator="Eugene",
            version="Version_1",
            model="RS2227",
            part_key="rs2227",
            sample_size=1,
        )
        rp_usb = RunParams(
            vcc=5.0,
            part="rs2227",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_usb = core.run_sequence(["usb_iso", "usb_xtalk"], rp_usb)
        if core.last_run_error:
            errors.append(f"RS2227 usb_iso/xtalk run_error: {core.last_run_error}")
        for tid, mid in (("usb_iso", "USB_ISO_dB"), ("usb_xtalk", "USB_XTALK_dB")):
            row_u = next((r for r in results_usb if r.test_id == tid), None)
            if row_u is None or not row_u.success:
                errors.append(f"SIM RS2227 {tid} failed: {row_u}")
                continue
            meas_u = (row_u.data or {}).get("measurements") if isinstance(row_u.data, dict) else None
            if not isinstance(meas_u, list):
                inner_u = (row_u.data or {}).get("data") if isinstance(row_u.data, dict) else {}
                meas_u = (inner_u or {}).get("measurements") if isinstance(inner_u, dict) else []
            um = next(
                (m for m in (meas_u or []) if isinstance(m, dict) and m.get("id") == mid),
                None,
            )
            uv = float(um.get("value") or 0) if um else 0.0
            if um is None or uv > -20.0:
                errors.append(
                    f"SIM {tid} must be isolated (not G11 CHAN2 gain), got {um}"
                )
        core.close_session()
        set_context(
            component="Logic",
            part="RS1G126",
            package="SC70-5",
            operator="SeeLim",
            version="Version_1",
            model="RS1G126XC5",
            part_key="rs1g126",
            sample_size=1,
        )
        core.load_family("logic")
        core.open_session(sim=True)
        want_oe = (
            ("rs1g126", "RRDelay", "FFDelay"),
            ("rs1g125", "FFDelay", "RRDelay"),
        )
        for pk, ten_item, tdis_item in want_oe:
            rp_oe = RunParams(
                vcc=5.0,
                part=pk,
                dut_indices=[1],
                current_limit_a=0.1,
                auto_continue=True,
            )
            results_oe = core.run_sequence(["ten", "tdis"], rp_oe)
            if core.last_run_error:
                errors.append(f"{pk} ten/tdis run_error: {core.last_run_error}")
            for tid, mid, item in (
                ("ten", "TEN_ns", ten_item),
                ("tdis", "TDIS_ns", tdis_item),
            ):
                row_oe = next((r for r in results_oe if r.test_id == tid), None)
                if row_oe is None or not row_oe.success:
                    errors.append(f"SIM {pk} {tid} failed: {row_oe}")
                    continue
                blob = row_oe.data or {}
                meas_oe = blob.get("measurements") if isinstance(blob, dict) else None
                inner_oe = blob.get("data") if isinstance(blob, dict) else {}
                if not isinstance(meas_oe, list):
                    meas_oe = (
                        inner_oe.get("measurements")
                        if isinstance(inner_oe, dict)
                        else []
                    )
                om = next(
                    (
                        m
                        for m in (meas_oe or [])
                        if isinstance(m, dict) and m.get("id") == mid
                    ),
                    None,
                )
                if om is None:
                    errors.append(f"SIM {pk} {tid} must stamp {mid}, got {blob}")
                else:
                    try:
                        nv = float(om.get("value") or 0)
                    except (TypeError, ValueError):
                        nv = 0.0
                    if nv >= 200.0:
                        errors.append(
                            f"SIM {pk} {tid} ns-window delay must be <200 ns, got {nv}"
                        )
                got_item = inner_oe.get("item") if isinstance(inner_oe, dict) else None
                if got_item != item:
                    errors.append(
                        f"SIM {pk} {tid} item must be {item} (oe_active), got {got_item}"
                    )
                if inner_oe.get("hotswap"):
                    errors.append(f"SIM {pk} {tid} must not take RS29511 EN->READY path")
        set_context(
            component="Logic",
            part="RS29511",
            package="SOIC",
            operator="Soo",
            version="Version_1",
            model="RS29511",
            part_key="rs29511",
            sample_size=1,
        )
        rp_hs = RunParams(
            vcc=5.0,
            part="rs29511",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_hs = core.run_sequence(["ten", "tdis"], rp_hs)
        if core.last_run_error:
            errors.append(f"rs29511 ten/tdis run_error: {core.last_run_error}")
        for tid, mid, item in (
            ("ten", "TEN_ns", "RRDelay"),
            ("tdis", "TDIS_ns", "FFDelay"),
        ):
            row_hs = next((r for r in results_hs if r.test_id == tid), None)
            if row_hs is None or not row_hs.success:
                errors.append(f"SIM rs29511 {tid} failed: {row_hs}")
                continue
            blob_hs = row_hs.data or {}
            inner_hs = blob_hs.get("data") if isinstance(blob_hs, dict) else {}
            meas_hs = blob_hs.get("measurements") if isinstance(blob_hs, dict) else None
            if not isinstance(meas_hs, list):
                meas_hs = (
                    inner_hs.get("measurements") if isinstance(inner_hs, dict) else []
                )
            hm = next(
                (
                    m
                    for m in (meas_hs or [])
                    if isinstance(m, dict) and m.get("id") == mid
                ),
                None,
            )
            if hm is None:
                errors.append(f"SIM rs29511 {tid} must stamp {mid}")
            else:
                try:
                    hv = float(hm.get("value") or 0)
                except (TypeError, ValueError):
                    hv = 0.0
                if tid == "ten" and hv < 50000.0:
                    errors.append(
                        f"SIM rs29511 ten must be tIDLE-class (>=50 us), got {hv} ns"
                    )
                if tid == "tdis" and hv >= 200.0:
                    errors.append(
                        f"SIM rs29511 tdis ns-window must be <200 ns, got {hv}"
                    )
            if not isinstance(inner_hs, dict) or inner_hs.get("hotswap") is not True:
                errors.append(f"SIM rs29511 {tid} must take EN->READY path, got {inner_hs}")
            got_hs = inner_hs.get("item") if isinstance(inner_hs, dict) else None
            if got_hs != item:
                errors.append(f"SIM rs29511 {tid} item must be {item}, got {got_hs}")
        results_prop = core.run_sequence(["tp", "tidle"], rp_hs)
        if core.last_run_error:
            errors.append(f"rs29511 tp/tidle run_error: {core.last_run_error}")
        row_tp = next((r for r in results_prop if r.test_id == "tp"), None)
        if row_tp is None or not row_tp.success:
            errors.append(f"SIM rs29511 tp failed: {row_tp}")
        else:
            blob_tp = row_tp.data or {}
            inner_tp = blob_tp.get("data") if isinstance(blob_tp, dict) else {}
            meas_tp = blob_tp.get("measurements") if isinstance(blob_tp, dict) else None
            if not isinstance(meas_tp, list):
                meas_tp = (
                    inner_tp.get("measurements") if isinstance(inner_tp, dict) else []
                )
            phl = next(
                (
                    m
                    for m in (meas_tp or [])
                    if isinstance(m, dict) and m.get("id") == "TPD_PHL_ns"
                ),
                None,
            )
            if phl is None:
                errors.append("SIM rs29511 tp must stamp TPD_PHL_ns")
            elif float(phl.get("value") or 0) >= 200.0:
                errors.append(
                    f"SIM rs29511 tp ns-window must be <200 ns, got {phl}"
                )
            if not isinstance(inner_tp, dict) or inner_tp.get("hotswap_prop") is not True:
                errors.append(f"SIM rs29511 tp must take SDA Path B, got {inner_tp}")
        row_ti = next((r for r in results_prop if r.test_id == "tidle"), None)
        if row_ti is None or not row_ti.success:
            errors.append(f"SIM rs29511 tidle failed: {row_ti}")
        else:
            blob_ti = row_ti.data or {}
            inner_ti = blob_ti.get("data") if isinstance(blob_ti, dict) else {}
            meas_ti = blob_ti.get("measurements") if isinstance(blob_ti, dict) else None
            if not isinstance(meas_ti, list):
                meas_ti = (
                    inner_ti.get("measurements") if isinstance(inner_ti, dict) else []
                )
            idle_m = next(
                (
                    m
                    for m in (meas_ti or [])
                    if isinstance(m, dict) and m.get("id") == "TIDLE_PHL_ns"
                ),
                None,
            )
            if idle_m is None:
                errors.append("SIM rs29511 tidle must stamp TIDLE_PHL_ns")
            elif float(idle_m.get("value") or 0) >= 200.0:
                errors.append(
                    f"SIM rs29511 tidle ns-window must be <200 ns, got {idle_m}"
                )
            if not isinstance(inner_ti, dict) or inner_ti.get("hotswap_prop") is not True:
                errors.append(f"SIM rs29511 tidle must take SDA Path B, got {inner_ti}")
        results_dc = core.run_sequence(
            ["supply_current", "output_voltage", "cap_load"], rp_hs
        )
        if core.last_run_error:
            errors.append(f"rs29511 dc run_error: {core.last_run_error}")
        row_icc = next((r for r in results_dc if r.test_id == "supply_current"), None)
        if row_icc is None or not row_icc.success:
            errors.append(f"SIM rs29511 supply_current failed: {row_icc}")
        else:
            blob_icc = row_icc.data or {}
            inner_icc = blob_icc.get("data") if isinstance(blob_icc, dict) else {}
            meas_icc = blob_icc.get("measurements") if isinstance(blob_icc, dict) else None
            if not isinstance(meas_icc, list):
                meas_icc = (
                    inner_icc.get("measurements") if isinstance(inner_icc, dict) else []
                )
            icc_m = next(
                (
                    m
                    for m in (meas_icc or [])
                    if isinstance(m, dict) and m.get("id") == "ICC_uA"
                ),
                None,
            )
            if icc_m is None:
                errors.append("SIM rs29511 ICC must stamp ICC_uA")
            else:
                icc_v = float(icc_m.get("value") or 0)
                if icc_v <= 0 or icc_v >= 100.0:
                    errors.append(
                        f"SIM rs29511 ICC must be CMOS-uA class under 100 uA, got {icc_m}"
                    )
            if not isinstance(inner_icc, dict) or inner_icc.get("hotswap_dc") is not True:
                errors.append(f"SIM rs29511 ICC must take Path B rs29511_dc, got {inner_icc}")
            rows_icc = inner_icc.get("rows") if isinstance(inner_icc, dict) else None
            vccs_icc = {
                float(r.get("VCC"))
                for r in (rows_icc or [])
                if isinstance(r, dict) and r.get("VCC") is not None
            }
            if 1.65 in vccs_icc:
                errors.append("SIM rs29511 ICC must not sweep CMOS 1.65 V")
            if 2.3 not in vccs_icc or 5.5 not in vccs_icc:
                errors.append(f"SIM rs29511 ICC must sweep 2.3 and 5.5 V, got {vccs_icc}")
        row_vo = next((r for r in results_dc if r.test_id == "output_voltage"), None)
        if row_vo is None or not row_vo.success:
            errors.append(f"SIM rs29511 output_voltage failed: {row_vo}")
        else:
            blob_vo = row_vo.data or {}
            inner_vo = blob_vo.get("data") if isinstance(blob_vo, dict) else {}
            meas_vo = blob_vo.get("measurements") if isinstance(blob_vo, dict) else None
            if not isinstance(meas_vo, list):
                meas_vo = (
                    inner_vo.get("measurements") if isinstance(inner_vo, dict) else []
                )
            vo_m = next(
                (
                    m
                    for m in (meas_vo or [])
                    if isinstance(m, dict) and m.get("id") == "VOUT_V"
                ),
                None,
            )
            if vo_m is None:
                errors.append("SIM rs29511 READY must stamp VOUT_V")
            elif abs(float(vo_m.get("value") or 0) - 5.0) > 0.2:
                errors.append(f"SIM rs29511 READY idle high must be ~VCC, got {vo_m}")
            if not isinstance(inner_vo, dict) or inner_vo.get("hotswap_dc") is not True:
                errors.append(f"SIM rs29511 READY must take Path B rs29511_dc, got {inner_vo}")
        row_cap = next((r for r in results_dc if r.test_id == "cap_load"), None)
        if row_cap is None or not row_cap.success:
            errors.append(f"SIM rs29511 cap_load failed: {row_cap}")
        else:
            blob_cap = row_cap.data or {}
            inner_cap = blob_cap.get("data") if isinstance(blob_cap, dict) else {}
            meas_cap = blob_cap.get("measurements") if isinstance(blob_cap, dict) else None
            if not isinstance(meas_cap, list):
                meas_cap = (
                    inner_cap.get("measurements") if isinstance(inner_cap, dict) else []
                )
            cap_m = next(
                (
                    m
                    for m in (meas_cap or [])
                    if isinstance(m, dict) and m.get("id") == "CAP_pF"
                ),
                None,
            )
            if cap_m is None:
                errors.append("SIM rs29511 Cio must stamp CAP_pF")
            else:
                cap_v = float(cap_m.get("value") or 0)
                if cap_v < 1.0 or cap_v > 15.0:
                    errors.append(f"SIM rs29511 Cio must be pF-class, got {cap_m}")
            if not isinstance(inner_cap, dict) or inner_cap.get("hotswap_dc") is not True:
                errors.append(f"SIM rs29511 Cio must take Path B rs29511_dc, got {inner_cap}")
        set_context(
            component="Logic",
            part="RS1G08",
            package="SC70-5",
            operator="Ariff",
            version="Version_1",
            model="RS1G08XC5",
            part_key="rs1g08",
            sample_size=1,
        )
        rp_and = RunParams(
            vcc=5.0,
            part="rs1g08",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_and = core.run_sequence(["tp", "tidle"], rp_and)
        if core.last_run_error:
            errors.append(f"rs1g08 tp/tidle run_error: {core.last_run_error}")
        row_and = next((r for r in results_and if r.test_id == "tp"), None)
        if row_and is None or not row_and.success:
            errors.append(f"SIM rs1g08 tp failed: {row_and}")
        else:
            blob_and = row_and.data or {}
            inner_and = blob_and.get("data") if isinstance(blob_and, dict) else {}
            meas_and = blob_and.get("measurements") if isinstance(blob_and, dict) else None
            if not isinstance(meas_and, list):
                meas_and = (
                    inner_and.get("measurements") if isinstance(inner_and, dict) else []
                )
            and_phl = next(
                (
                    m
                    for m in (meas_and or [])
                    if isinstance(m, dict) and m.get("id") == "TPD_PHL_ns"
                ),
                None,
            )
            if and_phl is None:
                errors.append("SIM rs1g08 tp must stamp TPD_PHL_ns")
            elif float(and_phl.get("value") or 0) >= 200.0:
                errors.append(f"SIM rs1g08 tp ns-window must be <200 ns, got {and_phl}")
            if not isinstance(inner_and, dict) or inner_and.get("cmos_prop") is not True:
                errors.append(f"SIM rs1g08 tp must take CMOS Path B, got {inner_and}")
            if isinstance(inner_and, dict) and inner_and.get("strap_b") != "VCC":
                errors.append(f"SIM rs1g08 AND must strap B=VCC, got {inner_and}")
            if isinstance(inner_and, dict) and inner_and.get("hotswap_prop"):
                errors.append("SIM rs1g08 tp must not take RS29511 SDA path")
        rp_or = RunParams(
            vcc=5.0,
            part="rs1g32",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_or = core.run_sequence(["tp"], rp_or)
        row_or = next((r for r in results_or if r.test_id == "tp"), None)
        if row_or is None or not row_or.success:
            errors.append(f"SIM rs1g32 tp failed: {row_or}")
        else:
            inner_or = (row_or.data or {}).get("data") if isinstance(row_or.data, dict) else {}
            if not isinstance(inner_or, dict) or inner_or.get("strap_b") != "GND":
                errors.append(f"SIM rs1g32 OR must strap B=GND, got {inner_or}")
        set_context(
            component="Logic",
            part="RS1G14",
            package="SOT23",
            operator="Eugene",
            version="Version_1",
            model="RS1G14",
            part_key="rs1g14",
            sample_size=1,
        )
        rp_inv = RunParams(
            vcc=5.0,
            part="rs1g14",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_inv = core.run_sequence(["tp"], rp_inv)
        if core.last_run_error:
            errors.append(f"rs1g14 tp run_error: {core.last_run_error}")
        row_inv = next((r for r in results_inv if r.test_id == "tp"), None)
        if row_inv is None or not row_inv.success:
            errors.append(f"SIM rs1g14 tp failed: {row_inv}")
        else:
            inner_inv = (row_inv.data or {}).get("data") if isinstance(row_inv.data, dict) else {}
            if not isinstance(inner_inv, dict) or inner_inv.get("invert") is not True:
                errors.append(f"SIM rs1g14 tp must flag invert, got {inner_inv}")
            if isinstance(inner_inv, dict) and (
                inner_inv.get("delay_hl") != "RFDelay" or inner_inv.get("delay_lh") != "FRDelay"
            ):
                errors.append(
                    f"SIM rs1g14 invert must query RFDelay/FRDelay, got {inner_inv}"
                )
        results_dc = core.run_sequence(["voh_load", "vol_load", "vih_vil"], rp_inv)
        if core.last_run_error:
            errors.append(f"rs1g14 dc run_error: {core.last_run_error}")
        got_inv = {r.test_id: r for r in results_dc}
        for tid in ("voh_load", "vol_load", "vih_vil"):
            row_dc = got_inv.get(tid)
            if row_dc is None or not row_dc.success:
                errors.append(f"SIM rs1g14 {tid} failed: {row_dc}")
        voh_blob = (got_inv.get("voh_load").data or {}) if got_inv.get("voh_load") else {}
        voh_inner = voh_blob.get("data") if isinstance(voh_blob.get("data"), dict) else voh_blob
        voh_rows = voh_inner.get("rows") if isinstance(voh_inner, dict) else []
        voh5 = next(
            (
                r
                for r in (voh_rows or [])
                if isinstance(r, dict) and abs(float(r.get("VCC") or 0) - 5.0) < 0.01
            ),
            None,
        )
        if not isinstance(voh5, dict):
            errors.append(f"SIM rs1g14 voh_load missing VCC=5 row, got {voh_rows}")
        else:
            a_voh = float(voh5.get("INPUT_A_V") if voh5.get("INPUT_A_V") is not None else 99)
            meas_voh = float(voh5.get("Measured") or 0)
            if a_voh > 0.2:
                errors.append(f"SIM rs1g14 VOH must drive A=0, got {voh5}")
            if abs(a_voh - 5.0) < 0.2 and abs(meas_voh - 5.0) < 0.35:
                errors.append(
                    f"SIM rs1g14 VOH equals VCC while A=VCC (old buffer polarity), got {voh5}"
                )
            if abs(meas_voh - 5.0) > 0.35:
                errors.append(f"SIM rs1g14 VOH with A=0 must be near VCC, got {voh5}")
        vol_blob = (got_inv.get("vol_load").data or {}) if got_inv.get("vol_load") else {}
        vol_inner = vol_blob.get("data") if isinstance(vol_blob.get("data"), dict) else vol_blob
        vol_rows = vol_inner.get("rows") if isinstance(vol_inner, dict) else []
        vol5 = next(
            (
                r
                for r in (vol_rows or [])
                if isinstance(r, dict) and abs(float(r.get("VCC") or 0) - 5.0) < 0.01
            ),
            None,
        )
        if not isinstance(vol5, dict):
            errors.append(f"SIM rs1g14 vol_load missing VCC=5 row, got {vol_rows}")
        else:
            a_vol = float(vol5.get("INPUT_A_V") if vol5.get("INPUT_A_V") is not None else 0)
            meas_vol = float(vol5.get("Measured") or 99)
            if abs(a_vol - 5.0) > 0.2:
                errors.append(f"SIM rs1g14 VOL must drive A=VCC, got {vol5}")
            if meas_vol > 0.2:
                errors.append(f"SIM rs1g14 VOL with A=VCC must be low, got {vol5}")
        vih_meas = (got_inv.get("vih_vil").data or {}).get("measurements") if got_inv.get("vih_vil") else None
        if not any(
            str(m.get("id") or "").startswith("VIH_")
            for m in (vih_meas or [])
            if isinstance(m, dict)
        ):
            errors.append(f"SIM rs1g14 vih_vil missing VIH_* got {vih_meas}")
        set_context(
            component="Logic",
            part="RS164",
            package="SOP14",
            operator="Eugene",
            version="Version_1",
            model="RS164XP",
            part_key="rs164",
            sample_size=1,
        )
        rp_sh = RunParams(
            vcc=5.0,
            part="rs164",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_sh = core.run_sequence(["serial_shift"], rp_sh)
        if core.last_run_error:
            errors.append(f"rs164 serial_shift run_error: {core.last_run_error}")
        row_sh = next((r for r in results_sh if r.test_id == "serial_shift"), None)
        if row_sh is None or not row_sh.success:
            errors.append(f"SIM rs164 serial_shift failed: {row_sh}")
        else:
            blob_sh = row_sh.data or {}
            meas_sh = blob_sh.get("measurements") if isinstance(blob_sh, dict) else None
            if not isinstance(meas_sh, list):
                inner_sh = blob_sh.get("data") if isinstance(blob_sh, dict) else {}
                meas_sh = inner_sh.get("measurements") if isinstance(inner_sh, dict) else []
            qhi_m = next(
                (m for m in (meas_sh or []) if isinstance(m, dict) and m.get("id") == "Q7_HIGH_V"),
                None,
            )
            qlo_m = next(
                (m for m in (meas_sh or []) if isinstance(m, dict) and m.get("id") == "Q7_LOW_V"),
                None,
            )
            qhi_v = float(qhi_m.get("value") or 0) if qhi_m else 0.0
            qlo_v = float(qlo_m.get("value") or 0) if qlo_m else 99.0
            if qhi_m is None or abs(qhi_v - 5.0) > 0.25:
                errors.append(f"SIM rs164 Q7_HIGH_V must follow A=VCC, got {qhi_m}")
            if qlo_m is None or qlo_v > 0.2:
                errors.append(f"SIM rs164 Q7_LOW_V must follow A=0, got {qlo_m}")
        set_context(
            component="Logic",
            part="RS1G123",
            package="VSSOP8",
            operator="Eugene",
            version="Version_1",
            model="RS1G123XVS8",
            part_key="rs1g123",
            sample_size=1,
        )
        rp_pw = RunParams(
            vcc=5.0,
            part="rs1g123",
            dut_indices=[1],
            current_limit_a=0.1,
            auto_continue=True,
        )
        results_pw = core.run_sequence(["pulse_width"], rp_pw)
        if core.last_run_error:
            errors.append(f"rs1g123 pulse_width run_error: {core.last_run_error}")
        row_pw = next((r for r in results_pw if r.test_id == "pulse_width"), None)
        if row_pw is None or not row_pw.success:
            errors.append(f"SIM rs1g123 pulse_width failed: {row_pw}")
        else:
            blob_pw = row_pw.data or {}
            meas_pw = blob_pw.get("measurements") if isinstance(blob_pw, dict) else None
            if not isinstance(meas_pw, list):
                inner_pw = blob_pw.get("data") if isinstance(blob_pw, dict) else {}
                meas_pw = inner_pw.get("measurements") if isinstance(inner_pw, dict) else []
            pulse_m = next(
                (m for m in (meas_pw or []) if isinstance(m, dict) and m.get("id") == "PULSE_ns"),
                None,
            )
            pulse_v = float(pulse_m.get("value") or 0) if pulse_m else 0.0
            if pulse_m is None or abs(pulse_v - 5e5) > 5e4:
                errors.append(
                    f"SIM pulse_width leftover 0.5/f at 1 kHz must be ~500 us, got {pulse_m}"
                )
        core.load_family("power")
        set_context(
            component="Power",
            part="RS3213",
            package="SOT23-5",
            operator="Eugene",
            version="Version_1",
            model="RS3213-3.3XF5",
            part_key="rs3213",
            sample_size=1,
        )
        rp_ldo = RunParams(
            vcc=5.0,
            part="rs3213",
            dut_indices=[1],
            current_limit_a=0.4,
            auto_continue=True,
        )
        results_ldo = core.run_sequence(["vinmin", "lir", "lor", "ioutmax"], rp_ldo)
        if core.last_run_error:
            errors.append(f"rs3213 ldo run_error: {core.last_run_error}")
        got_ldo = {r.test_id: r for r in results_ldo}
        for tid, mid in (
            ("vinmin", "VINMIN_V"),
            ("lir", "LIR_mV"),
            ("lor", "LOR_mV"),
            ("ioutmax", "IOUTMAX_V"),
        ):
            row_ldo = got_ldo.get(tid)
            if row_ldo is None or not row_ldo.success:
                errors.append(f"SIM rs3213 {tid} failed: {row_ldo}")
                continue
            blob_ldo = row_ldo.data or {}
            meas_ldo = blob_ldo.get("measurements") if isinstance(blob_ldo, dict) else None
            if not isinstance(meas_ldo, list):
                inner_ldo = blob_ldo.get("data") if isinstance(blob_ldo, dict) else {}
                meas_ldo = (
                    inner_ldo.get("measurements") if isinstance(inner_ldo, dict) else []
                )
            hit_ldo = next(
                (
                    m
                    for m in (meas_ldo or [])
                    if isinstance(m, dict) and m.get("id") == mid
                ),
                None,
            )
            if hit_ldo is None:
                errors.append(f"SIM rs3213 {tid} missing {mid}")
                continue
            val_ldo = float(hit_ldo.get("value") or 0)
            if tid == "lir" and abs(val_ldo - 1600.0) < 1.0:
                errors.append(f"SIM rs3213 LIR_mV is VIN alias, got {val_ldo}")
            if tid == "lir" and abs(val_ldo - 3400.0) < 1.0:
                errors.append(f"SIM rs3213 LIR_mV is VIN*1000, got {val_ldo}")
            if tid == "vinmin" and not (2.5 <= val_ldo <= 4.0):
                errors.append(f"SIM rs3213 VINMIN_V leftover range, got {val_ldo}")
            if tid == "ioutmax" and val_ldo < 1.0:
                errors.append(f"SIM rs3213 IOUTMAX_V looks Schmitt, got {val_ldo}")
            if tid == "ioutmax":
                inner_io = (
                    blob_ldo.get("data") if isinstance(blob_ldo.get("data"), dict) else blob_ldo
                )
                for rr in (inner_io.get("rows") or []) if isinstance(inner_io, dict) else []:
                    if not isinstance(rr, dict):
                        continue
                    try:
                        vin_r = float(rr.get("VIN_V"))
                        vout_r = float(rr.get("VOUT_AVG_V"))
                    except (TypeError, ValueError):
                        continue
                    if vin_r >= 4.5 and abs(vout_r - vin_r) < 0.08:
                        errors.append(
                            f"SIM rs3213 IOUTMAX VOUT follows VIN={vin_r}, got {vout_r}"
                        )
    except Exception as exc:
        errors.append(f"SIM run crashed: {exc}")
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
        print("FAIL check_sim_run:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        "OK check_sim_run: SIM COUNT/VPP/GBW/Cpd-current; "
        "RS1G07 full suite + PDF/log/shot-txt; "
        "RS1GT34 vih_vil/voh/vol/sweep; "
        "RS622 slew+psrr separated, Version_1 records + STS PDF; "
        "RS622 VOS G201 CHAN2 slope~201; "
        "RS622 AC gain G201 CHAN2 GAIN_VV~201; "
        "RS622 leftover settling SETTLE_VPP_V not SETTLE_us; "
        "RS2323 iso/xtalk SIM not G11 CHAN2; RS2227 usb_iso/xtalk SIM not G11 CHAN2; "
        "RS29511 EN->READY tIDLE vs tDISABLE; RS29511 tp SDA Path B; "
        "RS29511 ICC/READY/Cio Path B; "
        "RS1G08/RS1G32 CMOS tPD strap B; "
        "RS1G14 invert RFDelay/FRDelay; RS1G14 VOH A=0 Y~VCC; RS164 Q7 follows A not VCC; "
        "RS1G123 PULSE leftover 0.5/f not 500 ns dummy; "
        "RS3213 LDO DMM VOUT not VIN alias; "
        "RS0204 CHAN2 OE-DC is DUT Y VPP not OE; RTime MSO-ns; "
        "BUFFER NPR CHAN2 not G11*6 V; OVERSHOOT not 0.12 dummy; "
        "unknown ITEM Rigol invalid not 0.12"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
