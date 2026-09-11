"""Fail-closed RS622 campaign outline. FILL_ME and missing fixture_mode must fail.

Run: python -m ate.core.check_campaign_outline
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import yaml
from openpyxl import Workbook

from ate.core.campaign_outline import (
    attach_known_values,
    iter_campaign_maps,
    outline_errors,
    outline_from_workbook,
    outline_test,
    upgrade_sheet_map,
    _xlsx_from_map,
)
from ate.core.paths import PART_DB_ROOT, TEST_DB_ROOT


def _header(**extra: object) -> dict:
    data = {
        "component": "Logic",
        "part": "X",
        "package": "Y",
        "version": "Version_1",
        "sample_size": 4,
        "workbook": {"path": "../workbook/x.xlsx"},
        "naming": {
            "screenshot": "{TEST}_{DUT}_{VARIANT}_{TIMESTAMP}.jpg",
            "graph": "{TEST}_{DUT}_{VARIANT}_{TIMESTAMP}.png",
        },
        "tests": {},
    }
    data.update(extra)
    return data


def _memory_errors() -> list[str]:
    errors: list[str] = []
    missing = _header(
        tests={"VOH": {"folder": "VOH", "excel_sheet": "VOH"}},
    )
    miss = outline_errors(missing)
    if not any("fixture_mode" in e for e in miss):
        errors.append("outline_errors must fail when fixture_mode is missing")

    fill = _header(
        tests={
            "GBW": {
                "folder": "GBW",
                "excel_sheet": "GBW",
                "fixture_mode": "FILL_ME",
                "automated": False,
                "dut_iterations": 4,
                "paste": {"values": "FILL_ME", "photos": "FILL_ME"},
            },
            "Summary": {
                "folder": "Summary",
                "excel_sheet": "Summary",
                "fixture_mode": "FILL_ME",
                "automated": False,
                "dut_iterations": 4,
            },
        }
    )
    if not outline_errors(fill):
        errors.append("FILL_ME fixture_mode/paste must fail outline_errors")
    upgraded = upgrade_sheet_map(fill, family="opamp", sheets=["GBW", "Summary"])
    dumped = yaml.safe_dump(upgraded)
    if "FILL_ME" in dumped:
        errors.append("upgrade_sheet_map must strip FILL_ME")
    if "Summary" in (upgraded.get("tests") or {}):
        errors.append("upgrade must drop Summary stub")
    gbw = (upgraded.get("tests") or {}).get("GBW") or {}
    if gbw.get("fixture_mode") != "G11":
        errors.append(f"GBW FILL_ME must infer G11, got {gbw.get('fixture_mode')!r}")
    if gbw.get("automated") is not True:
        errors.append("FILL_ME stub automated false must become true")

    from_sheets = outline_from_workbook(
        component="Logic",
        part="RS1G08",
        package="SOT23",
        version="Version_1",
        sample_size=4,
        workbook_name="RS1G08_Lab_Report.xlsx",
        sheets=["Summary", "VOX", "ICC", "VOH"],
        family="logic",
    )
    tests = from_sheets.get("tests") or {}
    if "Summary" in tests:
        errors.append("tests_from_sheets must skip Summary")
    voh = tests.get("VOH") or {}
    if voh.get("excel_sheet") != "VOX":
        errors.append(f"VOX workbook must map VOH excel_sheet VOX, got {voh}")
    if (tests.get("Supply_Current") or {}).get("excel_sheet") != "ICC":
        errors.append("ICC sheet must map Supply_Current excel_sheet ICC")
    if outline_errors(from_sheets):
        errors.append("outline_from_workbook result must pass outline_errors: " + str(outline_errors(from_sheets)))

    tmp = Path(tempfile.mkdtemp(prefix="ate_outline_"))
    xlsx = tmp / "lab.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "VOX"
    wb.create_sheet("ICC")
    wb.save(xlsx)
    wb.close()
    hooked = {
        "voh_load": outline_test(
            folder="VOH",
            excel_sheet="VOH",
            fixture_mode="LOGIC",
            sample=4,
        ),
        "vol_load": outline_test(
            folder="VOL",
            excel_sheet="VOL",
            fixture_mode="LOGIC",
            sample=4,
        ),
        "supply_current_sweep": outline_test(
            folder="Supply_Current",
            excel_sheet="Supply_Current",
            fixture_mode="LOGIC",
            sample=4,
        ),
    }
    attach_known_values(hooked, ["VOX", "ICC"], xlsx)
    if hooked["voh_load"].get("excel_sheet") != "VOX":
        errors.append("attach_known_values must remap voh_load to VOX")
    if hooked["voh_load"].get("paste", {}).get("values", {}).get("VOH_4p5V") != ["G16", "H16", "I16"]:
        errors.append("attach_known_values must set VOH_4p5V G16:I16")
    if hooked["supply_current_sweep"].get("paste", {}).get("values", {}).get("ICC_uA") != "D10":
        errors.append("attach_known_values must set ICC_uA D10")
    return errors


def _live_errors() -> list[str]:
    errors: list[str] = []
    gold = PART_DB_ROOT / "_manifest" / "sheet_map.yaml"
    if not gold.is_file():
        return [f"RS622 TTSOP8 sheet_map missing: {gold}"]
    gold_data = yaml.safe_load(gold.read_text(encoding="utf-8")) or {}
    gbw_vals = (
        ((gold_data.get("tests") or {}).get("GBW") or {}).get("paste") or {}
    ).get("values") or {}
    if "GBW_MHz" not in gbw_vals:
        errors.append("RS622 TTSOP8 tests.GBW.paste.values.GBW_MHz missing")
    gold_errs = outline_errors(gold_data)
    if gold_errs:
        errors.append("RS622 TTSOP8 outline: " + "; ".join(gold_errs[:8]))

    logic = (
        TEST_DB_ROOT
        / "Logic"
        / "RS1G08"
        / "SOT23"
        / "Ariff"
        / "Version_1"
        / "_manifest"
        / "sheet_map.yaml"
    )
    if logic.is_file():
        logic_data = yaml.safe_load(logic.read_text(encoding="utf-8")) or {}
        tests = logic_data.get("tests") or {}
        voh = tests.get("VOH") or tests.get("voh_load") or {}
        vals = ((voh.get("paste") or {}).get("values") or {})
        if "VOH_4p5V" not in vals:
            errors.append("RS1G08 Ariff SOT23 must keep VOH_4p5V on VOX")
        xlsx = _xlsx_from_map(logic, logic_data)
        if xlsx is not None:
            from openpyxl import load_workbook

            wb = load_workbook(xlsx, read_only=True)
            try:
                names = set(wb.sheetnames)
            finally:
                wb.close()
            if "VOX" in names and str(voh.get("excel_sheet") or "") != "VOX":
                errors.append("RS1G08 workbook has VOX but excel_sheet is not VOX")
    else:
        errors.append(f"RS1G08 Ariff sheet_map missing: {logic}")

    for path in iter_campaign_maps():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            errors.append(f"{path}: not a map")
            continue
        rel = str(path)
        for err in outline_errors(raw):
            errors.append(f"{rel}: {err}")
        text = path.read_text(encoding="utf-8")
        if "FILL_ME" in text:
            errors.append(f"{rel}: FILL_ME still present")
        tests = raw.get("tests") if isinstance(raw.get("tests"), dict) else {}
        xlsx = _xlsx_from_map(path, raw)
        if not tests and xlsx is not None and xlsx.is_file():
            errors.append(f"{rel}: empty tests with workbook present")
        if len(errors) > 40:
            errors.append("... truncated campaign outline errors")
            break
    return errors


def main() -> int:
    errors = _memory_errors() + _live_errors()
    if errors:
        print("FAIL campaign_outline:")
        for line in errors:
            print(f"  - {line}")
        return 1
    print("OK campaign_outline: RS622 keys, no FILL_ME, known VOX/ICC/GBW paste")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
