"""Open inventory: AnalogSwitch RS2323 + Logic RS1G07/14 + Level RS0204 + Power RS3213.

Run: python -m ate.core.check_open_inventory
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

from ate.core.database import family_for_component, find_campaign_root, set_context
from ate.core.paths import PARTS_DIR, TEST_DB_ROOT
from ate.core.registry import all_tests, load_family
from ate.fixture.modes import enabled_tests_for_part, logic_catalog_for_ui

_LIM_IDS = frozenset({"iplus", "leakage_off", "leakage_on", "input_leakage"})
_LOGIC_PARTS = ("rs29511", "rs1g08", "rs1g07", "rs1g14")


_VENDOR_IMPORT = re.compile(r"(?m)^\s*(?:import|from)\s+(Ariff|Lim|Soo)\b")
_TESTS_ROOT = Path(__file__).resolve().parents[1] / "tests"


def _ast_calls_input(src: str) -> bool:
    tree = ast.parse(src)
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
        for node in ast.walk(tree)
    )


def _assert_tests_clean() -> list[str]:
    errors: list[str] = []
    for path in sorted(_TESTS_ROOT.rglob("*.py")):
        src = path.read_text(encoding="utf-8-sig")
        rel = path.relative_to(_TESTS_ROOT.parent.parent)
        try:
            calls_input = _ast_calls_input(src)
        except SyntaxError as exc:
            errors.append(f"{rel}: cannot parse ({exc})")
            continue
        if calls_input:
            errors.append(f"{rel}: must not call input()")
        vendor = _VENDOR_IMPORT.search(src)
        if vendor:
            errors.append(f"{rel}: must not import {vendor.group(1)}.*")
    return errors


def check_open_inventory() -> list[str]:
    errors: list[str] = []

    # Part yaml present
    for key in ("rs2323", "rs1g07", "rs1g14", "rs3213", "rs0204"):
        p = PARTS_DIR / f"{key}.yaml"
        if not p.is_file():
            errors.append(f"part yaml missing: {p}")

    # Campaigns (operator folder or legacy Package/Version)
    need = [
        ("AnalogSwitch", "RS2323", "MSOP", "Version_1", "SeeLim"),
        ("Logic", "RS1G07", "SOT23", "Version_1", "Eugene"),
        ("Logic", "RS1G14", "SOT23", "Version_1", "Eugene"),
        ("Level", "RS0204", "TSSOP14", "Version_1", "ChangThong"),
        ("Power", "RS3213", "SOT23-5", "Version_1", "Eugene"),
    ]
    for component, part, package, version, operator in need:
        root = find_campaign_root(component, part, package, version, operator=operator)
        if root is None:
            errors.append(f"campaign missing: {component}/{part}/{package}/{operator}/{version}")
        elif not (root / "_manifest" / "sheet_map.yaml").is_file():
            errors.append(f"sheet_map missing under {root}")
    if (TEST_DB_ROOT / "Level" / "Stub").is_dir():
        errors.append("Level/Stub still present -- run python -m ate.core.seed_classified_campaigns --apply")
    pwr = find_campaign_root("Power", "RS3213", "SOT23-5", "Version_1", operator="Eugene")
    if pwr is not None and not (pwr / "IQ").is_dir():
        errors.append(f"Power RS3213 must track IQ test folder under {pwr}")

    for key in _LOGIC_PARTS:
        if not (PARTS_DIR / f"{key}.yaml").is_file():
            errors.append(f"logic part yaml missing: {key}")

    # Lim family load
    load_family("switch")
    lim_ids = {t.id for t in all_tests()}
    missing = sorted(_LIM_IDS - lim_ids)
    if missing:
        errors.append(f"switch missing specs: {missing}")
    bad_modes = {
        t.id for t in all_tests() if t.fixture_mode in ("G11", "BUFFER", "G_NEG100")
    }
    if bad_modes:
        errors.append(f"switch has OPA fixture modes: {sorted(bad_modes)}")

    modes = logic_catalog_for_ui("rs2323")
    if not modes or modes[0].get("mode") != "LIM_RS2323":
        errors.append("rs2323 fixture catalog must expose LIM_RS2323")

    enabled = enabled_tests_for_part("rs2323")
    if not enabled or set(enabled) != _LIM_IDS:
        errors.append(f"rs2323 enabled_tests mismatch: {enabled}")

    # Lim campaign map vs lab_sheet
    set_context(
        component="AnalogSwitch",
        part="RS2323",
        package="MSOP",
        operator="SeeLim",
        version="Version_1",
        part_key="rs2323",
    )
    from ate.core.database import get_context, load_owners

    ctx = get_context()
    if family_for_component("AnalogSwitch") != "switch":
        errors.append("AnalogSwitch component must map to family switch")
    if family_for_component("Lim") != "switch":
        errors.append("legacy Lim component must map to family switch")
    ids = {str(o.get("id")) for o in load_owners()}
    if "lim" not in ids or "eugene" not in ids:
        errors.append("owners.yaml must list lim and eugene")
    sm = yaml.safe_load(ctx.sheet_map_path().read_text(encoding="utf-8")) or {}
    tests = sm.get("tests") or {}
    sheets = {t.lab_sheet for t in all_tests() if t.lab_sheet}
    for key, entry in tests.items() if isinstance(tests, dict) else []:
        if isinstance(entry, dict) and entry.get("excel_sheet") not in sheets:
            errors.append(f"switch map {key}->{entry.get('excel_sheet')} unregistered")

    errors += _assert_tests_clean()

    # Logic RS1G07 enable list uses Ariff ids
    load_family("logic")
    for pk in ("rs1g07", "rs1g14"):
        en = enabled_tests_for_part(pk)
        if not en:
            errors.append(f"{pk}: enabled_tests empty")
            continue
        ids = {t.id for t in all_tests()}
        miss = [t for t in en if t not in ids]
        if miss:
            errors.append(f"{pk}: enabled ids not registered: {miss}")

    # Restore OpAmp
    set_context(
        component="OpAmp",
        part="RS622",
        package="TTSOP8",
        operator="Eugene",
        version="Version_1",
        part_key="rs622",
    )
    load_family("opamp")
    return errors


def main() -> int:
    errors = check_open_inventory()
    if errors:
        print("FAIL open-inventory:")
        for line in errors:
            print(f"  - {line}")
        return 1
    print("OK open-inventory: AnalogSwitch RS2323 + Logic RS1G07/14 + Level RS0204 + Power RS3213")
    return 0


if __name__ == "__main__":
    sys.exit(main())
