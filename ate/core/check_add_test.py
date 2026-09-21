"""Fail-closed: add-test Path A/B/C contract (customize vs realize vs wrap scaffold).

Run: python -m ate.core.check_add_test
"""
from __future__ import annotations

import ast
import inspect
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DETECT = REPO / "ate" / "core" / "test_detect.py"
RUNNER = REPO / "ate" / "core" / "runner.py"
LOGIC_INIT = REPO / "ate" / "tests" / "logic" / "__init__.py"
ATE_PROMPT = REPO / ".cursor" / "skills" / "ate-prompt" / "SKILL.md"
ATE_ADD_TEST = REPO / ".cursor" / "skills" / "ate-add-test" / "SKILL.md"
EUGENE = REPO / "ate" / "tests" / "logic" / "eugene_cap.py"
WRAP_SCAFFOLD = REPO / "ate" / "tests" / "logic" / "imported_input_off_leakage.py"
VIBE = REPO / "docs" / "VIBE_CODE.md"
INDEX_HTML = REPO / "ate" / "ui" / "web" / "index.html"
LIMITS_G07 = REPO / "ate" / "config" / "limits" / "rs1g07.yaml"
PARTS_G07 = REPO / "ate" / "config" / "parts" / "rs1g07.yaml"
PARTS_GT34 = REPO / "ate" / "config" / "parts" / "rs1gt34.yaml"
LIMITS_GT34 = REPO / "ate" / "config" / "limits" / "rs1gt34.yaml"


def _src(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ast_calls_input(src: str) -> bool:
    """Real input() Call nodes only. Docstrings like 'No input().' must not fail."""
    tree = ast.parse(src)
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
        for node in ast.walk(tree)
    )


def _fn_src(src: str, fn_name: str) -> str:
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name:
            return ast.get_source_segment(src, node) or ""
    return ""


def check_add_test() -> list[str]:
    errors: list[str] = []

    detect = _src(DETECT)
    if "trigger_snippet" not in detect or "snippet_map" not in detect:
        errors.append("test_detect must remember snippet_map and trigger_snippet")
    if "imported scaffold -- fill body" in detect:
        errors.append("new wrap must not generate imported scaffold bodies")
    if "update_part_yaml: bool = False" not in detect and "update_part_yaml=False" not in detect:
        errors.append("enable_tests_on_part default must not write shared part yaml")
    if "_SKIP_TEST_NAMES" not in detect or "test_parameter" not in detect:
        errors.append("test_detect must skip test_parameter config helpers")
    if "psu" not in detect or "_INSTR_ARG_NAMES" not in detect:
        errors.append("test_detect must accept psu/dmm handles, not only instr")

    from ate.core.test_detect import enable_tests_on_part, wrap_detected_test

    sig = inspect.signature(enable_tests_on_part)
    default = sig.parameters["update_part_yaml"].default
    if default is not False:
        errors.append(f"update_part_yaml default={default!r} want False")
    doc = wrap_detected_test.__doc__ or ""
    if "imported_<id>.py" not in doc and "imported_" not in doc:
        errors.append("wrap_detected_test docstring must say it does not write imported_<id>.py")
    if "trigger" not in doc.lower() and "remember" not in doc.lower():
        errors.append("wrap_detected_test docstring must say remember/trigger")

    runner = _src(RUNNER)
    if "import ate.tests.opa" in runner:
        errors.append("runner.py must not import family test modules; use load_family")
    elif re.search(r"from ate\.tests\.logic(?!\.(?:product_model|excel_lock))", runner):
        errors.append("runner.py must not import family test modules; use load_family")

    init = _src(LOGIC_INIT)
    if "eugene_cap" not in init:
        errors.append("ate/tests/logic/__init__.py must import eugene_cap or cin/cpd vanish")

    eugene = _src(EUGENE)
    if '"id": "cin"' not in eugene and "id=\"cin\"" not in eugene and "id='cin'" not in eugene:
        errors.append("eugene_cap.py must register TestSpec id cin")
    if "CIN_pF" not in eugene or "CPD_pF" not in eugene:
        errors.append("eugene_cap run() must return measurements ids CIN_pF / CPD_pF")
    if "ICC_uA" not in eugene:
        errors.append("eugene_cap.py IDD must stamp ICC_uA")
    if "ovp=5.5" in eugene:
        errors.append("IDD OVP must be 5.6 V not 5.5 (Vset=OVP trips DP832)")
    if "ovp=5.6" not in eugene:
        errors.append("IDD must pass ovp=5.6")
    if "_psu_ch1_only" not in eugene or "OUTP CH{ch},OFF" not in eugene:
        errors.append("eugene_cap must force PSU CH2/CH3 OFF (Logic CH1 only)")
    if "set_output_load" not in eugene:
        errors.append("eugene_cap AWG must set high-Z load (INF) before square/DC")
    if _ast_calls_input('"""No input()."""\n'):
        errors.append("docstring mention of input() must not count as a call")
    if not _ast_calls_input("x = input('wire')\n"):
        errors.append("real input() call must fail-closed")
    if _ast_calls_input(eugene):
        errors.append("eugene_cap.py must not call input()")

    scaffold = _src(WRAP_SCAFFOLD)
    if "imported scaffold -- fill body" not in scaffold:
        errors.append("imported_input_off_leakage.py is the Path C example; keep fill-body marker")
    if "CIN_pF" in scaffold:
        errors.append("scaffold wrap must not pretend to be a filled CIN body")

    tree = ast.parse(eugene)
    has_register = any(
        isinstance(n, ast.Call) and getattr(n.func, "id", None) == "register"
        for n in ast.walk(tree)
    )
    if not has_register:
        errors.append("eugene_cap.py must call register(TestSpec)")

    vibe = _src(VIBE) if VIBE.is_file() else ""
    if not VIBE.is_file():
        errors.append("docs/VIBE_CODE.md missing")
    else:
        for token in ("Path A", "Path B", "Path C", "measurements", "pause_hook"):
            if token not in vibe:
                errors.append(f"docs/VIBE_CODE.md missing {token!r}")

    if not ATE_PROMPT.is_file() or not ATE_ADD_TEST.is_file():
        errors.append(".cursor/skills/ate-prompt and ate-add-test SKILL.md must exist")
    else:
        add_src = _src(ATE_ADD_TEST)
        for token in ("Path A", "Path B", "Path C", "register(TestSpec)", "pause_hook"):
            if token not in add_src:
                errors.append(f"ate-add-test skill missing {token!r}")

    html = _src(INDEX_HTML)
    if "this Version" not in html:
        errors.append("Tests page must say customize is this Version only")
    if "pointer" not in html.lower() and "snippet" not in html.lower():
        errors.append("Tests page must say scan uses a snippet pointer")
    if "does not rewrite" not in html.lower() and "does not rewrite the golden" not in html.lower():
        if "does not rewrite" not in html.lower():
            errors.append("Tests page must say Remember does not rewrite the golden")
    if 'id="panel-ate-prompt"' not in html or 'id="btn-copy-prompt"' not in html:
        errors.append("Tests page must Copy a filled Path A/B/C Cursor prompt")
    if 'id="panel-write-test"' not in html or 'id="btn-save-path-b"' not in html:
        errors.append("Tests page must Write Path B ate/tests/<id>.py")

    from ate.core.ate_prompt import fill_prompt
    from ate.core.test_detect import path_b_template, save_path_b_test

    prompt = fill_prompt(
        path="b",
        operator="SeeLim",
        family="logic",
        part="rs1g97",
        package="SC70-6",
        version="Version_1",
        test_id="delta_icc",
    )
    for token in ("Path B", "delta_icc", "SeeLim", "runner.py", "pause_hook", "8766"):
        if token not in prompt:
            errors.append(f"cursor prompt missing {token!r}")
    if "input()" not in prompt:
        errors.append("cursor prompt must ban input()")

    try:
        save_path_b_test(
            family="demo_ingest",
            test_id="runner",
            text=path_b_template(test_id="ok_slot", family="demo_ingest")["text"],
        )
        errors.append("save_path_b_test must refuse reserved id runner")
    except ValueError:
        pass
    dirty = "def run(instr, params):\n    x = input('wire')\n    return {}\n"
    try:
        save_path_b_test(family="demo_ingest", test_id="write_probe_tmp", text=dirty)
        errors.append("save_path_b_test must refuse input()")
    except ValueError:
        pass

    tid = "write_probe_tmp"
    pkg = REPO / "ate" / "tests" / "demo_ingest"
    dest = pkg / f"{tid}.py"
    demo_init = pkg / "__init__.py"
    demo_init_before = demo_init.read_text(encoding="utf-8") if demo_init.is_file() else ""
    try:
        body = path_b_template(test_id=tid, label="Write probe", family="demo_ingest")["text"]
        if "pause_hook" not in body or "power_on_protected" not in body:
            errors.append("path_b_template must include pause_hook and power_on_protected")
        out = save_path_b_test(
            family="demo_ingest",
            test_id=tid,
            text=body,
            enable_part="",
        )
        if not dest.is_file():
            errors.append("save_path_b_test must write ate/tests/demo_ingest/write_probe_tmp.py")
        if "runner.py" in str(out.get("file") or ""):
            errors.append("save_path_b_test must not write runner.py")
        from ate.core.registry import all_tests, load_family

        load_family("demo_ingest")
        if tid not in {t.id for t in all_tests()}:
            errors.append("save_path_b_test must register write_probe_tmp in demo_ingest")
    except Exception as exc:
        errors.append(f"save_path_b_test write_probe_tmp failed: {exc}")
    finally:
        if dest.is_file():
            dest.unlink()
        demo_init.write_text(
            demo_init_before if demo_init_before.endswith("\n") else demo_init_before + "\n",
            encoding="utf-8",
        )

    parts = _src(PARTS_G07)
    if "cin" not in parts or "cpd" not in parts:
        errors.append("rs1g07.yaml enabled_tests must list cin and cpd (Path B shared recipe)")

    from ate.tests.logic.product_model import has_product_model

    if not has_product_model("rs1gt34"):
        gt34 = _src(PARTS_GT34)
        for token in ("- vih_vil", "- voh_load", "- vol_load"):
            if token not in gt34:
                errors.append(f"rs1gt34.yaml missing {token}")
        i_vih = gt34.find("- vih_vil")
        i_tp = gt34.find("\n  - tp")
        if i_vih < 0 or i_tp < 0 or i_vih > i_tp:
            errors.append("rs1gt34.yaml must list vih_vil/voh/vol before tp")
        if "logic_inputs: 1" not in gt34:
            errors.append("rs1gt34.yaml must set logic_inputs: 1 (single buffer)")
        list_line = gt34.split("vih_vil_vcc_list:", 1)[-1].split("\n", 1)[0]
        if "3.5" in list_line:
            errors.append("rs1gt34 vih_vil_vcc_list must not include 3.5")
        if "package: SOT23-5" not in gt34:
            errors.append("rs1gt34.yaml package must be SOT23-5 (not SOT-353)")
        if "vih_vil_stimulus: psu_mso" not in gt34:
            errors.append("rs1gt34 vih_vil must set vih_vil_stimulus: psu_mso")
        if "vih_vil_vcc_range:" not in gt34:
            errors.append("rs1gt34 must declare vih_vil_vcc_range (4.5-5.5)")
        if "vin_step: 0.01" not in gt34:
            errors.append("rs1gt34 Parameters must default vin_step 0.01 (millivolt-class VIN)")
        if "step: 0.1" not in gt34.split("vih_vil_vcc_range:", 1)[-1].split("\n", 1)[0]:
            errors.append("rs1gt34 vih_vil_vcc_range CH1 VCC default step must be 0.1")

    vih_fn = _fn_src(_src(REPO / "ate" / "tests" / "logic" / "ariff_dc.py"), "_run_vih_vil")
    if "psu_mso" not in vih_fn or "MSO" not in vih_fn:
        errors.append("_run_vih_vil must support PSU CH2 + MSO CH1 path")
    if "_search_vin_trip" not in vih_fn or "_record_v" not in vih_fn:
        errors.append("_run_vih_vil must coarse-to-fine VIN search and record 6 dp")
    search_fn = _fn_src(_src(REPO / "ate" / "tests" / "logic" / "ariff_dc.py"), "_search_vin_trip")
    if "_interp_cross" not in search_fn:
        errors.append("_search_vin_trip must interpolate trip volts (more decimals than the 0.01 step)")

    from ate.tests.logic.ariff_dc import _search_vin_trip, _vin_step_ladder

    lad_hi = _vin_step_ladder(2.0, 0.01)
    if lad_hi[0] - 0.5 > 1e-9 or 0.01 not in lad_hi:
        errors.append("VIN ladder at VIH=2.0 must start at 0.5 and end at 0.01")
    lad_lo = _vin_step_ladder(0.3, 0.01)
    if lad_lo[0] > 0.2 + 1e-9:
        errors.append("VIN ladder at VIH=0.3 must start finer than 0.2 (limit-scaled)")

    def _probe(trip: float, vcc: float, invert: bool, vin_up: bool) -> None:
        sets: list[float] = []

        def set_vin(v: float) -> None:
            sets.append(float(v))

        def read_y() -> float:
            vin = sets[-1]
            hi = vcc if not invert else 0.0
            lo = 0.0 if not invert else vcc
            if vin_up:
                return hi if vin >= trip else lo
            return hi if vin >= trip else lo

        arm = 0.0 if vin_up else vcc
        stop = vcc if vin_up else 0.0
        hint = 2.0 if vin_up else 0.8
        got, n = _search_vin_trip(
            set_vin,
            read_y,
            arm=arm,
            stop=stop,
            mid=vcc / 2.0,
            vin_up=vin_up,
            invert=invert,
            hint=hint,
            fine=0.01,
            dwell=0.0,
            trace=sets if False else None,
        )
        if got is None or abs(float(got) - trip) > 0.012:
            errors.append(
                f"search miss vin_up={vin_up} invert={invert} want {trip} got {got}"
            )
        if n > 120:
            errors.append(f"search too many VIN sets n={n} (must skip after hit)")
        stage: list[float] = []
        arm_v = arm
        for v in sets:
            if stage and abs(v - arm_v) < 1e-12:
                d = [stage[i + 1] - stage[i] for i in range(len(stage) - 1)]
                if vin_up and any(x < -1e-9 for x in d):
                    errors.append("VIH stage reversed VIN (must 0 -> 1)")
                if (not vin_up) and any(x > 1e-9 for x in d):
                    errors.append("VIL stage reversed VIN (must 1 -> 0)")
                stage = [v]
            else:
                stage.append(v)
        if n < 6:
            errors.append(f"search too thin n={n}")
        if stage:
            d = [stage[i + 1] - stage[i] for i in range(len(stage) - 1)]
            if vin_up and any(x < -1e-9 for x in d):
                errors.append("VIH last stage reversed VIN")
            if (not vin_up) and any(x > 1e-9 for x in d):
                errors.append("VIL last stage reversed VIN")

    _probe(1.23, 5.5, False, True)
    _probe(1.23, 5.5, False, False)
    _probe(1.23, 5.5, True, True)
    _probe(0.22, 2.0, False, True)
    _probe(2.40, 5.5, False, True)
    gt34_src = _src(PARTS_GT34)
    if not has_product_model("rs1gt34"):
        enabled_only = gt34_src.split("enabled_tests:", 1)[-1].split("fixture_modes:", 1)[0]
        if "\n  - ten" in enabled_only or "\n  - tdis" in enabled_only:
            errors.append("rs1gt34 has no OE -- do not enable ten/tdis")
        for tid in ("- cin", "- cpd", "- ioff_leakage"):
            if tid not in enabled_only:
                errors.append(f"rs1gt34 lab book has CIN/CPD/IOFF -- enable {tid.strip('- ')}")
    else:
        from ate.fixture.modes import enabled_tests_for_part as _en_part

        en34 = _en_part("rs1gt34") or []
        for need in ("input_threshold", "icc", "ii", "voh", "vol", "delta_icc"):
            if need not in en34:
                errors.append(f"rs1gt34 Path B must enable {need}")
        if "ten" in en34 or "tdis" in en34:
            errors.append("rs1gt34 has no OE -- do not enable ten/tdis")

    limits = _src(LIMITS_G07)
    if "CIN_pF" not in limits or "CPD_pF" not in limits:
        errors.append("rs1g07 limits specs.id must include CIN_pF and CPD_pF")
    lim34 = _src(LIMITS_GT34)
    if "VOH_2p0V" not in lim34 or "VOL_5p0V" not in lim34:
        errors.append("rs1gt34 limits must include datasheet VOH_2p0V / VOL_5p0V")

    from ate.core.registry import all_tests, load_family

    load_family("logic")
    ids = {t.id for t in all_tests()}
    for tid in ("cin", "cpd", "input_off_leakage", "vih", "tp_rs0204", "clk_q", "pulse_width", "serial_shift", "ioz", "i2c_ii", "i2c_ron", "i2c_cioff"):
        if tid not in ids:
            errors.append(f"load_family(logic) missing {tid}")
    if "clk_q" not in init:
        errors.append("ate/tests/logic/__init__.py must import clk_q")
    if "pulse_width" not in init:
        errors.append("ate/tests/logic/__init__.py must import pulse_width")
    if "serial_shift" not in init:
        errors.append("ate/tests/logic/__init__.py must import serial_shift")
    if "rs0302" not in init:
        errors.append("ate/tests/logic/__init__.py must import rs0302")

    rs0204 = _src(REPO / "ate" / "tests" / "logic" / "rs0204.py")
    if 'f"{key}_V"' not in rs0204 and "VIH_V" not in rs0204:
        errors.append("rs0204.py Path B must stamp VIH_V / VIL_V")
    if "0.65" not in rs0204 or "0.35" not in rs0204:
        errors.append("rs0204 vih/vil must apply 0.65/0.35 * VCCA (not trip vs VIH min)")
    if '_FIXTURE = "LOGIC"' not in rs0204:
        errors.append("rs0204 dual-rail must stay LOGIC fixture (not BUFFER)")
    if re.search(r"^\s*(import Soo|from Soo)", rs0204, re.M):
        errors.append("rs0204.py must not import Soo")
    if "CIO_A_pF" not in rs0204:
        errors.append("rs0204 cpd must stamp CIO_A_pF (pin Cio, not dynamic CPD_pF)")
    eugene_cap_src = _src(EUGENE)
    if "rs0204" not in eugene_cap_src or "_run_cpd" not in eugene_cap_src:
        errors.append("eugene_cap.run_cpd must dispatch rs0204 pin Cio (_run_cpd)")
    if "TSU_ns" in rs0204:
        errors.append("rs0204 tsu must stamp TEN_ns (MSO OE delay), not invent TSU_ns")
    if "TEN_ns" not in rs0204 or "TDIS_ns" not in rs0204:
        errors.append("rs0204 tsu/th must stamp MSO OE delay as TEN_ns/TDIS_ns")
    sim_src = _src(REPO / "ate" / "instruments" / "sim.py")
    if "v2 > vcc + 0.05" not in sim_src or "v2 >= 1.2" not in sim_src:
        errors.append("SIM DMM xlat must require VCCB rail (v2 > vcc and v2 >= 1.2), not Ariff VOH Vref")
    if "_ch2_oe_dc" not in sim_src or '!= "DC"' not in sim_src:
        errors.append("SIM MSO CHAN2 must not follow AWG CH2 DC (OE); USB CHAN2 is DUT Y")
    if "_MSO_TR_S" not in sim_src:
        errors.append("SIM RTime/FTime must use MSO 70 MHz ceiling, not 0.12 s dummy")

    rs0302 = _src(REPO / "ate" / "tests" / "logic" / "rs0302.py")
    if "II_uA" not in rs0302 or "CIOFF_pF" not in rs0302:
        errors.append("rs0302.py must stamp II_uA and CIOFF_pF")
    if "64 mA" not in rs0302:
        errors.append("rs0302 RON must name 64 mA leftover (platform 10 mA)")
    if _ast_calls_input(rs0302):
        errors.append("rs0302.py must not call input()")
    from ate.fixture.modes import enabled_tests_for_part as _en_part

    en0302 = _en_part("rs0302") or []
    if en0302 != ["i2c_ii", "i2c_ron", "i2c_cioff"]:
        errors.append(f"rs0302 enabled_tests must be I2C suite, got {en0302}")
    for banned in ("vih", "vil", "voh", "vol", "vih_vil", "voh_load"):
        if banned in en0302:
            errors.append(f"rs0302 must not copy RS0204/Ariff {banned}")

    claude = REPO / "CLAUDE.md"
    ai_md = REPO / "AI.md"
    if not claude.is_file() or not ai_md.is_file():
        errors.append("CLAUDE.md and AI.md must exist (always-on system prompt)")
    else:
        blob = claude.read_text(encoding="utf-8") + ai_md.read_text(encoding="utf-8")
        if "AGENTS.md" not in blob or "paste" not in blob.lower():
            errors.append("CLAUDE.md/AI.md must point at AGENTS.md and forbid paste-copilot")

    from ate.fixture.modes import enabled_tests_for_part

    catalog = {"enabled_tests": ["cin"]}
    got = enabled_tests_for_part("rs1g07", catalog=catalog)
    if got != ["cin"]:
        errors.append(f"catalog must win over part yaml, got {got!r}")

    errors.extend(_check_ariff_dc_scale())
    errors.extend(_check_path_b_integrity())
    return errors


def _registered_ids() -> set[str]:
    from ate.core.registry import FAMILY_PACKAGES, _load_extra_families, load_family_tests, refresh_family_table

    refresh_family_table()
    ids: set[str] = set()
    fams = set(FAMILY_PACKAGES.keys()) | set(_load_extra_families().keys()) | {"demo_ingest"}
    for fam in fams:
        try:
            for spec in load_family_tests(fam):
                ids.add(spec.id)
        except Exception:
            pass
    return ids


def _check_path_b_integrity() -> list[str]:
    """Path B ids in parts yaml; repo snippet_map pointers; no input() in register run."""
    import yaml

    from ate.core.registry import load_family_tests

    errors: list[str] = []
    registered = _registered_ids()
    for part_yaml in sorted((REPO / "ate" / "config" / "parts").glob("*.yaml")):
        data = yaml.safe_load(part_yaml.read_text(encoding="utf-8")) or {}
        for tid in data.get("enabled_tests") or []:
            tid_s = str(tid or "").strip()
            if tid_s and tid_s not in registered:
                errors.append(
                    f"{part_yaml.name} enabled_tests {tid_s!r} not registered (Path B)"
                )

    smap_path = REPO / "ate" / "config" / "snippet_map.yaml"
    if smap_path.is_file():
        smap = yaml.safe_load(smap_path.read_text(encoding="utf-8")) or {}

        def _repo_snippet_path(fp: str) -> Path | None:
            raw = str(fp or "").strip().replace("\\", "/")
            if not raw:
                return None
            if raw.startswith("ate/"):
                return REPO / raw
            if "ate/tests/" in raw:
                tail = raw.split("ate/tests/", 1)[-1]
                return REPO / "ate" / "tests" / tail
            if raw.startswith("goldens/"):
                return REPO / raw
            return None

        for sn in smap.get("snippets") or []:
            if not isinstance(sn, dict):
                continue
            fp = str(sn.get("file") or "")
            p = _repo_snippet_path(fp)
            if p is None:
                continue
            sid = sn.get("id") or fp
            if not p.is_file():
                errors.append(f"snippet_map {sid} repo file missing: {fp}")
                continue
            ln = int(sn.get("lineno") or 0)
            nlines = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            if ln < 1 or ln > nlines:
                errors.append(f"snippet_map {sid} lineno {ln} out of range ({nlines} lines)")

    for fam in ("opamp", "logic", "switch", "level", "power", "demo_ingest"):
        try:
            specs = load_family_tests(fam)
        except Exception:
            continue
        for spec in specs:
            try:
                run_src = inspect.getsource(spec.run)
            except (OSError, TypeError, SyntaxError, IndentationError):
                continue
            try:
                bad = _ast_calls_input(run_src)
            except SyntaxError:
                continue
            if bad:
                errors.append(f"registered {spec.id} run() calls input()")

    scaffold = _src(WRAP_SCAFFOLD)
    if "imported scaffold -- fill body" not in scaffold:
        errors.append("imported_input_off_leakage.py must keep fill-body honesty marker")

    return errors


def _check_ariff_dc_scale() -> list[str]:
    """Existing Ariff DC ids on Logic SKUs that datasheets already include.

    Skip Soo / dual-rail / DFF / shift / mono. Do not rewrite Eugene cin/cpd.
    """
    from ate.core.specs import load_part_specs, load_part_yaml
    from ate.fixture.modes import enabled_tests_for_part
    from ate.tests.logic.product_model import has_product_model

    errors: list[str] = []
    path_b = {p.stem for p in (REPO / "ate" / "config" / "parts").glob("*.yaml") if has_product_model(p.stem)}
    skip = ("rs29511", "rs0204", "rs0302", "rs1g74", "rs164", "rs1g123")
    for pk in skip:
        en = set(enabled_tests_for_part(pk) or [])
        for banned in ("vih_vil", "voh_load", "vol_load", "supply_current_sweep"):
            if banned in en:
                errors.append(f"{pk} must not dump Ariff {banned}")

    push = (
        "rs1g08",
        "rs1g14",
        "rs1g32",
        "rs1g125",
        "rs1gt08",
        "rs1gt32",
        "rs1gt32d",
        "rs1gt34",
    )
    for pk in push:
        if pk in path_b:
            continue
        en = enabled_tests_for_part(pk) or []
        if en[:3] != ["vih_vil", "voh_load", "vol_load"]:
            errors.append(
                f"{pk} must list vih_vil, voh_load, vol_load first, got {en[:5]}"
            )

    g07 = enabled_tests_for_part("rs1g07") or []
    if "rs1g07" in path_b:
        if "cin" not in g07 or "cpd" not in g07:
            errors.append("rs1g07 must keep Eugene cin/cpd")
    else:
        if g07[:2] != ["vih_vil", "vol_load"]:
            errors.append(f"rs1g07 open-drain must start vih_vil, vol_load, got {g07[:4]}")
        if "voh_load" in g07:
            errors.append("rs1g07 open-drain must not enable voh_load")
        if "cin" not in g07 or "cpd" not in g07:
            errors.append("rs1g07 must keep Eugene cin/cpd")

    aup = enabled_tests_for_part("rs74aup1g07") or []
    if "vih_vil" not in aup:
        errors.append("rs74aup1g07 must enable vih_vil")
    if "voh_load" in aup or "vol_load" in aup:
        errors.append("rs74aup1g07 must not copy G-family VOH/VOL until PDF")
    from ate.core.physics_scale import classify_one as _phys_one

    aup_st, _ = _phys_one("rs74aup1g07", "vih_vil")
    if aup_st != "REALIZED":
        errors.append("rs74aup1g07 vih_vil is Ariff Path B 1.8/2.5/3.3; do not leftover the VIH body")
    ariff_src = _src(REPO / "ate" / "tests" / "logic" / "ariff_dc.py")
    if "yaml_explicit" not in ariff_src or "max(listed) < 4.5" not in ariff_src:
        errors.append("vih_vil must not append 4.5..5.5 when yaml list is low-only (AUP)")
    eug_src = _src(EUGENE)
    if "vih_vil_vcc_list" not in eug_src or "max(listed) < 4.5" not in eug_src:
        errors.append("eugene IDD must honor yaml low-only VCC (AUP) instead of inventing 5.5")
    from ate.core.runner import RunParams
    from ate.tests.logic.eugene_cap import _idd_vccs

    aup_idd = _idd_vccs(RunParams(part="rs74aup1g07"))
    if not aup_idd or max(aup_idd) >= 4.5 - 1e-9:
        errors.append(f"AUP IDD VCC must stay below 4.5, got {aup_idd}")
    g07_idd = _idd_vccs(RunParams(part="rs1g07"))
    if 5.5 not in g07_idd:
        errors.append(f"RS1G07 IDD must keep 5.5 V corner, got {g07_idd}")
    settle_src = _src(REPO / "ate" / "tests" / "opa" / "settling.py")
    if "SETTLE_us" in settle_src:
        errors.append("settling must not stamp MSO delay as SETTLE_us")
    if "SETTLE_VPP_V" not in settle_src:
        errors.append("settling leftover must stamp SETTLE_VPP_V (CHAN2 swing)")
    settle_spec = next((s for s in load_part_specs("rs622") if s.get("id") == "SETTLE_VPP_V"), None)
    if not settle_spec or settle_spec.get("test") != "settling":
        errors.append("SETTLE_VPP_V spec must bind test: settling")
    if settle_spec and (settle_spec.get("min") is not None or settle_spec.get("max") is not None):
        errors.append("do not invent SETTLE_us min/max on SETTLE_VPP_V")
    iso_src = _src(REPO / "ate" / "tests" / "lim" / "iso.py")
    if "1 MHz" not in iso_src and "1_000_000" not in iso_src:
        errors.append("iso Path B must stay 1 MHz high-Z, not 110 MHz RF")

    g14 = load_part_yaml("rs1g14")
    en14 = g14.get("enabled_tests") or []
    if "ten" in en14 or "tdis" in en14:
        errors.append("rs1g14 has no OE -- do not enable ten/tdis")
    if int(g14.get("logic_inputs") or 0) != 1:
        errors.append("rs1g14 Schmitt inverter must set logic_inputs: 1")
    if not g14.get("y_invert"):
        errors.append("rs1g14 Schmitt inverter must set y_invert: true")
    from ate.core.paths import PARTS_DIR

    for path in sorted(PARTS_DIR.glob("*.yaml")):
        pk = path.stem.lower()
        if pk == "rs1g14":
            continue
        if load_part_yaml(pk).get("y_invert"):
            errors.append(f"{pk} must not set y_invert (not an inverter)")
    ariff_src = _src(REPO / "ate" / "tests" / "logic" / "ariff_dc.py")
    if "0.0 if invert else vcc" not in ariff_src:
        errors.append("inverter VOH must drive A=0, not A=VCC")
    if "vcc if invert else 0.0" not in ariff_src:
        errors.append("inverter VOL must drive A=VCC, not A=0")
    voh_fn = _fn_src(ariff_src, "_run_voh_load")
    vol_fn = _fn_src(ariff_src, "_run_vol_load")
    pi_h = voh_fn.find("_pause_voh_vol(params, high=True)")
    po_h = voh_fn.find("power_on_protected")
    pi_l = vol_fn.find("_pause_voh_vol(params, high=False)")
    po_l = vol_fn.find("power_on_protected")
    if pi_h < 0 or po_h < 0 or pi_h > po_h:
        errors.append("voh_load must Continue-wait before PSU on (VOH wiring)")
    if pi_l < 0 or po_l < 0 or pi_l > po_l:
        errors.append("vol_load must Continue-wait before PSU on (VOL wiring differs)")
    if "same wiring as voh_load" in vol_fn:
        errors.append("vol_load must not claim same wiring as VOH")
    if "VOH load (not VOL)" not in ariff_src or "VOL load (not VOH)" not in ariff_src:
        errors.append("VOH/VOL pause text must say the setups differ")
    rs0204_src = _src(REPO / "ate" / "tests" / "logic" / "rs0204.py")
    vohvol_fn = _fn_src(rs0204_src, "_run_voh_vol")
    if vohvol_fn.find("_pause(") < 0 or vohvol_fn.find("_pause(") > vohvol_fn.find("setup_dc"):
        errors.append("rs0204 voh/vol must Continue-wait before drive")
    for pk in (
        "rs1g07",
        "rs1g08",
        "rs1g14",
        "rs1g32",
        "rs1g125",
        "rs1gt08",
        "rs1gt32",
        "rs1gt32d",
        "rs1gt34",
        "rs0204",
    ):
        en = enabled_tests_for_part(pk) or []
        if not any(t in en for t in ("voh_load", "vol_load", "voh", "vol")):
            continue
        text = (PARTS_DIR / f"{pk}.yaml").read_text(encoding="utf-8")
        if "Continue waits before" not in text:
            errors.append(
                f"{pk}: checklist must say Continue waits before VOH/VOL "
                "(setups differ on every logic board)"
            )

    for pk in ("rs1gt08", "rs1gt32", "rs1gt32d", "rs1gt34"):
        cfg = load_part_yaml(pk)
        for row in cfg.get("voh_table") or []:
            if not isinstance(row, dict):
                continue
            if float(row.get("vcc") or 0) < 1.99:
                errors.append(f"{pk} GT voh_table must not include {row.get('vcc')}")
    gt34 = load_part_yaml("rs1gt34")
    iohs = [
        float(r.get("ioh_a") or 0)
        for r in (gt34.get("voh_table") or [])
        if isinstance(r, dict)
    ]
    if not any(abs(i) <= 0.00015 for i in iohs):
        errors.append("rs1gt34 voh_table must include IOH=-100uA (MIN VCC-0.1)")
    if "voh_100ua" not in gt34:
        errors.append("rs1gt34 must declare voh_100ua (false until current source can sink 100uA)")

    for pk in ("rs1gt08", "rs1gt32"):
        en = enabled_tests_for_part(pk) or []
        if "cin" not in en or "cpd" not in en:
            errors.append(f"{pk} must enable existing cin/cpd")
        if "tdis" in en or "ten" in en:
            errors.append(f"{pk} has no OE -- do not enable ten/tdis")
    g08 = enabled_tests_for_part("rs1g08") or []
    if "tdis" in g08 or "ten" in g08:
        errors.append("rs1g08 AND has no OE -- do not enable ten/tdis")

    ariff = _src(REPO / "ate" / "tests" / "logic" / "ariff_dc.py")
    if "OVP_ABS_MAX_V" not in ariff:
        errors.append(
            "ariff_dc vih_vil must cap OVP at OVP_ABS_MAX_V "
            "(5.5*1.1=6.05 trips the 6.0 V DUT ceiling)"
        )
    if _ast_calls_input(ariff):
        errors.append("ariff_dc.py must not call input()")
    if '"ioz"' not in ariff and "'ioz'" not in ariff:
        errors.append("ariff_dc.py must register TestSpec id ioz")
    if "IOZ_uA" not in ariff:
        errors.append("ioz must stamp measurements id IOZ_uA")
    if "OFF_uA" not in ariff:
        errors.append("off_current must stamp measurements id OFF_uA")
    if "_load_meas_id" not in ariff or "100uA" not in ariff:
        errors.append("voh_load must stamp VOH_*_100uA vs high-current VOH_*V")
    if "_include_100ua" not in ariff or "_skip_100ua_rows" not in ariff:
        errors.append("voh/vol 100uA must be skippable (_include_100ua) until the current source can sink it")
    if "VCC_meas" not in ariff:
        errors.append("100uA VOH must measure VCC then MIN=VCC-0.1 (not a hardcoded 5.4)")
    voh_fn = _fn_src(ariff, "_run_voh_load") if "_run_voh_load" in ariff else ""
    vol_fn = _fn_src(ariff, "_run_vol_load") if "_run_vol_load" in ariff else ""
    if "power_off(instr.psu)" in voh_fn:
        errors.append("voh_load must not full power_off between corners (VISA SYSTEM_ERROR)")
    if "power_off(instr.psu)" in vol_fn:
        errors.append("vol_load must not full power_off between corners (VISA SYSTEM_ERROR)")
    if "setup=False" not in voh_fn or "dmm_setup_voltage" not in voh_fn:
        errors.append("voh_load must CONF DMM once then :READ? (not RANG AUTO every sample)")
    ldo = _src(REPO / "ate" / "tests" / "power" / "ldo.py")
    for mid in ("VINMIN_V", "LIR_mV", "LOR_mV", "IOUTMAX_V", "IEN_uA", "IQ_uA"):
        if mid not in ldo:
            errors.append(f"ldo.py must stamp measurements id {mid}")
    if "set_ldo_dut" not in ldo:
        errors.append("ldo.py must arm SIM LDO DUT so DMM READ? is VOUT")
    if "min(vins)" in ldo:
        errors.append("ldo.py must not VIN-stamp IOUTMAX when DMM is on VOUT")
    iq_fn = _fn_src(ldo, "_run_iq") if "_run_iq" in ldo else ""
    if "_arm_ldo" not in iq_fn:
        errors.append("ldo IQ must arm SIM LDO so DMM current follows VIN not VOUT-bias")
    if 'meas.append({"id": "VOUT_V"' in iq_fn:
        errors.append("ldo IQ must not stamp yaml VOUT_V (DMM is current)")
    for pk in ("rs1g125",):
        en = enabled_tests_for_part(pk) or []
        if "ioz" not in en:
            errors.append(f"{pk} 3-state must enable ioz")
        if "ten" not in en or "tdis" not in en:
            errors.append(f"{pk} 3-state must enable Path B ten/tdis")
        cfg = load_part_yaml(pk)
        if str(cfg.get("oe_active") or "").strip().lower() != "low":
            errors.append(f"{pk} /OE must set oe_active low")

    g97 = enabled_tests_for_part("rs1g97") or []
    for banned in ("vih_vil", "input_thresholds", "voh_load", "vol_load", "cin", "cpd", "tp", "ten", "tdis"):
        if banned in g97:
            errors.append(f"rs1g97 must not dump {banned} -- SeeLim tree has no such test_*")
    for need in ("icc", "delta_icc", "ii", "input_threshold"):
        if need not in g97:
            errors.append(f"rs1g97 must enable SeeLim original {need}")
    if "ioz" in g97:
        errors.append("rs1g97 has no OE -- do not enable ioz")

    g126 = enabled_tests_for_part("rs1g126") or []
    for banned in ("vih_vil", "input_thresholds", "voh_load", "vol_load", "cin", "cpd", "tp"):
        if banned in g126:
            errors.append(f"rs1g126 must not dump {banned} -- no VOH/CIN in SeeLim tree")
    for need in ("ioff", "ioz", "icc", "ii", "delta_icc", "input_threshold", "ten", "tdis"):
        if need not in g126:
            errors.append(f"rs1g126 must enable SeeLim original or Path B {need}")
    cfg126 = load_part_yaml("rs1g126")
    if str(cfg126.get("oe_active") or "").strip().lower() != "high":
        errors.append("rs1g126 must set oe_active high")
    oe_src = _src(REPO / "ate" / "tests" / "logic" / "oe_timing.py")
    if "TEN_ns" not in oe_src or "TDIS_ns" not in oe_src:
        errors.append("oe_timing must stamp TEN_ns / TDIS_ns")
    if "oe_active" not in oe_src:
        errors.append("oe_timing must branch on part yaml oe_active")
    if _ast_calls_input(oe_src):
        errors.append("oe_timing.py must not call input()")
    if "test_ten" in oe_src or "logic_tests" in oe_src:
        errors.append("oe_timing must not wrap Ariff logic_tests.test_ten")
    if "rs29511" not in oe_src or "READY" not in oe_src:
        errors.append("oe_timing must Path B RS29511 EN->READY (not 3-state Y)")
    if "Soo." in oe_src:
        errors.append("oe_timing must not import Soo.*")
    g295 = enabled_tests_for_part("rs29511") or []
    for need in ("ten", "tdis", "tp", "tidle"):
        if need not in g295:
            errors.append(f"rs29511 must enable Path B {need}")
    prop_src = _src(REPO / "ate" / "tests" / "logic" / "rs29511_prop.py")
    if "TPD_PHL_ns" not in prop_src or "TIDLE_PHL_ns" not in prop_src:
        errors.append("rs29511_prop must stamp TPD_PHL_ns / TIDLE_PHL_ns")
    if "logic_tests" in prop_src or "Soo." in prop_src:
        errors.append("rs29511_prop must not wrap Soo logic_tests")
    if _ast_calls_input(prop_src):
        errors.append("rs29511_prop.py must not call input()")
    if "register(" in prop_src:
        errors.append("rs29511_prop must not register tp/tidle (wraps owns the id)")
    wraps_src = _src(REPO / "ate" / "tests" / "logic" / "wraps.py")
    if "rs29511_prop" not in wraps_src:
        errors.append("wraps tp/tidle must route rs29511 to rs29511_prop")
    if "cmos_prop" not in wraps_src:
        errors.append("wraps tp/tidle must route combinational CMOS to cmos_prop")
    if "from logic_tests" in wraps_src or "import logic_tests" in wraps_src:
        errors.append("wraps must not import repo-root logic_tests")
    cmos_src = _src(REPO / "ate" / "tests" / "logic" / "cmos_prop.py")
    if "TPD_PHL_ns" not in cmos_src or "cmos_prop" not in cmos_src:
        errors.append("cmos_prop must stamp TPD_PHL_ns")
    if "logic_tests" in cmos_src or "Soo." in cmos_src:
        errors.append("cmos_prop must not wrap logic_tests")
    if _ast_calls_input(cmos_src):
        errors.append("cmos_prop.py must not call input()")
    if "register(" in cmos_src:
        errors.append("cmos_prop must not register tp (wraps owns the id)")
    if "setup_square(instr.gen, 2" in cmos_src:
        errors.append("cmos_prop must not reverse-drive AWG CH2 (that is B, not Y->A)")
    dc_src = _src(REPO / "ate" / "tests" / "logic" / "rs29511_dc.py")
    if "ICC_uA" not in dc_src or "VOUT_V" not in dc_src or "CAP_pF" not in dc_src:
        errors.append("rs29511_dc must stamp ICC_uA / VOUT_V / CAP_pF")
    if "logic_tests" in dc_src or "Soo." in dc_src:
        errors.append("rs29511_dc must not wrap Soo logic_tests")
    if _ast_calls_input(dc_src):
        errors.append("rs29511_dc.py must not call input()")
    if "register(" in dc_src:
        errors.append("rs29511_dc must not register supply_current (wraps owns the id)")
    if "1.65" in dc_src:
        errors.append("rs29511_dc ICC must not use CMOS 1.65 V (PDF min 2.3 V)")
    if "rs29511_dc" not in wraps_src:
        errors.append("wraps must route rs29511 ICC/READY/Cio to rs29511_dc")
    for need in ("supply_current", "output_voltage", "cap_load"):
        if need not in g295:
            errors.append(f"rs29511 must enable Path B {need}")
    vos_src = _src(REPO / "ate" / "tests" / "opa" / "vos.py")
    if "VOS_mV" not in vos_src or "CHAN2" not in vos_src:
        errors.append("vos_sweep Path B must stamp VOS_mV from MSO CHAN2")
    if "from opa_tests" in vos_src or "import opa_tests" in vos_src:
        errors.append("vos_sweep must not wrap opa_tests.test_vos_sweep (CHAN1=AWG)")
    if _ast_calls_input(vos_src):
        errors.append("vos.py must not call input()")
    if "g201_vos" not in vos_src:
        errors.append("vos_sweep must flag g201_vos Path B")
    acg_src = _src(REPO / "ate" / "tests" / "opa" / "ac_gain.py")
    if "GAIN_VV" not in acg_src or "CHAN2" not in acg_src:
        errors.append("ac_gain_check Path B must stamp GAIN_VV from MSO CHAN2")
    if "from opa_tests" in acg_src or "import opa_tests" in acg_src:
        errors.append("ac_gain_check must not wrap opa_tests (CHAN1=AWG)")
    if _ast_calls_input(acg_src):
        errors.append("ac_gain.py must not call input()")
    if "g201_ac" not in acg_src:
        errors.append("ac_gain_check must flag g201_ac Path B")
    acv_src = _src(REPO / "ate" / "tests" / "opa" / "ac_vin.py")
    if "GAIN_VV" not in acv_src or "CHAN2" not in acv_src:
        errors.append("ac_vin_sweep Path B must stamp GAIN_VV from MSO CHAN2")
    if "from opa_tests" in acv_src or "import opa_tests" in acv_src:
        errors.append("ac_vin_sweep must not wrap opa_tests (CHAN1=AWG)")
    if _ast_calls_input(acv_src):
        errors.append("ac_vin.py must not call input()")
    if "g201_ac" not in acv_src:
        errors.append("ac_vin_sweep must flag g201_ac Path B")
    gain_spec = next((s for s in load_part_specs("rs622") if s.get("id") == "GAIN_VV"), None)
    if not gain_spec or gain_spec.get("test") != "ac_gain_check":
        errors.append("GAIN_VV spec must bind test: ac_gain_check")
    if gain_spec and (gain_spec.get("min") is not None or gain_spec.get("max") is not None):
        errors.append("do not invent GAIN_VV min/max (closed-loop board, not AOL_dB)")
    from ate.core.physics_scale import check_physics_scale

    errors.extend(check_physics_scale())

    for pk in ("rs164", "rs1g74", "rs1g123"):
        en = enabled_tests_for_part(pk) or []
        if "tp" in en:
            errors.append(f"{pk} must not enable combinational tp wrap")
        if "cin" not in en or "cpd" not in en or "ioff_leakage" not in en:
            errors.append(f"{pk} must enable cin/cpd/ioff_leakage (input physics)")
    g74 = enabled_tests_for_part("rs1g74") or []
    if "clk_q" not in g74:
        errors.append("rs1g74 DFF must enable Path B clk_q (not combinational tp)")
    if "clk_q" not in (enabled_tests_for_part("rs164") or []):
        errors.append("rs164 must enable clk_q (CLK to Q0)")
    if "serial_shift" not in (enabled_tests_for_part("rs164") or []):
        errors.append("rs164 must enable Path B serial_shift (8 CLK then Q7)")
    if "serial_shift" in (enabled_tests_for_part("rs1g74") or []):
        errors.append("rs1g74 DFF must not enable RS164 serial_shift")
    if "pulse_width" not in (enabled_tests_for_part("rs1g123") or []):
        errors.append("rs1g123 must enable Path B pulse_width")

    en2323 = enabled_tests_for_part("rs2323") or []
    if "ron" not in en2323:
        errors.append("rs2323 must enable Path B ron")
    if "ton_toff" not in en2323:
        errors.append("rs2323 must enable Path B ton_toff")
    if "con_coff" not in en2323 or "tbbm" not in en2323:
        errors.append("rs2323 must enable Path B con_coff and tbbm")
    if "vth" not in en2323:
        errors.append("rs2323 must enable Path B vth")
    en2227 = enabled_tests_for_part("rs2227") or []
    if any(x in en2227 for x in ("ron", "ton_toff", "con_coff", "tbbm", "vth", "iso", "xtalk")):
        errors.append("rs2227 must not enable RS2323-pinout analog tests until USB recipe")
    if "iso" not in en2323:
        errors.append("rs2323 must enable Path B iso")
    if "xtalk" not in en2323:
        errors.append("rs2323 must enable Path B xtalk")
    iso_src = _src(REPO / "ate" / "tests" / "lim" / "iso.py")
    if "ISO_dB" not in iso_src:
        errors.append("iso must stamp ISO_dB")
    if "chan2_off_vpp" not in iso_src:
        errors.append("iso must query CHAN2 on SIM then leftover-couple (same USB SCPI)")
    if iso_src.find("if sim:") < iso_src.find("ITEM? VPP,CHAN2") and "ITEM? VPP,CHAN2" in iso_src:
        errors.append("iso must not skip CHAN2 SCPI on SIM")
    if "simulated" not in iso_src or "CHAN2" not in iso_src:
        errors.append("iso SIM must not treat G11 CHAN2 as COM residual")
    if _ast_calls_input(iso_src):
        errors.append("iso.py must not call input()")
    iso_spec = next((s for s in load_part_specs("rs2323") if s.get("id") == "ISO_dB"), {})
    if iso_spec.get("test") != "iso":
        errors.append("ISO_dB spec must bind test: iso")
    if iso_spec.get("min") is not None or iso_spec.get("max") is not None:
        errors.append("do not invent ISO_dB min/max from PDF image")
    xtalk_src = _src(REPO / "ate" / "tests" / "lim" / "xtalk.py")
    if "XTALK_dB" not in xtalk_src:
        errors.append("xtalk must stamp XTALK_dB")
    if "chan2_off_vpp" not in xtalk_src:
        errors.append("xtalk must query CHAN2 on SIM then leftover-couple")
    if "simulated" not in xtalk_src or "CHAN2" not in xtalk_src:
        errors.append("xtalk SIM must not treat G11 CHAN2 as COM2 residual")
    if _ast_calls_input(xtalk_src):
        errors.append("xtalk.py must not call input()")
    xtalk_spec = next((s for s in load_part_specs("rs2323") if s.get("id") == "XTALK_dB"), {})
    if xtalk_spec.get("test") != "xtalk":
        errors.append("XTALK_dB spec must bind test: xtalk")
    if xtalk_spec.get("min") is not None or xtalk_spec.get("max") is not None:
        errors.append("do not invent XTALK_dB min/max from PDF image")
    if "usb_ron" not in en2227 or "usb_ton_toff" not in en2227:
        errors.append("rs2227 must enable USB Path B usb_ron and usb_ton_toff")
    if "usb_iso" not in en2227 or "usb_xtalk" not in en2227:
        errors.append("rs2227 must enable Path B usb_iso and usb_xtalk")
    if "usb_iso" in en2323 or "usb_xtalk" in en2323:
        errors.append("rs2323 must not enable USB iso/xtalk ids")
    usb_src = _src(REPO / "ate" / "tests" / "lim" / "rs2227.py")
    if "USB_RON_ohm" not in usb_src:
        errors.append("usb_ron must stamp USB_RON_ohm")
    if "USB_TON_ns" not in usb_src or "USB_TOFF_ns" not in usb_src:
        errors.append("usb_ton_toff must stamp USB_TON_ns / USB_TOFF_ns")
    if "HSD1" not in usb_src:
        errors.append("rs2227 USB body must name HSD1 (DPDT), not RS2323 COM/NO")
    if _ast_calls_input(usb_src):
        errors.append("rs2227.py must not call input()")
    if "USB_ISO_dB" not in usb_src or "USB_XTALK_dB" not in usb_src:
        errors.append("usb_iso/usb_xtalk must stamp USB_ISO_dB / USB_XTALK_dB")
    if "chan2_off_vpp" not in usb_src:
        errors.append("usb_iso must query CHAN2 on SIM then leftover-couple")
    if "simulated" not in usb_src:
        errors.append("usb_iso SIM must not treat G11 CHAN2 as HSD residual")
    usb_iso_spec = next((s for s in load_part_specs("rs2227") if s.get("id") == "USB_ISO_dB"), {})
    if usb_iso_spec.get("test") != "usb_iso":
        errors.append("USB_ISO_dB spec must bind test: usb_iso")
    if usb_iso_spec.get("min") is not None or usb_iso_spec.get("max") is not None:
        errors.append("do not invent USB_ISO_dB min/max from PDF image")
    usb_xt_spec = next((s for s in load_part_specs("rs2227") if s.get("id") == "USB_XTALK_dB"), {})
    if usb_xt_spec.get("test") != "usb_xtalk":
        errors.append("USB_XTALK_dB spec must bind test: usb_xtalk")
    if usb_xt_spec.get("min") is not None or usb_xt_spec.get("max") is not None:
        errors.append("do not invent USB_XTALK_dB min/max from PDF image")
    usb_ron_spec = next(
        (s for s in load_part_specs("rs2227") if s.get("id") == "USB_RON_ohm"),
        {},
    )
    if usb_ron_spec.get("test") != "usb_ron":
        errors.append("USB_RON_ohm spec must bind test: usb_ron")
    if usb_ron_spec.get("min") is not None or usb_ron_spec.get("max") is not None:
        errors.append("do not invent USB rON min/max from PDF image")
    usb_ton_spec = next(
        (s for s in load_part_specs("rs2227") if s.get("id") == "USB_TON_ns"),
        {},
    )
    if usb_ton_spec.get("typ") != 20:
        errors.append("USB_TON_ns typ must stay 20 from banner")
    if usb_ton_spec.get("min") is not None or usb_ton_spec.get("max") is not None:
        errors.append("do not invent USB tON min/max from PDF image")
    ron_src = _src(REPO / "ate" / "tests" / "lim" / "rs2323.py")
    if "_is_usb" not in ron_src or "OE=V+" not in ron_src:
        errors.append("rs2323 leakage/iplus must branch USB OE/HSD wiring when part is rs2227")
    if "IOZ D+" not in ron_src or "IIN S = V+" not in ron_src:
        errors.append("rs2227 leakage Continue must name D+/S, not only RS2323 NO/IN1")
    if '"id": "RON_ohm"' not in ron_src:
        errors.append("ron must stamp RON_ohm from Vdrop/I_force")
    if "VCOM" not in ron_src:
        errors.append("ron must sweep VCOM (lab Icom=-10 mA, VNO 0-to-V+)")
    if "CONF:RES" in ron_src or "CONF:OHM" in ron_src:
        errors.append("ron must not send ohms SCPI (not in dmm_setup allowlist)")
    if '"id": "TON_ns"' not in ron_src:
        errors.append("ton_toff must stamp TON_ns")
    if "CON_pF" not in ron_src or "TBBM_ns" not in ron_src:
        errors.append("con_coff/tbbm must stamp CON_pF / TBBM_ns")
    if "VTH_V" not in ron_src:
        errors.append("vth must stamp VTH_V")
    ron_spec = next(
        (s for s in load_part_specs("rs2323") if s.get("id") == "RON_ohm"),
        {},
    )
    if ron_spec.get("test") != "ron":
        errors.append("RON_ohm spec must bind test: ron")
    if ron_spec.get("min") is not None or ron_spec.get("max") is not None:
        errors.append("do not invent rON min/max from PDF image")
    if ron_spec.get("typ") != 0.6:
        errors.append("RON_ohm typ must stay 0.6 from banner")
    for sid in ("TON_ns", "TOFF_ns", "CON_pF", "COFF_pF", "CIN_pF", "TBBM_ns", "VTH_V"):
        row = next((s for s in load_part_specs("rs2323") if s.get("id") == sid), {})
        if row.get("min") is not None or row.get("max") is not None:
            errors.append(f"do not invent {sid} min/max from PDF image")
    pulse_spec = next(
        (s for s in load_part_specs("rs1g123") if s.get("id") == "PULSE_ns"),
        {},
    )
    if pulse_spec.get("test") != "pulse_width":
        errors.append("PULSE_ns spec must bind test: pulse_width")
    if pulse_spec.get("min") is not None or pulse_spec.get("max") is not None:
        errors.append("do not invent PULSE_ns min/max (board RC)")

    clk_src = _src(REPO / "ate" / "tests" / "logic" / "clk_q.py")
    if "CLKQ_PHL_ns" not in clk_src:
        errors.append("clk_q must stamp CLKQ_PHL_ns")
    if _ast_calls_input(clk_src):
        errors.append("clk_q.py must not call input()")
    pw_src = _src(REPO / "ate" / "tests" / "logic" / "pulse_width.py")
    if "PULSE_ns" not in pw_src:
        errors.append("pulse_width must stamp PULSE_ns")
    if _ast_calls_input(pw_src):
        errors.append("pulse_width.py must not call input()")
    sh_src = _src(REPO / "ate" / "tests" / "logic" / "serial_shift.py")
    if "Q7_HIGH_V" not in sh_src:
        errors.append("serial_shift must stamp Q7_HIGH_V")
    if "Q7_LOW_V" not in sh_src:
        errors.append("serial_shift must stamp Q7_LOW_V")
    if _ast_calls_input(sh_src):
        errors.append("serial_shift.py must not call input()")
    cmos_src = _src(REPO / "ate" / "tests" / "logic" / "cmos_prop.py")
    if "RFDelay" not in cmos_src or "FRDelay" not in cmos_src:
        errors.append("rs1g14 inverter tPD must query RFDelay/FRDelay (Y is not A)")
    if "Bench still FFDelay" in cmos_src:
        errors.append("inverter wire text must not keep same-edge FFDelay/RRDelay")
    if _ast_calls_input(cmos_src):
        errors.append("cmos_prop.py must not call input()")
    seelim_src = _src(REPO / "ate" / "tests" / "logic" / "seelim_dc.py")
    if "run_see_lim" not in seelim_src or "goldens" not in seelim_src:
        errors.append("seelim_dc must call original goldens/see_lin files")
    if "test_icc" not in seelim_src or "test_delta_icc" not in seelim_src:
        errors.append("seelim_dc must trigger SeeLim test_icc / test_delta_icc")
    if _ast_calls_input(seelim_src):
        errors.append("seelim_dc.py must not call input() (Continue bridge only)")
    if "math.isfinite" not in seelim_src:
        errors.append("seelim_dc must drop NaN golden trips (not a stamp)")
    sim_src = _src(REPO / "ate" / "instruments" / "sim.py")
    if "seelim_oe_high_a0_y_low" not in sim_src:
        errors.append(
            "SIM loopback must keep RS1G126 OE-high A=0 as Y low (not LDO VOUT)"
        )
    if "return 500e-9" in sim_src:
        errors.append("SIM CHAN2 PWID must not return 500 ns dummy")
    if "serial_q7_follows_a_low" not in sim_src:
        errors.append("SIM loopback must assert Q7 follows A=0 after CLK")
    if 'if "OVER" in item_u' not in sim_src:
        errors.append("SIM OVERSHOOT must be modeled, not the 0.12 dummy")
    if "npr_chan2_not_g11" not in sim_src:
        errors.append("SIM loopback must keep BUFFER NPR CHAN2 off the G11*6 V path")
    if "vpp1 > 0.2" not in sim_src:
        errors.append("SIM CHAN2 volts-class SIN must clip Av=1, not G11")
    if "return 0.12 if driven" in sim_src:
        errors.append("SIM unknown ITEM must not return 0.12 dummy")
    if "9.91e37" not in sim_src:
        errors.append("SIM unknown ITEM must return Rigol invalid 9.91e37")
    if "unknown_item_not_dummy" not in sim_src:
        errors.append("SIM loopback must fail-close unknown MSO ITEM")
    dmm_fn = _fn_src(sim_src, "_dmm_volt") if "_dmm_volt" in sim_src else ""
    if "y_invert" not in dmm_fn:
        errors.append("SIM CMOS Y invert must gate on y_invert (inverter DUT only)")
    if '"y_invert"' not in dmm_fn and "'y_invert'" not in dmm_fn:
        errors.append("SIM must not invert CMOS Y unless y_invert is set")
    if "dmm_mso_y_agree" not in sim_src:
        errors.append("SIM loopback must fail-close DMM vs MSO Y on the same node")
    if "set_schmitt" not in sim_src:
        errors.append("SIM must export set_schmitt so DMM/MSO share Schmitt vs CMOS")
    if "dmm_mso_chan2_y_agree" not in sim_src:
        errors.append("SIM loopback must fail-close DMM vs MSO CHAN2 Y")
    if "set_ldo_dut" not in sim_src:
        errors.append("SIM must export set_ldo_dut for Path B LDO VOUT")
    if "ldo_dut" not in dmm_fn:
        errors.append("SIM _dmm_volt must gate LDO VOUT on ldo_dut (not CH3 heuristic)")
    if "v2 < 1" in dmm_fn or "v2<1" in dmm_fn:
        errors.append("SIM must not restore CH3+CH2<1V LDO shortcut (RS1G126 OE)")
    if "ldo_vout_not_vin" not in sim_src:
        errors.append("SIM loopback must fail-close LDO DMM as VOUT not VIN")
    if "ldo_lir_not_vin_alias" not in sim_src:
        errors.append("SIM loopback must fail-close LIR VIN alias")
    if "ldo_load_not_schmitt" not in sim_src:
        errors.append("SIM loopback must keep LDO load off SeeLim Schmitt")
    dmm_i = _fn_src(sim_src, "_dmm_current") if "_dmm_current" in sim_src else ""
    if "ldo_dut" not in dmm_i:
        errors.append(
            "SIM _dmm_current must gate LDO IQ on ldo_dut (VIN node, not VOUT-bias ICC)"
        )
    if "ldo_iq_follows_vin" not in sim_src:
        errors.append("SIM loopback must fail-close LDO IQ vs VIN")
    if "inverter_a_high_y_not_vcc" not in sim_src:
        errors.append("SIM loopback must fail-close inverter A=VCC as Y not VCC")
    if "inverter_a_low_y_vcc" not in sim_src:
        errors.append("SIM loopback must stamp inverter VOH with A=0")
    if "buffer_a_high_y_vcc_after_invert" not in sim_src:
        errors.append("SIM loopback must keep buffer Y=VCC after invert flag off")
    if "if local.is_dir()" not in seelim_src:
        errors.append("seelim_dc must prefer goldens/see_lin over Downloads See Lim Repo")
    if "sys.path[:]" not in seelim_src:
        errors.append("seelim_dc must strip the golden folder from all of sys.path")
    if "_NullLog" not in seelim_src:
        errors.append("seelim_dc must pass a log_test stub, not logger=None")
    sib = seelim_src.split("_SIBLINGS", 1)[-1].split(")", 1)[0]
    if "generator_setup" in sib:
        errors.append("seelim_dc must not shadow repo generator_setup (park_generator_idle)")
    if "psu_setup" not in sib or "dmm_setup" not in sib:
        errors.append("seelim_dc must isolate golden psu_setup/dmm_setup (query_psu_mode / clear_dmm_buffer)")
    if "_ensure_repo_setup" not in seelim_src:
        errors.append("seelim_dc must pin repo generator_setup before golden sys.path")
    psrr_src = _src(REPO / "ate" / "tests" / "opa" / "psrr.py")
    if "PSRR_dB" not in psrr_src:
        errors.append("psrr.py must stamp PSRR_dB from dVs/dVout")
    if _ast_calls_input(psrr_src):
        errors.append("psrr.py must not call input()")
    mapped_src = _src(REPO / "ate" / "tests" / "opa" / "mapped_dc.py")
    if '"psrr"' in mapped_src:
        errors.append("mapped_dc must not register psrr (real DC body owns the id)")
    if '"cmrr"' in mapped_src:
        errors.append("mapped_dc must not register cmrr (real DC body owns the id)")
    cmrr_src = _src(REPO / "ate" / "tests" / "opa" / "cmrr.py")
    if "CMRR_dB" not in cmrr_src:
        errors.append("cmrr.py must stamp CMRR_dB from dVcm/d(Vout-Vin)")
    if _ast_calls_input(cmrr_src):
        errors.append("cmrr.py must not call input()")
    pon_src = _src(REPO / "ate" / "tests" / "opa" / "power_on.py")
    if "POWERON_ns" not in pon_src:
        errors.append("power_on.py must stamp POWERON_ns")
    if _ast_calls_input(pon_src):
        errors.append("power_on.py must not call input()")
    if '"vohl"' in mapped_src:
        errors.append("mapped_dc must not register vohl (real DMM body owns the id)")
    en622 = enabled_tests_for_part("rs622") or []
    if "aol" in en622 or "emirr" in en622:
        errors.append("rs622 default enabled_tests must not include mapped aol/emirr")
    if "psrr" not in en622 or "vohl" not in en622:
        errors.append("rs622 must keep Path B psrr/vohl on default START")
    vohl_src = _src(REPO / "ate" / "tests" / "opa" / "vohl.py")
    if "VOH_V" not in vohl_src or "VOL_V" not in vohl_src:
        errors.append("vohl.py must stamp VOH_V and VOL_V from DMM")
    if _ast_calls_input(vohl_src):
        errors.append("vohl.py must not call input()")
    voh_spec = next((s for s in load_part_specs("rs622") if s.get("id") == "VOH_V"), None)
    if not voh_spec or voh_spec.get("test") != "vohl":
        errors.append("VOH_V spec must bind test: vohl")
    if voh_spec and (voh_spec.get("min") is not None or voh_spec.get("max") is not None):
        errors.append("do not invent VOH_V min/max (RS62X extract has no VOH table)")
    buf_src = _src(REPO / "ate" / "tests" / "opa" / "buffer_steps.py")
    if "OVERSHOOT" not in buf_src or "LSSR_VPP_V" not in buf_src:
        errors.append("sssr/lssr must stamp OVERSHOOT / LSSR_VPP_V")
    if _ast_calls_input(buf_src):
        errors.append("buffer_steps.py must not call input()")
    ort_src = _src(REPO / "ate" / "tests" / "opa" / "ort.py")
    if "ORT_POS_us" not in ort_src or "ORT_NEG_us" not in ort_src:
        errors.append("ort.py must stamp ORT_POS_us / ORT_NEG_us from MSO delay")
    if _ast_calls_input(ort_src):
        errors.append("ort.py must not call input()")
    ort_spec = next((s for s in load_part_specs("rs622") if s.get("id") == "ORT_POS_us"), None)
    if not ort_spec or ort_spec.get("test") != "ort":
        errors.append("ORT_POS_us spec must bind test: ort")
    if ort_spec and (ort_spec.get("min") is not None or ort_spec.get("max") is not None):
        errors.append("do not invent ORT_POS_us min/max (extract 0.5 s is garbled)")

    gbw_src = _src(REPO / "ate" / "tests" / "opa" / "gbw.py")
    if _ast_calls_input(gbw_src):
        errors.append("gbw.py must not call input()")
    if "pause_cb=params.pause_hook" not in gbw_src:
        errors.append("gbw must pass pause_cb=params.pause_hook to measure_gbw")
    if "measure_gbw" not in gbw_src:
        errors.append("gbw must wrap opa_tests.measure_gbw (CHAN1=IN+ CHAN2=VOUT G11)")
    opa_src = _src(REPO / "opa_tests.py")
    gbw_fn = _fn_src(opa_src, "measure_gbw")
    if not gbw_fn:
        errors.append("opa_tests.measure_gbw missing")
    else:
        if _ast_calls_input(gbw_fn):
            errors.append("measure_gbw must not call input(); use pause_cb")
        if "pause_cb" not in gbw_fn:
            errors.append("measure_gbw must use pause_cb")

    from ate.core.check_all_parts import must_stamp_missing_ids, sim_skip_scpi_files

    missing_stamp = must_stamp_missing_ids()
    if missing_stamp:
        errors.append(f"MUST_STAMP missing unique test_ids: {missing_stamp}")
    errors.extend(sim_skip_scpi_files())

    return errors


def main() -> int:
    errors = check_add_test()
    if errors:
        print("FAIL check_add_test:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        "OK check_add_test: Path A catalog wins; Path B cin/cpd + Write test; "
        "Path C remember+trigger; Cursor prompt fill; "
        "Ariff DC scaled on Logic SKUs; runner has no family imports"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
