"""Fail-closed REALIZED | LEFTOVER map for every enabled (part_key, test_id).

SIM 218/218 is not physics proof. Missing classification = check fail.
Do not mark analog-switch BW, BUFFER AOL_dB, or CMOS OE->Y on RS29511 REALIZED.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from ate.core.check_all_parts import load_part_rows
from ate.core.paths import REPO_ROOT
from ate.core.registry import all_tests, load_family

PROOF_PATH = Path(__file__).resolve().parent / "_check_data" / "physics_enabled.json"

# Path B bodies that match this bench (70 MHz MSO, DMM DC, 10 mA switch force).
REALIZED_IDS = frozenset(
    {
        "cin",
        "cpd",
        "vih_vil",
        "voh_load",
        "vol_load",
        "delta_supply_current",
        "off_current",
        "input_thresholds",
        "ioff_leakage",
        "ioz",
        "input_leakage_sweep",
        "supply_current_sweep",
        "ten",
        "tdis",
        "tp",
        "tidle",
        "clk_q",
        "serial_shift",
        "pulse_width",
        "ioff",
        "icc",
        "ii",
        "delta_icc",
        "input_threshold",
        "vih",
        "vil",
        "voh",
        "vol",
        "il",
        "tpd",
        "tp_rs0204",
        "tsu",
        "th",
        "fmax",
        "tr",
        "tf",
        "tsk",
        "tw",
        "i2c_ii",
        "i2c_cioff",
        "iplus",
        "leakage_off",
        "leakage_on",
        "input_leakage",
        "vth",
        "ton_toff",
        "con_coff",
        "tbbm",
        "usb_ton_toff",
        "iq",
        "vinmin",
        "lir",
        "lor",
        "ioutmax",
        "enable_current",
        "slew",
        "gbw",
        "ort",
        "psrr",
        "cmrr",
        "vohl",
        "power_on_time",
        "vos_sweep",
        "ac_gain_check",
        "ac_vin_sweep",
        "sssr",
        "lssr",
        "no_phase_reversal",
    }
)

LEFTOVER_REASON: dict[str, str] = {
    "iso": "1 MHz high-Z, not 110 MHz 50 ohm RF (MSO 70 MHz)",
    "xtalk": "1 MHz high-Z, not 110 MHz 50 ohm RF (MSO 70 MHz)",
    "usb_iso": "1 MHz high-Z, not 550 MHz 50 ohm RF (MSO 70 MHz)",
    "usb_xtalk": "1 MHz high-Z, not 550 MHz 50 ohm RF (MSO 70 MHz)",
    "settling": "photo/cursor; stamp SETTLE_VPP_V (CHAN2 swing), not 0.1% SETTLE_us",
    "noise": "0.1-10 Hz Vpp, not nV/rtHz; ISC missing",
    "aol": "mapped screenshot; BUFFER/G11 cannot measure open-loop AOL_dB",
    "emirr": "mapped screenshot, not RF EMIRR_dB",
    "output_voltage": "no Path B body; do not wrap logic_tests.test_output_voltage",
    "cap_load": "no Path B body; do not wrap logic_tests.test_cap_load",
    "supply_current": "no Path B body unless eugene IDD / rs29511 ICC",
    "ron": "10 mA platform; rON min/max still PDF image",
    "usb_ron": "10 mA platform; rON min/max still PDF image",
    "i2c_ron": "10 mA platform; datasheet 64 mA leftover",
}

LEFTOVER_IDS = frozenset(LEFTOVER_REASON)

# Pair leftover wins over id tables (keep BW/AOL fake-proof even if someone moves ids).
LEFTOVER_PAIRS: dict[tuple[str, str], str] = {
    ("rs2323", "iso"): LEFTOVER_REASON["iso"],
    ("rs2323", "xtalk"): LEFTOVER_REASON["xtalk"],
    ("rs2323", "ron"): LEFTOVER_REASON["ron"],
    ("rs2227", "usb_iso"): LEFTOVER_REASON["usb_iso"],
    ("rs2227", "usb_xtalk"): LEFTOVER_REASON["usb_xtalk"],
    ("rs2227", "usb_ron"): LEFTOVER_REASON["usb_ron"],
    ("rs0302", "i2c_ron"): LEFTOVER_REASON["i2c_ron"],
    ("rs622", "settling"): LEFTOVER_REASON["settling"],
    ("rs622", "noise"): LEFTOVER_REASON["noise"],
    ("rs358", "settling"): LEFTOVER_REASON["settling"],
    ("rs358", "noise"): LEFTOVER_REASON["noise"],
    ("lm358", "settling"): LEFTOVER_REASON["settling"],
    ("rs8551", "noise"): LEFTOVER_REASON["noise"],
    ("rs1g00", "supply_current"): "no eugene_cap IDD; UNCONFIRMED DRAFT numbers HOLD",
    ("rs1g02", "supply_current"): "no eugene_cap IDD; UNCONFIRMED DRAFT numbers HOLD",
    ("rs1g04", "supply_current"): "no eugene_cap IDD; UNCONFIRMED DRAFT numbers HOLD",
    ("rs1g86", "supply_current"): "no eugene_cap IDD; UNCONFIRMED DRAFT numbers HOLD",
    ("rs2g08", "supply_current"): "no eugene_cap IDD; UNCONFIRMED DRAFT numbers HOLD",
    ("rs2g32", "supply_current"): "no eugene_cap IDD; UNCONFIRMED DRAFT numbers HOLD",
}

# Pair realized wins over leftover ids (RS29511 tp is not CMOS wrap).
REALIZED_PAIRS: dict[tuple[str, str], str] = {
    ("rs29511", "tp"): "Path B SDAIN->SDAOUT; SIM 50 ns cannot prove tPLZ 10 ns",
    ("rs29511", "tidle"): "Path B same edges at 100 kHz; SIM 50 ns leftover vs tPLZ 10 ns",
    ("rs29511", "supply_current"): "Path B ICC SDAIN=0 + 10k OUT; SIM CMOS uA not 2.0/4.5 mA PDF",
    ("rs29511", "output_voltage"): "Path B READY 10k pull-up idle high",
    ("rs29511", "cap_load"): "Path B DMM CAP SDAIN; SIM 5 pF vs CIO typ 6.5 leftover",
    ("rs1g07", "supply_current"): "eugene_cap IDD Path B",
    ("rs74aup1g07", "supply_current"): "eugene_cap IDD Path B",
    ("rs1g14", "supply_current"): "eugene_cap IDD Path B",
    ("rs1g125", "supply_current"): "eugene_cap IDD Path B",
    ("rs164", "supply_current"): "eugene_cap IDD Path B",
    ("rs1g74", "supply_current"): "eugene_cap IDD Path B",
    ("rs1g123", "supply_current"): "eugene_cap IDD Path B",
    ("rs622", "vos_sweep"): "Path B G201 CHAN2 VOUT; SIM Vos_dut=0 slope~201 not CHAN1=AWG",
    ("rs622", "ac_gain_check"): "Path B G201 CHAN2 VPP/amp; closed-loop GAIN_VV not AOL_dB",
    ("rs622", "ac_vin_sweep"): "Path B G201 CHAN2 VPP/amp sweep; closed-loop GAIN_VV not AOL_dB",
    ("rs8551", "vos_sweep"): "Path B G201 CHAN2 VOUT; SIM Vos_dut=0 slope~201 not CHAN1=AWG",
    ("rs74aup1g07", "vih_vil"): "Ariff Path B VIH/VIL at 1.8/2.5/3.3; VOH/VOL stay disabled until PDF",
}

# If enabled, these must stay LEFTOVER (do not fake BW / AOL / 0.1% settle).
MUST_STAY_LEFTOVER = frozenset(LEFTOVER_PAIRS)


def _ensure_families_loaded(family: str = "") -> tuple[dict[str, str], list[str]]:
    """load_family clears the registry; snapshot TestSpec files per family."""
    errors: list[str] = []
    files: dict[str, str] = {}
    seen: set[str] = set()
    from ate.core.check_all_parts import filter_part_rows

    for prow in filter_part_rows(load_part_rows(), family):
        if prow.get("error") or prow.get("stub"):
            continue
        fam = str(prow.get("family") or "")
        if not fam or fam in seen:
            continue
        seen.add(fam)
        try:
            load_family(fam)
        except Exception as exc:
            errors.append(f"physics_scale load_family({fam!r}): {exc}")
            continue
        for spec in all_tests():
            files[spec.id] = _spec_file_from_spec(spec)
    return files, errors


def _spec_file_from_spec(spec: Any) -> str:
    try:
        path = Path(inspect.getfile(spec.run)).resolve()
    except (OSError, TypeError):
        return ""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def classify_one(part_key: str, test_id: str) -> tuple[str, str]:
    pk = str(part_key or "").strip().lower()
    tid = str(test_id or "").strip()
    key = (pk, tid)
    if key in LEFTOVER_PAIRS:
        return "LEFTOVER", LEFTOVER_PAIRS[key]
    if key in REALIZED_PAIRS:
        return "REALIZED", REALIZED_PAIRS[key]
    if tid in LEFTOVER_IDS:
        return "LEFTOVER", LEFTOVER_REASON[tid]
    if tid in REALIZED_IDS:
        return "REALIZED", ""
    return "UNCLASSIFIED", ""


def classify_enabled(family: str = "") -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    files, errors = _ensure_families_loaded(family)
    from ate.core.check_all_parts import filter_part_rows

    for prow in filter_part_rows(load_part_rows(), family):
        if prow.get("error"):
            errors.append(f"{prow.get('part_key')}: {prow['error']}")
            continue
        if prow.get("stub"):
            continue
        pk = str(prow.get("part_key") or "")
        for tid in prow.get("ids") or []:
            status, why = classify_one(pk, str(tid))
            rec = {
                "part_key": pk,
                "test_id": tid,
                "status": status,
                "why": why,
                "file": files.get(str(tid), ""),
            }
            rows.append(rec)
            if status == "UNCLASSIFIED":
                errors.append(f"{pk} {tid}: unclassified -- REALIZED or LEFTOVER required")
            if not rec["file"]:
                errors.append(f"{pk} {tid}: missing TestSpec file")
            key = (pk, str(tid))
            if key in MUST_STAY_LEFTOVER and status != "LEFTOVER":
                errors.append(f"{pk} {tid}: must stay leftover-honest ({LEFTOVER_PAIRS[key]})")
    if not rows:
        errors.append("physics_scale: no enabled (part, test) rows")
    return rows, errors


def write_proof(rows: list[dict[str, Any]], path: Path | None = None) -> Path:
    """File-level proof: every enabled (part_key, test_id) REALIZED or LEFTOVER."""
    import json

    leftover = [r for r in rows if r.get("status") == "LEFTOVER"]
    realized = [r for r in rows if r.get("status") == "REALIZED"]
    dest = path or PROOF_PATH
    doc = {
        "n": len(rows),
        "realized": len(realized),
        "leftover": len(leftover),
        "rows": rows,
        "leftover_named": leftover,
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return dest


def check_physics_scale() -> list[str]:
    rows, errors = classify_enabled()
    write_proof(rows)
    return errors


def main() -> int:
    from ate.core.check_all_parts import scale_family_from_argv

    family = scale_family_from_argv()
    rows, errors = classify_enabled(family=family)
    leftover = [r for r in rows if r.get("status") == "LEFTOVER"]
    realized = [r for r in rows if r.get("status") == "REALIZED"]
    dest = (
        PROOF_PATH
        if not family
        else PROOF_PATH.with_name(f"physics_enabled_{family}.json")
    )
    proof = write_proof(rows, dest)
    if errors:
        print("FAIL physics_scale:")
        for e in errors:
            print(f"  - {e}")
        print(f"rows={len(rows)} REALIZED={len(realized)} LEFTOVER={len(leftover)}")
        return 1
    print(
        f"OK physics_scale: rows={len(rows)} "
        f"REALIZED={len(realized)} LEFTOVER={len(leftover)} "
        f"proof={proof.name}"
    )
    for r in leftover:
        print(f"  LEFTOVER {r['part_key']} {r['test_id']}: {r['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
