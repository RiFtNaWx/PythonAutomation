"""Self-check: RUN-IC category map + new-product folders in a temp tree.

Run: python -m ate.core.check_new_product
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import yaml

from ate.core.new_product import (
    build_demo_steps,
    category_by_id,
    ensure_product,
    ensure_version,
    load_categories,
    load_inventory,
    load_qualification_main,
    part_key_for,
    qualification_xlsx,
    resolve_inventory_report,
    suite_for_part,
    SHEET_CLASS_CATEGORY,
)
from ate.core.registry import TestSpec


def main() -> int:
    cats = {c["id"]: c for c in load_categories()}
    if "opamp" not in cats or not cats["opamp"].get("live"):
        raise AssertionError("run_ic.yaml must include live opamp")
    if not cats.get("power", {}).get("live") or cats["power"].get("family") != "power":
        raise AssertionError("power LDO suite must be live family=power")
    if cats.get("power", {}).get("family") == "opamp":
        raise AssertionError("Power must not steal OpAmp family")
    if cats.get("comparator", {}).get("live"):
        raise AssertionError("comparator must stay stub until a suite exists")
    if category_by_id("Logic Series")["id"] != "logic":
        raise AssertionError("sheet alias Logic Series must map to logic")
    if category_by_id("Level Shifters")["id"] != "level":
        raise AssertionError("sheet alias Level Shifters must map to level (not logic)")
    if category_by_id("Linear Regulator")["id"] != "power":
        raise AssertionError("sheet alias Linear Regulator must map to power")
    if category_by_id("LDO")["id"] != "power":
        raise AssertionError("sheet alias LDO must map to power")
    if category_by_id("Low Noise Op-Amp")["id"] != "opamp":
        raise AssertionError("sheet alias Low Noise Op-Amp must map to opamp")
    if category_by_id("Precision Op-Amp")["id"] != "opamp":
        raise AssertionError("sheet alias Precision Op-Amp must map to opamp")
    if category_by_id("Analog Switch")["id"] != "analog_switch":
        raise AssertionError("sheet alias Analog Switch must map to analog_switch")
    inv = load_inventory()
    if len(inv) < 30:
        raise AssertionError("inventory must list tracking-sheet SKUs (not one row per part)")
    sku_keys = [(r.get("part"), r.get("model"), r.get("package"), r.get("lot")) for r in inv]
    if len(sku_keys) != len(set(sku_keys)):
        raise AssertionError("inventory SKU rows must be unique")
    parts = {str(r["part"]).upper() for r in inv}
    for need in ("RS622", "RS2323", "RS0204", "RS3213", "RS0302", "LM358", "RS2227", "RS29511", "RS1GT32D"):
        if need not in parts:
            raise AssertionError(f"inventory missing tracking-sheet part {need}")
    r0204 = [r for r in inv if str(r.get("part") or "").upper() == "RS0204"]
    if any(str(r.get("category") or "") != "level" for r in r0204):
        raise AssertionError("RS0204 tracking class must be level (Level Shifter)")
    if any(str(r.get("ate_suite") or "") != "logic" for r in r0204):
        raise AssertionError("RS0204 ate_suite must stay logic (live dual-rail suite)")
    if any(str(r.get("sheet_class") or "") != "Level Shifters" for r in r0204):
        raise AssertionError("RS0204 sheet_class must be Level Shifters")
    sheet_map = dict(SHEET_CLASS_CATEGORY)
    for row in inv:
        sc = str(row.get("sheet_class") or "").strip()
        if not sc:
            raise AssertionError(f"inventory row {row.get('part')} missing sheet_class")
        want = sheet_map.get(sc)
        if not want:
            raise AssertionError(f"unknown sheet_class {sc!r} on {row.get('part')}")
        if str(row.get("category") or "") != want:
            raise AssertionError(
                f"{row.get('part')} sheet_class {sc!r} must be category {want}, "
                f"got {row.get('category')!r}"
            )

    qrows = load_qualification_main()
    if qualification_xlsx() is not None:
        if len(qrows) < 30:
            raise AssertionError(f"Qualification Main expected ~33 SKUs, got {len(qrows)}")
        for q in qrows:
            sc = q["sheet_class"]
            want = SHEET_CLASS_CATEGORY.get(sc)
            if not want:
                raise AssertionError(f"Qualification Main unknown class {sc!r} on {q['part']}")
            hits = [
                r
                for r in inv
                if str(r.get("part") or "").upper() == str(q["part"]).upper()
                and str(r.get("model") or r.get("part") or "").upper() == str(q["model"] or q["part"]).upper()
                and str(r.get("package") or "") == str(q.get("package") or "")
            ]
            if not hits:
                raise AssertionError(
                    f"inventory missing Qualification SKU {q['part']} {q['model']} {q['package']}"
                )
            if str(hits[0].get("sheet_class") or "") != sc:
                raise AssertionError(
                    f"{q['part']} inventory sheet_class {hits[0].get('sheet_class')!r} != Main {sc!r}"
                )
            if str(hits[0].get("category") or "") != want:
                raise AssertionError(f"{q['part']} category {hits[0].get('category')} != {want}")
        rs1g = resolve_inventory_report(
            next(r for r in inv if str(r.get("part") or "").upper() == "RS1G08" and r.get("report"))
        )
        if rs1g is None or not rs1g.is_file():
            raise AssertionError("RS1G08 report xlsx must resolve under Product Testing Report")
    js = Path(__file__).resolve().parents[1] / "ui" / "web" / "app.js"
    js_text = js.read_text(encoding="utf-8")
    if "ate_suite || row.category" in js_text.replace(" ", ""):
        raise AssertionError("inventory pick must not steal tracking class from ate_suite")
    if "$(\"np-category\").value = row.category" not in js_text:
        raise AssertionError("inventory pick must set RUN-IC class from tracking category")
    if not any(str(r.get("package") or "") == "TSSOP14" for r in r0204):
        raise AssertionError("RS0204 tracking sheet includes TSSOP14")
    r3213 = [r for r in inv if str(r.get("part") or "").upper() == "RS3213"]
    if any(str(r.get("category") or "") != "power" for r in r3213):
        raise AssertionError("RS3213 must be power / LDO")
    r1g08 = [r for r in inv if str(r.get("part") or "").upper() == "RS1G08"]
    if not r1g08 or any(str(r.get("category") or "") != "logic" for r in r1g08):
        raise AssertionError("RS1G08 must stay Logic Series")
    r2323 = [r for r in inv if str(r.get("part") or "").upper() == "RS2323"]
    if not any(str(r.get("package") or "") == "UQFN1.4X1.8-10" for r in r2323):
        raise AssertionError("RS2323 tracking package is UQFN1.4X1.8-10")
    r2227 = [r for r in inv if str(r.get("part") or "").upper() == "RS2227"]
    if not r2227 or any(str(r.get("category") or "") != "analog_switch" for r in r2227):
        raise AssertionError("RS2227 must be analog_switch")
    r29511 = [r for r in inv if str(r.get("part") or "").upper() == "RS29511"]
    if not r29511 or any(str(r.get("category") or "") != "logic" for r in r29511):
        raise AssertionError("RS29511 must stay Logic Series")
    rlm = [r for r in inv if str(r.get("part") or "").upper() == "LM358"]
    if not rlm or any(str(r.get("category") or "") != "opamp" for r in rlm):
        raise AssertionError("LM358 must stay OpAmp")
    if not any(str(r.get("report") or "") for r in inv if str(r.get("part") or "").upper() == "RS1G08"):
        raise AssertionError("RS1G08 must point at Product Testing Report workbook")
    if "RS724-Q1" in parts or "RS722P-Q1" in parts:
        raise AssertionError("do not seed RUN-IC catalog SKUs into inventory")
    from ate.core.migrate_operator_folders import _pic_label_map

    if _pic_label_map().get("RS622") != "Eugene":
        raise AssertionError("RS622 PIC Eugene must survive later SKUs with blank PIC")
    if part_key_for("RS74AUP1G07") != "rs74aup1g07":
        raise AssertionError("part_key_for failed")
    from ate.core.paths import PARTS_DIR

    missing_yaml = sorted(
        {
            part_key_for(str(r.get("part") or ""))
            for r in inv
            if str(r.get("part") or "").strip()
            and not (PARTS_DIR / f"{part_key_for(str(r.get('part') or ''))}.yaml").is_file()
        }
    )
    if missing_yaml:
        raise AssertionError(f"inventory parts missing yaml (not customizable): {missing_yaml}")
    from ate.core.database import DbContext, family_for_component

    if family_for_component("Power") != "power":
        raise AssertionError("Power maps to power family (LDO suite)")
    if family_for_component("Power") == "opamp":
        raise AssertionError("Power must not steal OpAmp family")
    if family_for_component("Comparator") != "":
        raise AssertionError("Comparator is a RUN-IC stub -- must not steal OpAmp family")
    if family_for_component("Level") != "level":
        raise AssertionError("Level component must map to level family")
    if family_for_component("LevelShifters") != "level":
        raise AssertionError("LevelShifters folder name must map to level, not logic")
    if family_for_component("OpAmp") != "opamp":
        raise AssertionError("OpAmp must stay live opamp family")
    logic_photo = DbContext(component="Logic", part="NoSuch", package="X", operator="Eugene")
    if logic_photo._default_photo_test_key() != "Setup":
        raise AssertionError("empty Logic photo folder must be Setup, not ORT")
    opa_photo = DbContext(component="OpAmp", part="NoSuch", package="X", operator="Eugene")
    if opa_photo._default_photo_test_key() != "ORT":
        raise AssertionError("empty OpAmp photo folder must stay ORT")

    tmp = Path(tempfile.mkdtemp(prefix="ate_newprod_"))
    out = ensure_product(
        category_id="logic",
        part="RSDEMO1",
        package="SOT23",
        model="RSDEMO1",
        sample_size=2,
        operator="Ariff",
        open_folder=False,
        apply=False,
        base=tmp,
    )
    root = Path(out["root"])
    if "Ariff" not in str(root):
        raise AssertionError(f"ensure_product root must include operator: {root}")
    sm_text = (root / "_manifest" / "sheet_map.yaml").read_text(encoding="utf-8")
    if "FILL_ME" in sm_text:
        raise AssertionError("ensure_product sheet_map must not write FILL_ME")
    sm_data = yaml.safe_load(sm_text) or {}
    if not sm_data.get("naming") or not sm_data.get("sample_size"):
        raise AssertionError("ensure_product sheet_map must use RS622 outline keys")
    for _key, entry in (sm_data.get("tests") or {}).items():
        if isinstance(entry, dict) and not entry.get("fixture_mode"):
            raise AssertionError("tracked sheet_map tests must include fixture_mode")
    if not (root / "Setup" / "DUT_1" / "graphs").is_dir():
        raise AssertionError("ensure_product must create DUT graph folders")
    again = ensure_product(
        category_id="logic",
        part="RSDEMO1",
        package="SOT23",
        operator="Ariff",
        open_folder=False,
        apply=False,
        base=tmp,
    )
    if again.get("wrote_part_yaml"):
        raise AssertionError("second ensure_product must not clobber yaml")

    rs0204_out = ensure_product(
        category_id="level",
        part="RS0204",
        package="TSSOP14",
        model="RS0204YQ",
        operator="ChangThong",
        open_folder=False,
        apply=False,
        base=tmp,
    )
    if "Level" not in str(rs0204_out["root"]).replace("\\", "/"):
        raise AssertionError(f"RS0204 tracking folder must be Level: {rs0204_out['root']}")
    rnames = {p.name for p in Path(rs0204_out["root"]).iterdir() if p.is_dir()}
    if "GBW" in rnames or "ORT" in rnames:
        raise AssertionError(f"Level RS0204 must not grow OpAmp folders: {sorted(rnames)}")
    if rs0204_out.get("sheet_class") != "Level Shifters":
        raise AssertionError("RS0204 tracking class must stay Level Shifters")
    if rs0204_out.get("family") != "logic":
        raise AssertionError("RS0204 live family must be logic")
    if rs0204_out.get("tracking_category") != "level":
        raise AssertionError("RS0204 tracking_category must be level")
    if suite_for_part("RS0204", component="Level", package="TSSOP14") != "logic":
        raise AssertionError("RS0204 suite_for_part must stay logic")

    ldo = ensure_product(
        category_id="power",
        part="RS3213DEMO",
        package="SOT23-5",
        operator="Eugene",
        open_folder=False,
        apply=False,
        base=tmp,
    )
    if "Power" not in str(ldo["root"]).replace("\\", "/"):
        raise AssertionError(f"Linear Regulator must use Power component: {ldo['root']}")
    names = {p.name for p in Path(ldo["root"]).iterdir() if p.is_dir()}
    if "GBW" in names or "ORT" in names:
        raise AssertionError(f"Power campaign must not grow OpAmp folders: {sorted(names)}")
    if ldo.get("family") != "power":
        raise AssertionError("RS3213 live family must be power")
    if ldo.get("family") != "power" or not ldo.get("live"):
        raise AssertionError("RS3213 campaign must load the power LDO suite")

    try:
        ensure_product(
            category_id="logic",
            part="RS1G08",
            package="SOT23",
            operator="All",
            open_folder=False,
            apply=False,
            base=tmp,
        )
        raise AssertionError("All must not Create folders")
    except ValueError:
        pass

    ariff = ensure_product(
        category_id="logic",
        part="RS1G08",
        package="SOT23",
        operator="Ariff",
        sample_size=2,
        open_folder=False,
        apply=False,
        base=tmp,
    )
    ariff_root = Path(ariff["root"])
    marker = ariff_root / "sessions" / "ariff_only.txt"
    marker.write_text("ariff", encoding="utf-8")
    (ariff_root / "workbook" / "keep.xlsx").write_bytes(b"xlsx-marker")
    chang = ensure_product(
        category_id="logic",
        part="RS1G08",
        package="SOT23",
        operator="ChangThong",
        sample_size=2,
        open_folder=False,
        apply=False,
        base=tmp,
    )
    chang_root = Path(chang["root"])
    if ariff_root == chang_root:
        raise AssertionError("two people on RS1G08 must be two operator folders")
    if "Ariff" not in str(ariff_root) or "ChangThong" not in str(chang_root):
        raise AssertionError(f"RS1G08 trees must include person folders: {ariff_root} {chang_root}")
    if marker.read_text(encoding="utf-8") != "ariff":
        raise AssertionError("second operator must not clobber the first person's sessions")
    if list(ariff_root.rglob("*.py")) or list(chang_root.rglob("*.py")):
        raise AssertionError("Create folders must not copy test Python into #Test_Database")
    ver = ensure_version(
        component="Logic",
        part="RS1G08",
        package="SOT23",
        operator="Ariff",
        version="Version_2",
        copy_from_version="Version_1",
        sample_size=2,
        open_folder=False,
        apply=False,
        base=tmp,
    )
    v2 = Path(ver["root"])
    if v2.name != "Version_2" or "Ariff" not in str(v2):
        raise AssertionError(f"new Version must stay under that person: {v2}")
    if list((v2 / "workbook").glob("*.xlsx")):
        raise AssertionError("ensure_version must not clone xlsx")
    if (chang_root.parent / "Version_2").exists():
        raise AssertionError("new Version must not appear under the other operator")

    spec = TestSpec(
        id="demo_dmm",
        label="Demo DMM",
        required_instruments=frozenset({"PSU", "DMM"}),
        fixture_mode="LOGIC",
        lab_sheet="Demo",
        run=lambda *_a, **_k: {},
    )
    steps = build_demo_steps([spec], {"vcc": 3.3})
    if not steps or "DMM" not in steps[0]["instruments"]:
        raise AssertionError("demo steps must list DMM")
    if steps[0]["mock"].get("dmm_v") is None:
        raise AssertionError("demo mock must include dmm_v")

    vol = TestSpec(
        id="vol",
        label="VOL",
        required_instruments=frozenset({"PSU", "DMM"}),
        fixture_mode="LOGIC",
        lab_sheet="VOL",
        run=lambda *_a, **_k: {},
    )
    vol_mock = build_demo_steps(
        [vol], {"vcc": 5.0, "vccb": 3.3, "current_limit_a": 0.05}
    )[0]["mock"]
    if float(vol_mock.get("dmm_v") or 9) >= 1.0:
        raise AssertionError(f"VOL demo mock must stay low, got {vol_mock}")
    if vol_mock.get("psu_ch2") != 3.3:
        raise AssertionError(f"dual-rail demo must mock PSU CH2=VCCB, got {vol_mock}")
    if vol_mock.get("current_limit_a") != 0.05:
        raise AssertionError(f"demo must carry current_limit_a, got {vol_mock}")

    iplus = TestSpec(
        id="iplus",
        label="I+",
        required_instruments=frozenset({"PSU", "DMM"}),
        fixture_mode="LIM_RS2323",
        lab_sheet="Iplus",
        run=lambda *_a, **_k: {},
    )
    i_mock = build_demo_steps([iplus], {"vcc": 5.0})[0]["mock"]
    if i_mock.get("i_ua") is None or i_mock.get("dmm_v") is not None:
        raise AssertionError(f"current demo must mock i_ua not dmm_v, got {i_mock}")

    from openpyxl import Workbook

    from ate.core.new_product import _maybe_merge_golden_style

    filled_xlsx = tmp / "filled_gbw.xlsx"
    fwb = Workbook()
    fws = fwb.active
    fws.title = "GBW"
    fws["C21"] = 7.0
    fwb.save(filled_xlsx)
    fwb.close()
    skip_g = _maybe_merge_golden_style({"workbook": str(filled_xlsx)})
    if skip_g.get("golden") is not False:
        raise AssertionError(f"filled GBW must skip golden merge, got {skip_g}")

    print(
        f"OK new-product: categories={len(cats)} inventory={len(inv)} "
        f"tmp={root.name} demo_instruments={steps[0]['instruments']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
