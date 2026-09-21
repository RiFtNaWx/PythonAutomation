"""Fail-closed: lab-report sheets map to existing TestSpecs (all families).

Run: python -m ate.core.check_report_coverage
"""
from __future__ import annotations

import sys


def main() -> int:
    errors: list[str] = []
    from ate.core.report_coverage import SHEET_TO_IDS, audit

    if "vix" not in SHEET_TO_IDS or SHEET_TO_IDS["vix"] != ("vih_vil",):
        errors.append("VIX sheet must map to vih_vil")
    if "vox" not in SHEET_TO_IDS:
        errors.append("VOX sheet must map to voh_load/vol_load")
    got = audit(write=True)
    if not got.get("parts"):
        errors.append("audit returned no parts")
    fmts = got.get("formats") or {}
    if "logic_lab_vix_vox" not in fmts:
        errors.append("expected at least one Logic VIX/VOX lab report")
    by = {str(p.get("part_key")): p for p in got.get("parts") or []}

    g07 = by.get("rs1g07") or {}
    en07 = set(g07.get("enabled") or [])
    sheets07 = {str(s) for s in g07.get("sheets") or []}
    mapped07_ids = {m.get("sheet"): m.get("ids") for m in g07.get("mapped") or []}
    if "VIX" in sheets07:
        if "vih_vil" not in (mapped07_ids.get("VIX") or []):
            errors.append(f"rs1g07 VIX must map to vih_vil, got {mapped07_ids.get('VIX')}")
        if "VOL" in sheets07:
            vol_ids = set(mapped07_ids.get("VOL") or [])
            if "vol_load" not in vol_ids and "vol" not in vol_ids:
                errors.append("rs1g07 VOL (open-drain) must map to vol_load or vol")
        if "voh_load" in en07:
            errors.append("rs1g07 must not enable voh_load")
    if "CIN" in sheets07 and "cin" not in (mapped07_ids.get("CIN") or []):
        errors.append("rs1g07 CIN sheet must map to cin TestSpec")

    g08 = by.get("rs1g08") or {}
    leftover = set(g08.get("opamp_leftover") or [])
    if "SR" in (g08.get("sheets") or []) and "SR" not in leftover:
        errors.append("rs1g08 SR sheet is opamp leftover, not a Logic TestSpec")
    mapped08_ids = {m.get("sheet"): m.get("ids") for m in g08.get("mapped") or []}
    if "VOX" in (g08.get("sheets") or []):
        hit = mapped08_ids.get("VOX") or []
        if "voh_load" not in hit or "vol_load" not in hit:
            errors.append(f"rs1g08 VOX must map to voh_load+vol_load, got {hit}")

    g622 = by.get("rs622") or {}
    en622 = set(g622.get("enabled") or [])
    for tid in ("slew", "gbw"):
        if tid not in en622:
            errors.append(f"rs622 fixture_modes must include {tid}")

    soo = by.get("rs29511") or {}
    en_soo = set(soo.get("enabled") or [])
    for banned in ("vih_vil", "voh_load", "vol_load"):
        if banned in en_soo:
            errors.append(f"rs29511 must not dump Ariff {banned}")

    src = __import__("ate.core.ocr_engine", fromlist=["_SKIP"])._SKIP
    if "qianfan" not in src:
        errors.append("ocr_engine must keep qianfan parked")

    from ate.core.paths import PATH_RULE

    if "Slice at #Test_Database" not in PATH_RULE:
        errors.append("PATH_RULE must tell later AI to slice at #Test_Database")
    root_s = str(got.get("reports_root") or "")
    if "C:\\Users\\" in root_s or "OoiJianHong" in root_s:
        errors.append(f"coverage reports_root must be portable, got {root_s}")
    for p in got.get("parts") or []:
        xlsx = str(p.get("xlsx") or "")
        if "C:\\Users\\" in xlsx or xlsx.startswith("C:"):
            errors.append(f"{p.get('part_key')} xlsx must be relative, got {xlsx}")
            break
    if not got.get("path_rule"):
        errors.append("coverage.json must include path_rule for later AI export")

    if errors:
        print("FAIL check_report_coverage:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        "OK check_report_coverage: report sheets map to existing TestSpecs; "
        f"formats={got.get('formats')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
