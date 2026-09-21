"""Fail-closed: DUT-first vs channel-first walk + BUFFER catalog order.

Run: python -m ate.core.check_walk_order
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


class _Spec:
    def __init__(self, tid: str, *, dual: bool = True) -> None:
        self.id = tid
        self.dual_channel = dual
        self.short_tag = tid.upper()


def main() -> int:
    errors: list[str] = []
    from ate.core.timeline import build_plan, walk_pairs
    from ate.core.runner import RunParams

    ch_pairs = walk_pairs(["CHA", "CHB"], [1, 2], "channel")
    if ch_pairs != [("CHA", 1), ("CHA", 2), ("CHB", 1), ("CHB", 2)]:
        errors.append(f"channel-first pairs {ch_pairs}")
    dut_pairs = walk_pairs(["CHA", "CHB"], [1, 2], "dut")
    if dut_pairs != [("CHA", 1), ("CHB", 1), ("CHA", 2), ("CHB", 2)]:
        errors.append(f"DUT-first pairs {dut_pairs}")
    if walk_pairs(["CHA", "CHB"], [1, 2], "DUT-first") != dut_pairs:
        errors.append("walk_order prefix dut* must match DUT-first")

    rp = RunParams(walk_order="dut", channels=["CHA", "CHB"], dut_indices=[1, 2])
    if rp.resolved_walk_order() != "dut":
        errors.append("RunParams.resolved_walk_order dut failed")
    if RunParams(walk_order="").resolved_walk_order() != "channel":
        errors.append("empty walk_order must default channel")
    over = RunParams(
        vcc_start=0.0,
        vcc_stop=5.0,
        vcc_step=0.5,
        test_params={"iplus": {"vcc_start": 1.8, "vcc_stop": 3.3, "vcc_step": 0.5}},
    )
    got = over.overlay_for("iplus").resolved_vcc_sweep()
    if not got or abs(got[0] - 1.8) > 1e-9:
        errors.append(f"overlay_for iplus sweep {got}")
    if over.overlay_for("ron").vcc_start != 0.0:
        errors.append("overlay_for missing test must keep globals")
    list_over = RunParams(
        vcc_start=0.0,
        vcc_stop=5.0,
        vcc_step=0.5,
        test_params={
            "supply_current_sweep": {
                "vcc_list": [1.65, 3.3, 3.5],
                "logic_inputs": 2,
                "levels": [0.0, 5.5],
            }
        },
    )
    list_pts = list_over.overlay_for("supply_current_sweep").resolved_vcc_sweep()
    if list_pts != [1.65, 3.3, 3.5]:
        errors.append(f"vcc_list must win over start/stop/step, got {list_pts}")
    from ate.tests.logic.ariff_dc import _input_corners, _logic_inputs

    if len(_input_corners(2, [0.0, 5.5])) != 4:
        errors.append("2-input corners must be 4 (2^n)")
    if len(_input_corners(1, [0.0, 5.5])) != 2:
        errors.append("1-input corners must be 2")
    if _logic_inputs({"logic_inputs": 3}) != 3:
        errors.append("logic_inputs must uncap past 2")
    from ate.core.database import _clean_test_param_block

    cleaned = _clean_test_param_block(
        {
            "vcc_list": "1.65, 3.3, 3.5",
            "logic_inputs": 2,
            "rails_mode": "dual",
            "rails_psu": "1:VCC:3.300,2:VSS:-3.300",
        }
    )
    if cleaned.get("vcc_list") != [1.65, 3.3, 3.5]:
        errors.append(f"clean vcc_list {cleaned.get('vcc_list')}")
    if (cleaned.get("rails") or {}).get("mode") != "dual":
        errors.append(f"clean rails {cleaned.get('rails')}")
    timing = _clean_test_param_block(
        {"settle_s": "0.3", "timeout_s": 120, "dwell_s": "5.0", "settle_s_bad": "x"}
    )
    if timing.get("settle_s") != 0.3 or timing.get("timeout_s") != 120.0:
        errors.append(f"clean timing floats {timing}")
    if timing.get("dwell_s") != 5.0:
        errors.append(f"clean dwell_s {timing.get('dwell_s')}")
    timing_over = RunParams(
        test_params={"cin": {"settle_s": 0.25, "dwell_s": 4.0, "timeout_s": 30.0}}
    ).overlay_for("cin")
    if timing_over.settle_s != 0.25 or timing_over.dwell_s != 4.0:
        errors.append(f"overlay_for timing {timing_over.settle_s} {timing_over.dwell_s}")
    if timing_over.timeout_s != 30.0:
        errors.append(f"overlay_for timeout_s {timing_over.timeout_s}")
    shot_clean = _clean_test_param_block({"screenshot_from": "mso", "settle_s": 0.3})
    if shot_clean.get("screenshot_from") != "mso":
        errors.append("Write screenshot_from=mso must persist (not stripped)")
    if shot_clean.get("settle_s") != 0.3:
        errors.append("screenshot_from Write must keep settle_s")
    shot_over = RunParams(
        test_params={"icc": {"screenshot_from": "mso"}}
    ).overlay_for("icc")
    if getattr(shot_over, "screenshot_from", "") != "mso":
        errors.append("overlay_for must apply screenshot_from=mso")
    dmm_clean = _clean_test_param_block({"screenshot_from": "dmm", "settle_s": 0.2})
    if dmm_clean.get("screenshot_from") != "dmm":
        errors.append("Write screenshot_from=dmm must persist (not stripped)")
    dmm_over = RunParams(test_params={"ioz": {"screenshot_from": "dmm"}}).overlay_for("ioz")
    if getattr(dmm_over, "screenshot_from", "") != "dmm":
        errors.append("overlay_for must apply screenshot_from=dmm")
    none_clean = _clean_test_param_block({"screenshot_from": "none"})
    if none_clean.get("screenshot_from") != "none":
        errors.append("Write screenshot_from=none must persist (disable DMM shot)")
    avg_over = RunParams(
        test_params={"ioz": {"dmm_avg_n": 5, "dmm_nplc": 1, "screenshot_from": "dmm"}}
    ).overlay_for("ioz")
    if getattr(avg_over, "dmm_avg_n", None) != 5:
        errors.append("overlay_for must apply dmm_avg_n=5")
    if getattr(avg_over, "dmm_nplc", None) != 1:
        errors.append("overlay_for must apply dmm_nplc=1")
    rtxt = Path(__file__).with_name("runner.py").read_text(encoding="utf-8")
    cap = rtxt[rtxt.find("def capture_screenshot") : rtxt.find("def operator_respond")]
    if "_reopen_mso_after_visa" not in cap:
        errors.append("capture_screenshot must reopen MSO after :DISP:DATA? poison")
    if "screenshot_from=mso skipped on SIM" not in rtxt:
        errors.append("_run_one must honor screenshot_from from Parameters Write")
    if "no Keithley dump" in rtxt:
        errors.append("screenshot_from=dmm must dump DMM6500 HCOP, not a phone stub")
    if "capture_dmm_screenshot" not in rtxt:
        errors.append("runner must capture_dmm_screenshot for screenshot_from=dmm")
    if "TestSpec is not MSO" not in rtxt:
        errors.append("IOZ/ICC must not capture MSO when screenshot_from=mso")
    if "using DMM instead" not in rtxt:
        errors.append("stale screenshot_from=mso on IOZ must fall through to DMM")
    if "spec.lab_sheet" not in rtxt:
        errors.append("DMM/MSO screenshots must land in lab_sheet folder (IOZ not ioz)")
    dmm_src = Path(__file__).resolve().parents[2] / "dmm_setup.py"
    dtxt = dmm_src.read_text(encoding="utf-8")
    if "DATA:FORM" in dtxt and "Do not send :HCOP:SDUM:DATA:FORM" not in dtxt:
        errors.append("DMM6500 must not send HCOP DATA:FORM (1.7.16a -113)")
    if "_reading_png" not in dtxt:
        errors.append("DMM HCOP leftover must write a reading-card PNG, never MSO")
    if "def is_banned_dmm_scpi" not in dtxt:
        errors.append("dmm_setup must expose is_banned_dmm_scpi")
    if "def clear_active_buffer" not in dtxt or "def dmm_drain_errors" not in dtxt:
        errors.append("dmm_setup must drain SYST:ERR and clear buffer before READ")
    if "dmm_scpi.log" not in dtxt:
        errors.append("dmm_setup must append DMM write/SYST:ERR to ate/worker/dmm_scpi.log")
    if "def dmm_dismiss_header" not in dtxt or "SYST:CLE" not in dtxt:
        errors.append("dmm_setup must SYST:CLE leftover Event Log once (not every READ)")
    sess_src = (Path(__file__).resolve().parents[1] / "instruments" / "session.py").read_text(
        encoding="utf-8"
    )
    if "dmm_dismiss_header" not in sess_src:
        errors.append("USB Open Session must dismiss leftover DMM Event Log")
    if "def dmm_read_avg" not in dtxt or "statistics.mean" not in dtxt:
        errors.append("dmm_read_avg must mean n readings (host filter, no AVER SCPI)")
    if ".write(" in dtxt and "HCOP" in dtxt:
        for i, ln in enumerate(dtxt.splitlines(), 1):
            if ".write(" in ln and "HCOP" in ln.upper():
                errors.append(f"dmm_setup.py:{i} must not write HCOP")
    from dmm_setup import is_banned_dmm_scpi

    if not is_banned_dmm_scpi("*RST") or not is_banned_dmm_scpi(":HCOP:SDUM:DATA?"):
        errors.append("is_banned_dmm_scpi must flag *RST and HCOP")
    if not is_banned_dmm_scpi(":SENS:CURR:NPLC 1") or not is_banned_dmm_scpi(
        ":TRAC:CLE 'defbuffer1'"
    ):
        errors.append("is_banned_dmm_scpi must flag NPLC/TRAC")
    if is_banned_dmm_scpi(":CONF:CURR:DC") or is_banned_dmm_scpi("*CLS"):
        errors.append("is_banned_dmm_scpi must allow CONF:CURR:DC and *CLS")
    if is_banned_dmm_scpi("SYST:CLE"):
        errors.append("is_banned_dmm_scpi must allow SYST:CLE (Event Log dismiss)")
    if not is_banned_dmm_scpi(":SENS:FUNC 'CURR:DC'"):
        errors.append("is_banned_dmm_scpi must skip extra SENS:FUNC (1.7.16a -113)")
    from dmm_setup import _reading_png

    card = _reading_png("DMM6500 DCI", "2.8 uA")
    if not card.startswith(b"\x89PNG"):
        errors.append("DMM reading card must be a real PNG")
    if "coerce_screenshot_from" not in rtxt:
        errors.append("empty screenshot_from must auto MSO/DMM from TestSpec instruments")
    wtxt = (Path(__file__).resolve().parents[1] / "worker" / "server.py").read_text(
        encoding="utf-8"
    )
    if "coerce_screenshot_from" not in wtxt:
        errors.append("list_tests must coerce screenshot_from from TestSpec instruments")
    from ate.core.param_defaults import coerce_screenshot_from
    from ate.core.registry import known_families, load_family_tests

    if coerce_screenshot_from("mso", frozenset({"DMM", "PSU"})) != "dmm":
        errors.append("DMM-only stale mso must coerce to dmm")
    if coerce_screenshot_from("", frozenset({"DMM"})) != "dmm":
        errors.append("DMM-only empty shot must be dmm")
    if coerce_screenshot_from("mso", frozenset({"MSO", "AWG"})) != "mso":
        errors.append("MSO TestSpec must keep mso")
    if coerce_screenshot_from("mso", frozenset({"PSU"})) != "none":
        errors.append("PSU-only stale mso must not capture MSO")
    for fam in known_families():
        try:
            specs = load_family_tests(fam)
        except Exception as exc:
            errors.append(f"load_family_tests({fam}): {exc}")
            continue
        for spec in specs:
            req = spec.required_instruments
            need = {str(x).upper() for x in (req or ())}
            has_mso = "MSO" in need or "SCOPE" in need
            has_dmm = "DMM" in need
            stale = coerce_screenshot_from("mso", req)
            empty = coerce_screenshot_from("", req)
            if has_dmm and not has_mso:
                if stale != "dmm":
                    errors.append(
                        f"{fam}.{spec.id} DMM-only stale mso must be dmm, got {stale}"
                    )
                if empty != "dmm":
                    errors.append(
                        f"{fam}.{spec.id} DMM-only empty shot must be dmm, got {empty}"
                    )
            elif has_mso:
                if stale != "mso":
                    errors.append(
                        f"{fam}.{spec.id} MSO spec must keep mso, got {stale}"
                    )
                if empty != "mso":
                    errors.append(
                        f"{fam}.{spec.id} MSO spec empty shot must be mso, got {empty}"
                    )
            else:
                if stale != "none":
                    errors.append(
                        f"{fam}.{spec.id} no MSO/DMM must not capture MSO, got {stale}"
                    )
    from ate.core.param_defaults import LOGIC_TEST_DEFAULTS

    if (LOGIC_TEST_DEFAULTS.get("icc") or {}).get("screenshot_from") != "dmm":
        errors.append("LOGIC icc default screenshot_from must be dmm")
    if (LOGIC_TEST_DEFAULTS.get("ioz") or {}).get("screenshot_from") != "dmm":
        errors.append("LOGIC ioz default screenshot_from must be dmm")
    if (LOGIC_TEST_DEFAULTS.get("ioff") or {}).get("screenshot_from") != "dmm":
        errors.append("LOGIC ioff default screenshot_from must be dmm")
    ldc_txt = Path(__file__).resolve().parents[1].joinpath("tests", "logic", "logic_dc.py").read_text(encoding="utf-8")
    if "def _end_powered" not in ldc_txt or "_end_powered" not in ldc_txt.split("def _run_icc", 1)[-1]:
        errors.append("logic_dc DMM tests must _end_powered before power_down")
    if (LOGIC_TEST_DEFAULTS.get("tp") or {}).get("screenshot_from") == "dmm":
        errors.append("LOGIC tp must keep MSO screenshot (not DMM default)")
    from ate.core.progress import who_has_tests

    who_rows = who_has_tests(limit=20)
    if not isinstance(who_rows, list):
        errors.append("who_has_tests must return a list")

    from ate.core.specs import probe_channels_for_part

    if probe_channels_for_part("rs1g07", family="logic") != ["CHA"]:
        errors.append(f"rs1g07 must be CHA only, got {probe_channels_for_part('rs1g07', family='logic')}")
    if probe_channels_for_part("rs622", family="opamp") != ["CHA", "CHB"]:
        errors.append(f"rs622 must be CHA+CHB, got {probe_channels_for_part('rs622', family='opamp')}")
    triple = walk_pairs(["CHA", "CHB", "CHC"], [1, 2], "channel")
    if triple != [
        ("CHA", 1),
        ("CHA", 2),
        ("CHB", 1),
        ("CHB", 2),
        ("CHC", 1),
        ("CHC", 2),
    ]:
        errors.append(f"3-channel walk {triple}")
    if RunParams(channels=["CHA", "CHC"]).resolved_channels() != ["CHA", "CHC"]:
        errors.append("resolved_channels must keep CHC")
    logic_ch = RunParams(part="rs1g07", channels=["CHA", "CHB"]).resolved_channels()
    if logic_ch != ["CHA", "CHB"]:
        errors.append(f"operator CHA+CHB on logic must run both, got {logic_ch}")
    if RunParams(part="rs1g07", channels=["CHA"]).resolved_channels() != ["CHA"]:
        errors.append("logic CHA-only ticks must stay CHA")
    opa_ch = RunParams(part="rs622", channels=["CHA", "CHB"]).resolved_channels()
    if opa_ch != ["CHA", "CHB"]:
        errors.append(f"opamp START must keep CHA+CHB, got {opa_ch}")

    specs = [_Spec("slew")]
    ch_plan = build_plan(
        dut_indices=[1, 2],
        batches=[("BUFFER", specs)],
        gains={"BUFFER": 1.0},
        channels=["CHA", "CHB"],
        walk_order="channel",
    )
    ch_tests = [(e.channel, e.dut) for e in ch_plan if e.kind == "test"]
    if ch_tests != [("CHA", 1), ("CHA", 2), ("CHB", 1), ("CHB", 2)]:
        errors.append(f"channel-first timeline tests {ch_tests}")

    dut_plan = build_plan(
        dut_indices=[1, 2],
        batches=[("BUFFER", specs)],
        gains={"BUFFER": 1.0},
        channels=["CHA", "CHB"],
        walk_order="dut",
    )
    dut_tests = [(e.channel, e.dut) for e in dut_plan if e.kind == "test"]
    if dut_tests != [("CHA", 1), ("CHB", 1), ("CHA", 2), ("CHB", 2)]:
        errors.append(f"DUT-first timeline tests {dut_tests}")
    dut_prompts = [(e.kind, e.dut, e.channel) for e in dut_plan if e.kind == "dut_change"]
    if dut_prompts and dut_prompts[0][1] != 1:
        errors.append(f"DUT-first first socket prompt {dut_prompts[0]}")

    from ate.core.registry import group_by_fixture, load_family

    load_family("opamp")
    want = ["slew", "settling", "sssr", "lssr", "no_phase_reversal", "power_on_time"]
    batches = group_by_fixture(want)
    if not batches or batches[0][0] != "BUFFER":
        errors.append(f"BUFFER batch missing, got {[(m, [s.id for s in sp]) for m, sp in batches]}")
    else:
        got = [s.id for s in batches[0][1]]
        if got != want:
            errors.append(f"BUFFER catalog order {got} want {want}")

    tmp = Path(tempfile.mkdtemp(prefix="ate_walk_"))
    from ate.core import database as dbmod
    from ate.core import paths as pathmod
    from ate.core.database import (
        get_context,
        load_run_prefs,
        save_run_prefs,
        set_context,
    )

    old_root = pathmod.TEST_DB_ROOT
    old_db = dbmod.TEST_DB_ROOT
    pathmod.TEST_DB_ROOT = tmp / "#Test_Database"
    dbmod.TEST_DB_ROOT = pathmod.TEST_DB_ROOT
    try:
        pathmod.TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
        set_context(
            component="OpAmp",
            part="RS622",
            package="TTSOP8",
            operator="Eugene",
            version="Version_1",
            model="RS622",
            part_key="rs622",
            sample_size=2,
        )
        ctx = get_context()
        ctx.ensure_tree()
        if load_run_prefs(ctx).get("walk_order") != "channel":
            errors.append("default walk_order must be channel")
        saved = save_run_prefs("dut", sample_size=6, probe_channels=["CHA"], ctx=ctx)
        if saved.get("walk_order") != "dut":
            errors.append(f"save_run_prefs {saved}")
        if saved.get("sample_size") != 6:
            errors.append(f"save_run_prefs sample_size {saved}")
        if not ctx.run_prefs_path().is_file():
            errors.append("run_prefs.yaml missing after save")
        ident = ctx.identity()
        if ident.get("walk_order") != "dut":
            errors.append(f"identity walk_order {ident.get('walk_order')}")
        if ident.get("sample_size") != 6:
            errors.append(f"identity sample_size {ident.get('sample_size')}")
        if ident.get("probe_channels") != ["CHA"]:
            errors.append(f"identity probe_channels {ident.get('probe_channels')}")
        from ate.core.database import load_test_params, save_test_params

        wrote = save_test_params(
            "iplus",
            {"vcc_start": 1.8, "vcc_stop": 3.3, "vcc_step": 0.5},
            ctx=ctx,
        )
        loaded = load_test_params(ctx)
        if (loaded.get("tests") or {}).get("iplus", {}).get("vcc_start") != 1.8:
            errors.append(f"test_params roundtrip {loaded}")
        if not ctx.test_params_path().is_file():
            errors.append("test_params.yaml missing after save")
        if wrote.get("tests", {}).get("iplus", {}).get("vcc_stop") != 3.3:
            errors.append(f"save_test_params {wrote}")
    finally:
        pathmod.TEST_DB_ROOT = old_root
        dbmod.TEST_DB_ROOT = old_db

    tl_src = Path(__file__).resolve().parent / "timeline.py"
    if "Automated:" in tl_src.read_text(encoding="utf-8"):
        errors.append("timeline next_hint must not say Automated (looks like DEMO)")
    cap = Path(__file__).resolve().parents[1] / "tests" / "logic" / "eugene_cap.py"
    cap_src = cap.read_text(encoding="utf-8")
    if "capture_jpeg" in cap_src or "def _shot" in cap_src:
        errors.append("CIN/CPD are DMM tests; MSO JPEG hangs USB START")
    cin_fn = cap_src.split("def run_cin", 1)[-1].split("register(", 1)[0]
    if "for freq in freqs" not in cin_fn:
        errors.append("run_cin must sweep freqs")
    elif cin_fn.find("_psu_ch1_only") > cin_fn.find("for freq in freqs"):
        errors.append("CIN must power PSU once, then sweep AWG (no OVP flash per MHz)")
    if "_SETTLE_S = 5.0" not in cap_src:
        errors.append("CIN/CPD/IDD must dwell 5s per sweep step on USB")
    if "_dmm_ua_after_settle" not in cap_src:
        errors.append("sweep steps must log DMM delta vs last point")
    if ":OUTP1 OFF" not in cap_src or "APPL:SQU" not in cap_src:
        errors.append("CIN must OUTP OFF then APPL:SQU (DG822 Pro; no FREQ header)")
    if any("write(" in ln and "FREQ" in ln for ln in cap_src.splitlines()):
        errors.append("CIN must not write SOUR FREQ (DG822 Pro Error 116)")
    if "resolved_freq_hz" not in cap_src:
        errors.append("CIN must use panel freq start/stop/step")
    if "applied_freq_hz" not in cap_src:
        errors.append("CIN/CPD C=I/(V f) must use APPL? frequency, not the want")
    delta = Path(__file__).resolve().parents[1] / "tests" / "logic" / "ariff_dc.py"
    delta_src = delta.read_text(encoding="utf-8")
    if "resolved_vcc_sweep" not in delta_src:
        errors.append("Delta Supply must sweep VCC from panel start/stop/step")
    if 'tag in ((vcc, 0.0, "CH1"), (0.0, vcc, "CH2"))' not in delta_src:
        errors.append("Delta Supply must alternate AWG CH1 then CH2")
    if "_dmm_ua_after_settle" not in delta_src and "_settle_ua" not in delta_src:
        errors.append("Ariff VCC sweeps must 5s DMM delta like CIN")
    if "_logic_inputs" not in delta_src:
        errors.append("single-input buffers must skip AWG CH2 (logic_inputs: 1)")
    run_src = (Path(__file__).resolve().parent / "runner.py").read_text(encoding="utf-8")
    if '"MSO" in spec.required_instruments and self._instr.scope is not None' not in run_src:
        errors.append("Logic DMM tests must not recover/park MSO")
    if "post DUT_" in run_src:
        errors.append("do not SAFE IDLE after every test (MSO *IDN hang); idle only at Continue")
    if "skip MSO" not in run_src:
        errors.append("safe idle must skip MSO *IDN on DMM Continue")
    gen_src = (Path(__file__).resolve().parents[2] / "generator_setup.py").read_text(encoding="utf-8")
    if 'write(":OUTP3' in gen_src or "write(':OUTP3" in gen_src:
        errors.append("DG822 Pro is 2-ch; stop_output must not send OUTP3")
    if any("write(" in ln and "DCYC" in ln for ln in gen_src.splitlines()):
        errors.append("DG822 Pro: do not send DCYC header (Error 116)")
    if "APPL:SQU {freq},{vpp},{offset},0" not in gen_src:
        errors.append("setup_square must APPL freq,amp,offset,phase=0 (Pro 50% duty)")
    if "def applied_freq_hz" not in gen_src:
        errors.append("generator_setup must expose applied_freq_hz (APPL? not FREQ?)")
    if "def is_banned_awg_scpi" not in gen_src:
        errors.append("generator_setup must expose is_banned_awg_scpi")
    from generator_setup import applied_freq_hz, is_banned_awg_scpi

    for i, ln in enumerate(gen_src.splitlines(), 1):
        if ".write(" not in ln and ".query(" not in ln:
            continue
        probe = ln.replace("{ch}", "1").replace("{channel}", "1")
        if is_banned_awg_scpi(probe):
            errors.append(
                f"generator_setup.py:{i} banned AWG header (Error 116): {ln.strip()}"
            )

    class _Appl:
        def __init__(self, raw: str) -> None:
            self._raw = raw

        def query(self, cmd: str) -> str:
            return self._raw

    if applied_freq_hz(_Appl("SQU,5000000,3.3,1.65"), 1, 1e6) != 5e6:
        errors.append("applied_freq_hz must parse APPL? frequency")
    quoted = '"SQU,+1.000000000000000E+07,+3.300000000000000E+00,+1.650000000000000E+00,+0.000000000000000E+00"'
    if applied_freq_hz(_Appl(quoted), 1, 1e6) != 10e6:
        errors.append("applied_freq_hz must parse quoted APPL? scientific freq")

    from ate.core.param_defaults import vcc_sweep_points

    pts = vcc_sweep_points(0, 5, 0.5)
    if pts[:1] != [0.0] or pts[-1:] != [5.0] or len(pts) != 11:
        errors.append(f"vcc_sweep_points 0..5 / 0.5 want 11 pts, got {pts}")
    fine = vcc_sweep_points(4.5, 5.5, 0.01)
    if len(fine) != 101 or fine[0] != 4.5 or fine[-1] != 5.5:
        errors.append(f"vcc_sweep_points 4.5..5.5 / 0.01 want 101 pts, got {len(fine)} {fine[:3]}..{fine[-3:]}")

    from ate.core.runner import RunParams

    vin_over = RunParams(test_params={"vih_vil": {"vin_step": 0.01, "vcc_step": 0.01}}).overlay_for("vih_vil")
    if getattr(vin_over, "vin_step", None) != 0.01 or vin_over.vcc_step != 0.01:
        errors.append(f"overlay_for vin_step/vcc_step {getattr(vin_over, 'vin_step', None)} {vin_over.vcc_step}")

    freq = RunParams().resolved_freq_hz()
    if freq != [1e6, 5e6, 10e6]:
        errors.append(f"CIN default freq range must be 1/5/10 MHz, got {freq}")

    if errors:
        print("FAIL check_walk_order:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_walk_order channel/DUT pairs + BUFFER catalog + run_prefs + test_params")
    return 0


if __name__ == "__main__":
    sys.exit(main())
