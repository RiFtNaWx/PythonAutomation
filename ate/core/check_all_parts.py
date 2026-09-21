"""Fail-closed: every parts/*.yaml enabled_tests exists; USB KEEP locks.

Run: python -m ate.core.check_all_parts
     python -m ate.core.check_all_parts logic
"""
from __future__ import annotations

import ast
import inspect
import json
import math
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

from ate.core.new_product import suite_for_part
from ate.core.paths import PARTS_DIR, REPO_ROOT
from ate.core.registry import all_tests, load_family
from ate.core.specs import any_fail, measurements_from_result
from ate.instruments.discovery import load_known_visa, skip_visa_resource
from ate.instruments.session import Instruments

KEEP_BENCH = frozenset({"PSU", "AWG", "DMM"})
SCAFFOLD_MARK = "imported scaffold -- fill body"
_STUB_EMPTY = frozenset()
_KNOWN_KINDS = ("PSU", "AWG", "DMM", "MSO")
# logic argv also scales Level translators (RS0204 ate_suite=logic, RS0302).
_FAMILY_ALIASES = {
    "logic": frozenset({"logic", "level"}),
    "level": frozenset({"logic", "level"}),
    "switch": frozenset({"switch"}),
    "lim": frozenset({"switch"}),
    "opamp": frozenset({"opamp"}),
    "power": frozenset({"power"}),
}


def scale_family_from_argv(argv: list[str] | None = None) -> str:
    args = [
        a.strip().lower()
        for a in (argv if argv is not None else sys.argv[1:])
        if a and not str(a).startswith("-")
    ]
    return args[0] if args else ""


def filter_part_rows(rows: list[dict[str, Any]], family: str = "") -> list[dict[str, Any]]:
    fam = str(family or "").strip().lower()
    if not fam:
        return list(rows)
    want = _FAMILY_ALIASES.get(fam, frozenset({fam}))
    return [r for r in rows if str(r.get("family") or "") in want]
STAMPS_PATH = Path(__file__).resolve().parent / "_check_data" / "sim_stamps.json"
# Trailing "_" = prefix match (VIH_ hits VIH_V and VIH_1p8V).
MUST_STAMP = {
    "ac_gain_check": "GAIN_VV",
    "ac_vin_sweep": "GAIN_VV",
    "cap_load": "CAP_pF",
    "cin": "CIN_pF",
    "clk_q": "CLKQ_PHL_ns",
    "cmrr": "CMRR_dB",
    "con_coff": "CON_pF",
    "cpd": "CPD_pF",
    "delta_icc": "DELTA_ICC_uA",
    "delta_supply_current": "DELTA_ICC_uA",
    "enable_current": "IEN_uA",
    "fmax": "FMAX_Mbps",
    "gbw": "GBW_MHz",
    "i2c_cioff": "CIOFF_pF",
    "i2c_ii": "II_uA",
    "i2c_ron": "RON_ohm",
    "icc": "ICC_uA",
    "ii": "II_uA",
    "il": "IL_uA",
    "input_leakage": "IIN_uA",
    "input_leakage_sweep": "II_uA",
    "input_threshold": "VIH_",
    "input_thresholds": "VIH_",
    "ioff": "IOFF_uA",
    "ioff_leakage": "IOFF_uA",
    "ioutmax": "IOUTMAX_V",
    "ioz": "IOZ_uA",
    "iplus": "IPLUS_uA",
    "iq": "IQ_uA",
    "iso": "ISO_dB",
    "leakage_off": "IOZ_uA",
    "leakage_on": "ION_uA",
    "lir": "LIR_mV",
    "lor": "LOR_mV",
    "lssr": "LSSR_VPP_V",
    "no_phase_reversal": "NPR_VPP_V",
    "noise": "VN_OUT_PP_mV",
    "off_current": "OFF_uA",
    "ort": "ORT_POS_us",
    "output_voltage": "VOUT_V",
    "power_on_time": "POWERON_ns",
    "psrr": "PSRR_dB",
    "pulse_width": "PULSE_ns",
    "ron": "RON_ohm",
    "serial_shift": "Q7_HIGH_V",
    "settling": "SETTLE_VPP_V",
    "slew": "SR_Vus",
    "sssr": "OVERSHOOT",
    "supply_current": "ICC_uA",
    "supply_current_sweep": "ICC_uA",
    "tbbm": "TBBM_ns",
    "tdis": "TDIS_ns",
    "ten": "TEN_ns",
    "tf": "TF_ns",
    "th": "TDIS_ns",
    "tidle": "TIDLE_PHL_ns",
    "ton_toff": "TON_ns",
    "tp": "TPD_PHL_ns",
    "tp_rs0204": "TP_PHL_ns",
    "tpd": "TPD_PHL_ns",
    "tr": "TR_ns",
    "tsk": "TSK_ns",
    "tsu": "TEN_ns",
    "tw": "TW_ns",
    "usb_iso": "USB_ISO_dB",
    "usb_ron": "USB_RON_ohm",
    "usb_ton_toff": "USB_TON_ns",
    "usb_xtalk": "USB_XTALK_dB",
    "vih": "VIH_V",
    "vih_vil": "VIH_",
    "vil": "VIL_V",
    "vinmin": "VINMIN_V",
    "voh": "VOH_",
    "voh_load": "VOH_",
    "vohl": "VOH_V",
    "vol": "VOL_",
    "vol_load": "VOL_",
    "vos_sweep": "VOS_mV",
    "vth": "VTH_V",
    "xtalk": "XTALK_dB",
}
# Pin Cio is not dynamic Cpd. Workbook Tsu/Th stay TEN_ns/TDIS_ns (MSO OE delay).
# Trailing "_" prefix match when any listed prefix hits.
MUST_STAMP_ANY: dict[str, tuple[str, ...]] = {
    "input_threshold": ("VIH_", "VTPLUS_"),
    "vth": ("VTH_V", "VTPLUS_V", "VTPLUS_", "VIH_V", "VIH_"),
}
MUST_STAMP_PART = {
    ("rs0204", "cpd"): "CIO_A_pF",
}
BAN_STAMP = frozenset({"AOL_dB", "SETTLE_us"})
MSO_BW_MHZ = 70.0


_DMM_BAN = ("*RST", "NPLC", "AZER", "AVER", "TRAC:CLE", "MEAS:CURR")


def _writes_rst(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name != "write" or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and "*RST" in str(arg.value):
            return True
    return False


def _stamp_hit(ids_st: list[str], want: str) -> bool:
    if want in ids_st:
        return True
    if want.endswith("_"):
        return any(str(i).startswith(want) for i in ids_st)
    return False


def _scale_sim_hard_fail(meas: list[dict[str, Any]], step: Any) -> bool:
    """SPEC fail that should fail-closed scale SIM (not UNCONFIRMED/leftover honest)."""
    if step is not None and getattr(step, "error", None):
        return True
    for m in meas or []:
        if not isinstance(m, dict):
            continue
        if str(m.get("result") or "") != "fail":
            continue
        if m.get("greenable") is False:
            continue
        if str(m.get("status") or "").upper() in (
            "UNCONFIRMED",
            "LEFTOVER",
            "PROVISIONAL",
        ):
            continue
        return True
    return False


def _finite_stamp(m: dict[str, Any]) -> bool:
    if not m.get("id"):
        return False
    try:
        v = float(m.get("value"))
    except (TypeError, ValueError):
        return False
    if not math.isfinite(v):
        return False
    # Rigol MSO invalid (9.91e37). Do not treat as a stamped value.
    if abs(v) > 1e10:
        return False
    return True


def _scope_invalid(raw: Any) -> bool:
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v) and abs(v) > 1e10


def _bw_over_mso(compact: list[dict[str, Any]]) -> str:
    for row in compact:
        mid = str(row.get("id") or "")
        unit = str(row.get("unit") or "").strip().lower()
        if unit != "mhz" and not mid.endswith("_MHz"):
            continue
        try:
            mhz = float(row.get("value"))
        except (TypeError, ValueError):
            continue
        if mhz == mhz and mhz > MSO_BW_MHZ:
            return f"{mid}={mhz} MHz"
    return ""


def must_stamp_missing_ids(family: str = "") -> list[str]:
    """Fail-closed: every unique enabled test_id has a MUST_STAMP measurement id."""
    seen: set[str] = set()
    for row in filter_part_rows(load_part_rows(), family):
        if row.get("error") or row.get("stub"):
            continue
        for tid in row.get("ids") or []:
            seen.add(str(tid))
    return sorted(
        tid for tid in seen if tid not in MUST_STAMP and tid not in MUST_STAMP_ANY
    )


def sim_skip_scpi_files() -> list[str]:
    """ate/tests must not skip USB SCPI on SIM. iso leftover couple after CHAN2 is allowed."""
    errors: list[str] = []
    root = REPO_ROOT / "ate" / "tests"
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "if sim:" not in text:
            continue
        if path.name == "iso.py":
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        errors.append(
            f"{rel}: SIM if sim: skip (only iso leftover couple after CHAN2 query is allowed)"
        )
    return errors


def _dmm_banned_writes(path: Path) -> list[str]:
    hits: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name != "write" or not node.args:
            continue
        arg = node.args[0]
        if not isinstance(arg, ast.Constant):
            continue
        text = str(arg.value).upper()
        if any(tok in text for tok in _DMM_BAN):
            hits.append(str(arg.value))
    return hits


def _is_scaffold(spec) -> bool:
    notes = str(getattr(spec, "notes", "") or "").lower()
    if "fill measurement body" in notes or "imported scaffold" in notes:
        return True
    try:
        src = inspect.getsource(spec.run)
    except (OSError, TypeError):
        return False
    return SCAFFOLD_MARK in src


def _part_test_ids(data: dict[str, Any]) -> list[str]:
    raw = data.get("enabled_tests")
    if isinstance(raw, list):
        return [str(x) for x in raw]
    ids: list[str] = []
    modes = data.get("fixture_modes") or {}
    if isinstance(modes, dict):
        for mode in modes.values():
            if not isinstance(mode, dict):
                continue
            if str(mode.get("board_class") or "").lower() == "research":
                continue
            for tid in mode.get("tests") or []:
                s = str(tid)
                if s not in ids:
                    ids.append(s)
    return ids


def _result_rows(step) -> list[dict[str, Any]]:
    blob = step.data if isinstance(getattr(step, "data", None), dict) else {}
    inner = blob.get("data") if isinstance(blob.get("data"), dict) else blob
    rows = inner.get("rows") if isinstance(inner, dict) else None
    return [r for r in (rows or []) if isinstance(r, dict)]


def _inverter_polarity_errors(pk: str, tid: str, step) -> list[str]:
    """Fail-closed: inverter VOH must not equal VCC while A is driven to VCC."""
    if pk != "rs1g14" or tid not in ("voh_load", "vol_load"):
        return []
    errors: list[str] = []
    rows = _result_rows(step)
    if not rows:
        errors.append(f"rs1g14 {tid}: missing INPUT_A_V rows")
        return errors
    for r in rows:
        try:
            vcc = float(r.get("VCC") or 0)
            a_v = float(r.get("INPUT_A_V"))
            meas = float(r.get("Measured"))
        except (TypeError, ValueError):
            errors.append(f"rs1g14 {tid}: missing INPUT_A_V/Measured")
            continue
        if tid == "voh_load":
            if a_v > 0.2:
                errors.append(
                    f"rs1g14 voh_load A must be 0 for inverter VOH, got {a_v} at VCC={vcc}"
                )
            if abs(a_v - vcc) < 0.2 and abs(meas - vcc) < 0.35:
                errors.append(
                    f"rs1g14 VOH equals VCC while A=VCC (old buffer polarity) VCC={vcc}"
                )
            if abs(meas - vcc) > 0.35:
                errors.append(
                    f"rs1g14 VOH with A=0 must be near VCC, got {meas} at VCC={vcc}"
                )
        elif abs(a_v - vcc) > 0.2:
            errors.append(
                f"rs1g14 vol_load A must be VCC for inverter VOL, got {a_v} at VCC={vcc}"
            )
        elif meas > 0.2:
            errors.append(
                f"rs1g14 VOL with A=VCC must be low, got {meas} at VCC={vcc}"
            )
    return errors


def load_part_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(PARTS_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
        if not isinstance(data, dict):
            rows.append({"path": path, "error": "yaml not a mapping"})
            continue
        pk = str(data.get("part_key") or path.stem).strip().lower()
        part = str(data.get("part") or data.get("device") or pk).strip()
        component = str(data.get("component") or "").strip()
        package = str(data.get("package") or "").strip()
        model = str(data.get("model") or "").strip()
        family = suite_for_part(part, component=component, package=package, model=model)
        ids = _part_test_ids(data)
        rows.append(
            {
                "path": path,
                "part_key": pk,
                "part": part,
                "component": component,
                "package": package,
                "model": model,
                "version": str(data.get("version") or "Version_1"),
                "vcc": float(data.get("vcc") or data.get("vcca") or 5.0),
                "vccb": data.get("vccb"),
                "current_limit": float(data.get("current_limit") or 0.1),
                "vin_lir": data.get("vin_lir") or [3.4, 5.0],
                "family": family,
                "ids": ids,
                "stub": pk in _STUB_EMPTY or (isinstance(data.get("enabled_tests"), list) and not ids),
            }
        )
    return rows


def classify_ids(ids: list[str], specs: dict[str, Any]) -> dict[str, list[str]]:
    keep: list[str] = []
    mso: list[str] = []
    scaffold: list[str] = []
    missing: list[str] = []
    other: list[str] = []
    for tid in ids:
        spec = specs.get(tid)
        if spec is None:
            missing.append(tid)
            continue
        if _is_scaffold(spec):
            scaffold.append(tid)
            continue
        need = set(spec.required_instruments or ())
        if "MSO" in need:
            mso.append(tid)
            continue
        if need and need <= KEEP_BENCH:
            keep.append(tid)
            continue
        other.append(tid)
    return {"keep": keep, "mso": mso, "scaffold": scaffold, "missing": missing, "other": other}


def usb_mso_plan(family: str = "") -> list[dict[str, Any]]:
    """Parts with MSO TestSpecs. USB START when visa_known.yaml lists the scope."""
    plan: list[dict[str, Any]] = []
    cache: dict[str, dict[str, Any]] = {}
    for row in filter_part_rows(load_part_rows(), family):
        if row.get("error") or row.get("stub"):
            continue
        fam = str(row.get("family") or "")
        if not fam:
            continue
        if fam not in cache:
            load_family(fam)
            cache[fam] = {t.id: t for t in all_tests()}
        bits = classify_ids(row["ids"], cache[fam])
        if not bits["mso"]:
            continue
        plan.append({**row, **bits})
    return plan


def usb_keep_plan(family: str = "") -> list[dict[str, Any]]:
    """Parts that can START on PSU+AWG+DMM (no MSO)."""
    plan: list[dict[str, Any]] = []
    cache: dict[str, dict[str, Any]] = {}
    for row in filter_part_rows(load_part_rows(), family):
        if row.get("error") or row.get("stub"):
            continue
        fam = str(row.get("family") or "")
        if not fam:
            continue
        if fam not in cache:
            load_family(fam)
            cache[fam] = {t.id: t for t in all_tests()}
        bits = classify_ids(row["ids"], cache[fam])
        if not bits["keep"]:
            continue
        plan.append({**row, **bits})
    return plan


def check_all_parts(family: str = "") -> list[str]:
    errors: list[str] = []
    dmm = REPO_ROOT / "dmm_setup.py"
    ldo = REPO_ROOT / "ate" / "tests" / "power" / "ldo.py"
    sess = REPO_ROOT / "ate" / "instruments" / "session.py"
    scope_src = (REPO_ROOT / "scope_setup.py").read_text(encoding="utf-8")

    disc = REPO_ROOT / "ate" / "instruments" / "discovery.py"
    disc_src = disc.read_text(encoding="utf-8")
    sess_src = sess.read_text(encoding="utf-8")

    known = load_known_visa()
    for kind in _KNOWN_KINDS:
        if kind not in known:
            errors.append(f"visa_known.yaml missing {kind}")
    if "_idn_isolated" not in disc_src or "load_known_visa" not in disc_src:
        errors.append("discover live path must *IDN visa_known.yaml in a child")
    if "usbtmc_pnp_ok_serials" not in disc_src:
        errors.append("discover must skip Windows PnP Unknown USBTMC")
    if "taskkill" not in disc_src:
        errors.append("isolated *IDN must taskkill hung NI viOpen")
    if "open_timeout" not in sess_src:
        errors.append("Instruments.open_resource must set open_timeout")
    if "find_instruments(rm=self.rm)" in sess_src:
        errors.append("Instruments must not list_resources via parent RM")

    if _writes_rst(dmm):
        errors.append("dmm_setup.py must not write *RST")
    dmm_src = dmm.read_text(encoding="utf-8")
    if ":CONF:CURR:DC" not in dmm_src or ":SENS:FUNC '{name}'" not in dmm_src:
        errors.append("dmm_setup must CONF:CURR:DC + SENS:FUNC 'CURR:DC' so DMM6500 shows DCI")
    banned = _dmm_banned_writes(dmm)
    if banned:
        errors.append(f"dmm_setup banned DMM6500 writes {banned}")
    if "\u666e\u6e90" in scope_src:
        errors.append("scope_setup.screenshot must not print Chinese demo (Windows TP crash)")
    ldo_src = ldo.read_text(encoding="utf-8")
    if "ovp=6.5" in ldo_src or "ovp = 6.5" in ldo_src:
        errors.append("ldo.py must not pass ovp=6.5 (DUT ceiling 6.0 V)")
    if tuple(Instruments.REQUIRED_AT_OPEN) != ():
        errors.append("REQUIRED_AT_OPEN must be empty")
    reset_fn = next(
        (
            n
            for n in ast.walk(ast.parse(sess_src))
            if isinstance(n, ast.FunctionDef) and n.name == "reset_all"
        ),
        None,
    )
    if reset_fn is None or "self.dmm" in ast.unparse(reset_fn):
        errors.append("reset_all must not *RST DMM6500")
    if skip_visa_resource("USB0::0x1AB1::0x0515::SN::INSTR"):
        errors.append("must not skip MSO USB 0x0515")
    if "def reopen_bench" not in sess_src:
        errors.append("Instruments.reopen_bench required after DMM/PSU TMO")
    runner = (REPO_ROOT / "ate" / "core" / "runner.py").read_text(encoding="utf-8")
    if "def _reopen_bench_after_visa" not in runner or "def _visa_bus_error" not in runner:
        errors.append("runner must retry KEEP VISA TMO via reopen_bench")
    if 'reason="session close"' not in runner and "reason='session close'" not in runner:
        errors.append("close_session must SAFE IDLE PSU before close_all")

    cache: dict[str, dict[str, Any]] = {}
    keep_n = 0
    for row in filter_part_rows(load_part_rows(), family):
        pk = row.get("part_key") or "?"
        if row.get("error"):
            errors.append(f"{pk}: {row['error']}")
            continue
        if row.get("stub"):
            continue
        fam = str(row.get("family") or "")
        if not fam:
            errors.append(f"{pk}: no family (suite_for_part empty)")
            continue
        if fam not in cache:
            try:
                load_family(fam)
            except Exception as exc:
                errors.append(f"{pk}: load_family({fam!r}) {exc}")
                cache[fam] = {}
                continue
            cache[fam] = {t.id: t for t in all_tests()}
        bits = classify_ids(row["ids"], cache[fam])
        if bits["missing"]:
            errors.append(f"{pk}: missing TestSpec {bits['missing']} in family {fam}")
        if bits["scaffold"]:
            errors.append(
                f"{pk}: enabled Path C scaffold {bits['scaffold']} "
                "-- fill Path B or drop from enabled_tests"
            )
        keep_n += len(bits["keep"])
        if pk == "rs622":
            ids = row.get("ids") or []
            if "slew" not in ids:
                errors.append("rs622 BUFFER catalog must include slew")
            if "slew" not in bits["mso"]:
                errors.append("rs622 slew must require MSO (do not KEEP-skip it)")
    if keep_n < 1:
        errors.append("no KEEP (PSU/AWG/DMM) tests -- USB DC plan is empty")
    missing_stamp = must_stamp_missing_ids(family)
    if missing_stamp:
        errors.append(f"MUST_STAMP missing unique test_ids: {missing_stamp}")
    errors.extend(sim_skip_scpi_files())
    if family in ("", "logic", "level"):
        load_family("logic")
        ioff = {t.id: t for t in all_tests()}.get("input_off_leakage")
        if ioff is None or not _is_scaffold(ioff):
            errors.append(
                "input_off_leakage must stay a Path C scaffold until Path B fill"
            )
    if family in ("", "opamp"):
        load_family("opamp")
        if "slew" not in {t.id for t in all_tests()}:
            errors.append("load_family(opamp) missing slew")
        mso_plan = usb_mso_plan(family)
        rs622 = next((p for p in mso_plan if p.get("part_key") == "rs622"), None)
        if rs622 is None or "slew" not in (rs622.get("mso") or []):
            errors.append("usb_mso_plan must include rs622 slew (MSO USB is on this bench)")
    logic_keys = {
        str(r.get("part_key") or "")
        for r in filter_part_rows(load_part_rows(), "logic")
        if not r.get("error")
    }
    if scale_family_from_argv(["logic"]) != "logic":
        errors.append("scale_family_from_argv(['logic']) must return logic")
    if filter_part_rows([{"family": "opamp", "part_key": "rs622"}], "logic"):
        errors.append("filter_part_rows leaked opamp into logic")
    if "rs622" in logic_keys:
        errors.append("logic scale must not include rs622")
    if "rs1g08" not in logic_keys:
        errors.append("logic scale missing rs1g08")
    if "rs0204" not in logic_keys:
        errors.append("logic scale missing rs0204")
    return errors


_FAM_COMPONENT = {
    "logic": "Logic",
    "opamp": "OpAmp",
    "switch": "AnalogSwitch",
    "level": "Level",
    "power": "Power",
}


def _stamped_meas(data: Any) -> list[dict[str, Any]]:
    blob = data if isinstance(data, dict) else {}
    raw = blob.get("measurements")
    if isinstance(raw, list) and raw:
        return [x for x in raw if isinstance(x, dict)]
    inner = blob.get("data") if isinstance(blob.get("data"), dict) else {}
    nested = inner.get("measurements") if isinstance(inner, dict) else []
    if isinstance(nested, list):
        return [x for x in nested if isinstance(x, dict)]
    return []


def sim_run_all_enabled(family: str = "") -> tuple[list[str], dict[str, Any]]:
    """SIM-run every non-scaffold enabled TestSpec. Original bodies, not USB."""
    from ate.core import database as dbmod
    from ate.core import paths as pathmod
    from ate.core.database import set_context
    from ate.core.runner import ATECore, RunParams

    errors: list[str] = []
    stats: dict[str, Any] = {
        "parts": 0,
        "ran": 0,
        "ok": 0,
        "scaffold": [],
        "stamps": [],
    }
    tmp = Path(tempfile.mkdtemp(prefix="ate_all_parts_"))
    old_root = pathmod.TEST_DB_ROOT
    old_db = dbmod.TEST_DB_ROOT
    old_sleep = time.sleep
    time.sleep = lambda *_a, **_k: None
    pathmod.TEST_DB_ROOT = tmp / "#Test_Database"
    dbmod.TEST_DB_ROOT = pathmod.TEST_DB_ROOT
    core = None
    try:
        pathmod.TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
        core = ATECore(emit=lambda _e: None)
        cache: dict[str, dict[str, Any]] = {}
        for row in filter_part_rows(load_part_rows(), family):
            if row.get("error") or row.get("stub"):
                continue
            from ate.instruments.sim import reset_bus

            reset_bus()
            fam = str(row.get("family") or "")
            if not fam:
                continue
            if fam not in cache:
                try:
                    load_family(fam)
                    cache[fam] = {t.id: t for t in all_tests()}
                except Exception as exc:
                    errors.append(f"{row['part_key']}: load_family({fam!r}) {exc}")
                    cache[fam] = {}
                    continue
            bits = classify_ids(row["ids"], cache[fam])
            if bits["scaffold"]:
                stats["scaffold"].append(f"{row['part_key']}:{','.join(bits['scaffold'])}")
            runnable = bits["keep"] + bits["mso"] + bits["other"]
            if not runnable:
                continue
            stats["parts"] += 1
            set_context(
                component=row.get("component") or _FAM_COMPONENT.get(fam, fam),
                part=row["part"],
                package=row.get("package") or "SOT23",
                operator="Eugene",
                version=row.get("version") or "Version_1",
                model=row.get("model") or row["part"],
                part_key=row["part_key"],
                sample_size=1,
            )
            core.load_family(fam)
            core.open_session(sim=True)
            vccb = row.get("vccb")
            rp = RunParams(
                vcc=float(row.get("vcc") or 5.0),
                vccb=float(vccb) if vccb not in (None, "") else None,
                part=row["part_key"],
                dut_indices=[1],
                channels=["CHA"],
                current_limit_a=float(row.get("current_limit") or 0.1),
                auto_continue=True,
            )
            try:
                results = core.run_sequence(runnable, rp)
            except Exception as exc:
                errors.append(f"{row['part_key']}: run_sequence crashed {exc}")
                core.close_session()
                continue
            if core.last_run_error:
                errors.append(f"{row['part_key']}: run_error {core.last_run_error}")
            got = {r.test_id: r for r in results}
            for tid in runnable:
                stats["ran"] += 1
                step = got.get(tid)
                if step is None:
                    errors.append(f"{row['part_key']} {tid}: missing result")
                else:
                    meas = measurements_from_result(
                        step.data, test_id=tid, part_key=str(row["part_key"] or "")
                    )
                    if _scale_sim_hard_fail(meas, step):
                        errors.append(
                            f"{row['part_key']} {tid}: {step.error or step.summary}"
                        )
                        continue
                    stamped = _stamped_meas(step.data)
                    ids_st = [str(m.get("id") or "") for m in stamped]
                    compact = [
                        {
                            "id": str(m.get("id") or ""),
                            "value": m.get("value"),
                            "unit": m.get("unit") or "",
                        }
                        for m in stamped
                        if m.get("id")
                    ]
                    stats["stamps"].append(
                        {
                            "part_key": row["part_key"],
                            "test_id": tid,
                            "stamps": compact,
                        }
                    )
                    pk = str(row["part_key"] or "")
                    errors.extend(_inverter_polarity_errors(pk, tid, step))
                    want = MUST_STAMP_PART.get((pk, tid)) or MUST_STAMP.get(tid)
                    banned = sorted(BAN_STAMP.intersection(ids_st))
                    bw_hit = _bw_over_mso(compact)
                    invalid_hit = next(
                        (
                            f"{m.get('id')}={m.get('value')}"
                            for m in compact
                            if _scope_invalid(m.get("value"))
                        ),
                        "",
                    )
                    iout_dead = False
                    iout_vin_alias = False
                    lir_vin_alias = False
                    iq_yaml_vout = False
                    iq_flat_vin = False
                    fmax_dead = False
                    edge_dead = False
                    serial_dead = False
                    pulse_dummy = False
                    npr_dead = False
                    over_dummy = False
                    if tid == "ioutmax":
                        raw_v = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "IOUTMAX_V"
                            ),
                            None,
                        )
                        try:
                            iout_dead = float(raw_v) < 1.0
                        except (TypeError, ValueError):
                            iout_dead = True
                        blob = step.data if isinstance(step.data, dict) else {}
                        inner = blob.get("data") if isinstance(blob.get("data"), dict) else blob
                        for rr in (inner.get("rows") or []) if isinstance(inner, dict) else []:
                            if not isinstance(rr, dict):
                                continue
                            try:
                                vin_r = float(rr.get("VIN_V"))
                                vout_r = float(rr.get("VOUT_AVG_V"))
                            except (TypeError, ValueError):
                                continue
                            if vin_r >= 4.5 and abs(vout_r - vin_r) < 0.08:
                                iout_vin_alias = True
                    if tid == "iq":
                        iq_yaml_vout = any(m.get("id") == "VOUT_V" for m in compact)
                        iq_vals: list[float] = []
                        vin_pts: list[float] = []
                        for rr in _result_rows(step):
                            try:
                                vin_pts.append(float(rr.get("VIN_V")))
                                iq_vals.append(float(rr.get("IQ_uA")))
                            except (TypeError, ValueError):
                                continue
                        if len(set(round(v, 4) for v in vin_pts)) >= 2 and len(
                            set(round(i, 6) for i in iq_vals)
                        ) < 2:
                            iq_flat_vin = True
                    if tid == "lir":
                        raw_lir = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "LIR_mV"
                            ),
                            None,
                        )
                        vins = row.get("vin_lir") or [3.4, 5.0]
                        try:
                            lir_v = float(raw_lir)
                            dvin_mv = abs(float(vins[-1]) - float(vins[0])) * 1000.0
                            lir_vin_alias = abs(lir_v - dvin_mv) < 1.0
                            if any(abs(lir_v - float(v) * 1000.0) < 1.0 for v in vins):
                                lir_vin_alias = True
                        except (TypeError, ValueError):
                            lir_vin_alias = True
                    if tid == "fmax":
                        raw_f = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "FMAX_Mbps"
                            ),
                            None,
                        )
                        try:
                            fmax_dead = float(raw_f) <= 0.0
                        except (TypeError, ValueError):
                            fmax_dead = True
                    if tid in ("tr", "tf"):
                        sid = "TR_ns" if tid == "tr" else "TF_ns"
                        raw_e = next(
                            (m.get("value") for m in compact if m.get("id") == sid),
                            None,
                        )
                        try:
                            edge_dead = float(raw_e) > 1e5
                        except (TypeError, ValueError):
                            edge_dead = True
                    if tid == "serial_shift":
                        qhi = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "Q7_HIGH_V"
                            ),
                            None,
                        )
                        qlo = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "Q7_LOW_V"
                            ),
                            None,
                        )
                        try:
                            serial_dead = float(qlo) >= 0.2 * max(float(qhi), 0.1)
                        except (TypeError, ValueError):
                            serial_dead = True
                    if tid == "pulse_width":
                        raw_p = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "PULSE_ns"
                            ),
                            None,
                        )
                        try:
                            pulse_dummy = float(raw_p) < 1e3
                        except (TypeError, ValueError):
                            pulse_dummy = True
                    if tid == "no_phase_reversal":
                        raw_n = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "NPR_VPP_V"
                            ),
                            None,
                        )
                        try:
                            npr_dead = float(raw_n) > 15.0
                        except (TypeError, ValueError):
                            npr_dead = True
                    if tid == "sssr":
                        raw_o = next(
                            (
                                m.get("value")
                                for m in compact
                                if m.get("id") == "OVERSHOOT"
                            ),
                            None,
                        )
                        try:
                            over_dummy = abs(float(raw_o) - 0.12) < 1e-6
                        except (TypeError, ValueError):
                            over_dummy = True
                    if not any(_finite_stamp(m) for m in stamped):
                        errors.append(
                            f"{row['part_key']} {tid}: no stamped measurements"
                        )
                    elif banned:
                        errors.append(
                            f"{row['part_key']} {tid}: banned stamp {banned}"
                        )
                    elif bw_hit:
                        errors.append(
                            f"{row['part_key']} {tid}: BW>70 MHz stamp {bw_hit}"
                        )
                    elif invalid_hit:
                        errors.append(
                            f"{row['part_key']} {tid}: Rigol-invalid stamp "
                            f"{invalid_hit} (unknown ITEM, not a value)"
                        )
                    elif tid not in MUST_STAMP and tid not in MUST_STAMP_ANY:
                        errors.append(
                            f"{row['part_key']} {tid}: MUST_STAMP missing measurement id"
                        )
                    elif tid in MUST_STAMP_ANY:
                        if not any(_stamp_hit(ids_st, p) for p in MUST_STAMP_ANY[tid]):
                            errors.append(
                                f"{row['part_key']} {tid}: missing stamp "
                                f"{'/'.join(MUST_STAMP_ANY[tid])}"
                            )
                    elif not _stamp_hit(ids_st, str(want)):
                        errors.append(
                            f"{row['part_key']} {tid}: missing stamp {want}"
                        )
                    elif iout_dead:
                        errors.append(
                            f"{row['part_key']} ioutmax: IOUTMAX_V looks like "
                            "Schmitt CH2, not VOUT"
                        )
                    elif iout_vin_alias:
                        errors.append(
                            f"{row['part_key']} ioutmax: IOUTMAX_V follows VIN "
                            "(SIM DMM on VIN, not VOUT)"
                        )
                    elif lir_vin_alias:
                        errors.append(
                            f"{row['part_key']} lir: LIR_mV looks like VIN alias "
                            "(|dVIN|*1000 or VIN*1000), not VOUT regulation"
                        )
                    elif iq_yaml_vout:
                        errors.append(
                            f"{row['part_key']} iq: VOUT_V yaml stamp "
                            "(DMM is current, not VOUT)"
                        )
                    elif iq_flat_vin:
                        errors.append(
                            f"{row['part_key']} iq: IQ_uA flat vs VIN "
                            "(SIM followed VOUT-bias ICC, not VIN)"
                        )
                    elif fmax_dead:
                        errors.append(
                            f"{row['part_key']} fmax: FMAX_Mbps=0 "
                            "(SIM CHAN2 followed OE DC, not DUT Y)"
                        )
                    elif edge_dead:
                        errors.append(
                            f"{row['part_key']} {tid}: MSO edge stamp looks like "
                            "SIM 0.12 s dummy, not ns-class RTime"
                        )
                    elif serial_dead:
                        errors.append(
                            f"{row['part_key']} serial_shift: Q7_LOW must follow "
                            "A=0 after CLK, not VCC"
                        )
                    elif pulse_dummy:
                        errors.append(
                            f"{row['part_key']} pulse_width: PULSE_ns looks like "
                            "SIM 500 ns CHAN2 dummy, not 0.5/f"
                        )
                    elif npr_dead:
                        errors.append(
                            f"{row['part_key']} no_phase_reversal: NPR_VPP_V "
                            "looks like G11*6 V, not BUFFER clip"
                        )
                    elif over_dummy:
                        errors.append(
                            f"{row['part_key']} sssr: OVERSHOOT looks like "
                            "SIM 0.12 unknown-item dummy"
                        )
                    elif any_fail(meas):
                        fails = [
                            f"{m.get('id')}={m.get('value')} "
                            f"min={m.get('min')} max={m.get('max')}"
                            for m in meas
                            if isinstance(m, dict) and m.get("result") == "fail"
                        ]
                        errors.append(
                            f"{row['part_key']} {tid}: SPEC FAIL {', '.join(fails)}"
                        )
                    else:
                        stats["ok"] += 1
            core.close_session()
    except Exception as exc:
        errors.append(f"sim_run_all_enabled crashed: {exc}")
    finally:
        time.sleep = old_sleep
        pathmod.TEST_DB_ROOT = old_root
        dbmod.TEST_DB_ROOT = old_db
        try:
            if core is not None:
                core.close_session()
        except Exception:
            pass
    if stats["ran"] < 1:
        errors.append("SIM ran zero enabled tests")
    stamp_path = STAMPS_PATH
    if family:
        stamp_path = STAMPS_PATH.with_name(f"sim_stamps_{family}.json")
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(
        json.dumps(
            {
                "n": len(stats.get("stamps") or []),
                "ok": stats.get("ok"),
                "ran": stats.get("ran"),
                "family": family or "all",
                "rows": stats.get("stamps") or [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return errors, stats


def main() -> int:
    family = scale_family_from_argv()
    errors = check_all_parts(family=family)
    plan = usb_keep_plan(family=family)
    mso_plan = usb_mso_plan(family=family)
    rows = filter_part_rows(load_part_rows(), family)
    stubs = [r["part_key"] for r in rows if r.get("stub")]
    from ate.core.physics_scale import PROOF_PATH, classify_enabled, write_proof

    phys_rows, phys_errors = classify_enabled(family=family)

    proof_path = (
        PROOF_PATH
        if not family
        else PROOF_PATH.with_name(f"physics_enabled_{family}.json")
    )
    write_proof(phys_rows, proof_path)
    leftover_n = sum(1 for r in phys_rows if r.get("status") == "LEFTOVER")
    realized_n = sum(1 for r in phys_rows if r.get("status") == "REALIZED")
    errors.extend(phys_errors)
    sim_errors, stats = sim_run_all_enabled(family=family)
    errors.extend(sim_errors)
    fam_tag = family or "all"
    if errors:
        print("FAIL check_all_parts:")
        for e in errors:
            print(f"  - {e}")
        print(
            f"family={fam_tag} SIM {stats.get('ok')}/{stats.get('ran')} "
            f"parts={stats.get('parts')} scaffold={stats.get('scaffold')} "
            f"physics REALIZED={realized_n} LEFTOVER={leftover_n}"
        )
        return 1
    print(
        f"OK check_all_parts: family={fam_tag} yaml={len(rows)} keep_parts={len(plan)} "
        f"mso_parts={len(mso_plan)} stub={stubs} known={sorted(load_known_visa())} "
        f"SIM {stats['ok']}/{stats['ran']} parts={stats['parts']} "
        f"physics REALIZED={realized_n} LEFTOVER={leftover_n}"
    )
    for p in plan:
        print(f"  KEEP {p['part_key']} {p['family']} {p['keep']}")
        if p.get("mso"):
            print(f"  MSO  {p['part_key']} {p['mso']}")
    for p in mso_plan:
        if p["part_key"] not in {x["part_key"] for x in plan}:
            print(f"  MSO  {p['part_key']} {p['family']} {p['mso']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
