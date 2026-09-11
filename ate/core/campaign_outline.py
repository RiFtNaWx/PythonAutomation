"""RS622-shaped campaign sheet_map. One place for outline + known paste cells.

Do not invent photo cells. Do not write FILL_ME. Tracking-probed numbers only.
"""
from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from ate.core.paths import TEST_DB_ROOT
from ate.reporting.session_values import _fold_name

_FILL = frozenset({"FILL_ME", "STUB", "TODO", "TBD"})
_SKIP_SHEETS = frozenset({"Summary", "Checklist", "Mapping", "Status", "Problems"})
_NAMING = {
    "screenshot": "{TEST}_{DUT}_{VARIANT}_{TIMESTAMP}.jpg",
    "graph": "{TEST}_{DUT}_{VARIANT}_{TIMESTAMP}.png",
}
_FAM_MODE = {
    "opamp": "BUFFER",
    "logic": "LOGIC",
    "level": "LOGIC",
    "switch": "LIM_RS2323",
    "power": "LDO",
}
_KEY_MODE = {
    "gbw": "G11",
    "ort": "G_NEG100",
    "vos": "G1001",
    "vossweep": "G1001",
    "noise": "ATE",
    "psrr": "ATE",
    "cmrr": "ATE",
    "aol": "ATE",
    "emirr": "ATE",
    "iplus": "LIM_RS2323",
    "iq": "LDO",
}

# Probed on live tracking xlsx. Do not add corners that are not on the sheet.
_VOX_VOH = {"VOH_4p5V": ["G16", "H16", "I16"]}
_VOX_VOL = {"VOL_4p5V": ["G25", "H25", "I25"]}
_ICC_MAX = {"ICC_uA": "D10"}
_IPLUS_STUB = {"IPLUS_uA": "B2"}
_GBW_TTSOP = {
    "GBW_MHz": {"CHA": ["R20", "S20", "T20", "U20"], "CHB": ["AA20", "AB20", "AC20", "AD20"]},
    "F_3dB_kHz": {"CHA": ["R19", "S19", "T19", "U19"], "CHB": ["AA19", "AB19", "AC19", "AD19"]},
    "VOUT_1k_mV": {"CHA": ["R17", "S17", "T17", "U17"], "CHB": ["AA17", "AB17", "AC17", "AD17"]},
}
_GBW_SOP8 = {
    "GBW_MHz": {"CHA": ["C21", "D21", "E21"], "CHB": ["J21", "K21", "L21"]},
    "F_3dB_kHz": {"CHA": ["C20", "D20", "E20"], "CHB": ["J20", "K20", "L20"]},
    "VOUT_1k_mV": {"CHA": ["C18", "D18", "E18"], "CHB": ["J18", "K18", "L18"]},
}
_VOS_TTSOP = {
    "VOS_mV": {"CHA": ["R16", "S16", "T16", "U16"], "CHB": ["AA16", "AB16", "AC16", "AD16"]}
}
_VOS_SOP8 = {
    "VOS_mV": {"CHA": ["B16", "C16", "D16", "E16"], "CHB": ["I16", "J16", "K16", "L16"]}
}

# 8 photo boxes (4 DUT x CHA/CHB) from Eugene TTSOP8 golden_layout_report.json
# Do not invent cells. Live RS622 sheet_map already matches these rows.
_PHOTO_TTSOP = {
    "Slew Rate": {
        "u1_chA": "A70",
        "u1_chB": "E70",
        "u2_chA": "I70",
        "u2_chB": "M70",
        "u3_chA": "Q70",
        "u3_chB": "U70",
        "u4_chA": "Y70",
        "u4_chB": "AC70",
    },
    "GBW": {
        "u1_chA": "A45",
        "u1_chB": "E45",
        "u2_chA": "I45",
        "u2_chB": "M45",
        "u3_chA": "Q45",
        "u3_chB": "U45",
        "u4_chA": "Y45",
        "u4_chB": "AC45",
    },
    "VOS": {
        "u1_chA": "A39",
        "u1_chB": "E39",
        "u2_chA": "I39",
        "u2_chB": "M39",
        "u3_chA": "Q39",
        "u3_chB": "U39",
        "u4_chA": "Y39",
        "u4_chB": "AC39",
    },
    "NoPhaseReversal": {
        "u1_chA": "A41",
        "u1_chB": "E41",
        "u2_chA": "I41",
        "u2_chB": "M41",
        "u3_chA": "Q41",
        "u3_chB": "U41",
        "u4_chA": "Y41",
        "u4_chB": "AC41",
    },
    "PowerOnTime": {
        "u1_chA": "A59",
        "u1_chB": "E59",
        "u2_chA": "I59",
        "u2_chB": "M59",
        "u3_chA": "Q59",
        "u3_chB": "U59",
        "u4_chA": "Y59",
        "u4_chB": "AC59",
    },
    "VOL": {
        "u1_chA": "A42",
        "u1_chB": "E42",
        "u2_chA": "I42",
        "u2_chB": "M42",
        "u3_chA": "Q42",
        "u3_chB": "U42",
        "u4_chA": "Y42",
        "u4_chB": "AC42",
    },
}


def _merge_photos(entry: dict[str, Any], photos: dict[str, str]) -> None:
    paste = entry.setdefault("paste", {})
    if not isinstance(paste, dict):
        paste = {}
        entry["paste"] = paste
    cur = paste.get("photos")
    if not isinstance(cur, dict):
        cur = {}
        paste["photos"] = cur
    for key, cell in photos.items():
        if key not in cur:
            cur[key] = cell


def attach_known_photos(tests: dict[str, Any], sheets: list[str], *, ttsop: bool) -> None:
    """TTSOP8 8-box photo cells from the Eugene RS622 golden workbook.

    SOP8 C21 layout does not get these cells -- that would invent a grid.
    """
    if not ttsop:
        return
    sheet_set = {str(s) for s in sheets}
    for sheet, photos in _PHOTO_TTSOP.items():
        if sheet not in sheet_set:
            continue
        entry = _pick_entry(tests, sheet, _folder_key(sheet))
        if entry is None:
            continue
        _merge_photos(entry, photos)

TEST_OUTLINE = ("folder", "excel_sheet", "fixture_mode", "automated", "dut_iterations")


def _is_fill(raw: Any) -> bool:
    if isinstance(raw, str) and raw.split("#", 1)[0].strip().upper() in _FILL:
        return True
    if isinstance(raw, dict):
        return bool(raw) and all(_is_fill(v) for v in raw.values())
    if isinstance(raw, (list, tuple)):
        return bool(raw) and all(_is_fill(v) for v in raw)
    return False


def _folder_key(sheet: str) -> str:
    raw = re.sub(r"[^\w\-]+", "", (sheet or "").replace(" ", ""))
    return raw or "Sheet"


def _family_from_component(name: str) -> str:
    n = str(name or "").strip().lower().replace(" ", "")
    if n in ("opamp", "opa"):
        return "opamp"
    if n in ("analogswitch", "switch", "lim"):
        return "switch"
    if n == "power":
        return "power"
    if n == "level":
        return "level"
    if n == "logic":
        return "logic"
    return n


def _infer_mode(key: str, family: str) -> str:
    folds = _fold_name(key)
    for name, mode in _KEY_MODE.items():
        if name in folds:
            return mode
    return _FAM_MODE.get(family, "LOGIC")


def _cell_ok(ws: Any, coord: str) -> bool:
    try:
        from openpyxl.cell.cell import MergedCell

        return not isinstance(ws[coord], MergedCell)
    except Exception:
        return False


def _xlsx_from_map(path: Path, data: dict[str, Any]) -> Path | None:
    rel = ""
    wb = data.get("workbook")
    if isinstance(wb, dict):
        rel = str(wb.get("path") or "")
    if rel:
        cand = (path.parent / rel).resolve()
        if cand.is_file():
            return cand
    folder = path.parent.parent / "workbook"
    if folder.is_dir():
        hits = sorted(folder.glob("*.xlsx"))
        if hits:
            return hits[0]
    return None


def outline_test(
    *,
    folder: str,
    excel_sheet: str,
    fixture_mode: str,
    sample: int,
    automated: bool = True,
) -> dict[str, Any]:
    return {
        "folder": folder,
        "excel_sheet": excel_sheet,
        "fixture_mode": str(fixture_mode or "LOGIC"),
        "automated": bool(automated),
        "dut_iterations": max(1, int(sample or 4)),
    }


def campaign_header(
    *,
    component: str,
    part: str,
    package: str,
    version: str,
    sample_size: int,
    workbook_name: str,
    operator: str = "",
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "component": component,
        "part": part,
        "package": package,
        "version": version or "Version_1",
        "sample_size": max(1, int(sample_size or 4)),
        "workbook": {"path": f"../workbook/{workbook_name}"},
        "naming": dict(_NAMING),
        "tests": {},
    }
    if operator:
        out["operator"] = operator
    return out


def _clean_paste(entry: dict[str, Any]) -> None:
    paste = entry.get("paste")
    if paste is None:
        return
    if _is_fill(paste):
        entry.pop("paste", None)
        return
    if not isinstance(paste, dict):
        return
    cleaned = {k: v for k, v in paste.items() if not _is_fill(v)}
    if cleaned:
        entry["paste"] = cleaned
    else:
        entry.pop("paste", None)


def _merge_values(entry: dict[str, Any], values: dict[str, Any], excel_sheet: str | None = None) -> None:
    if excel_sheet:
        entry["excel_sheet"] = excel_sheet
    paste = entry.setdefault("paste", {})
    if not isinstance(paste, dict):
        paste = {}
        entry["paste"] = paste
    cur = paste.get("values")
    if not isinstance(cur, dict):
        cur = {}
        paste["values"] = cur
    for mid, cells in values.items():
        if mid not in cur:
            cur[mid] = cells


def _pick_entry(tests: dict[str, Any], *names: str) -> dict[str, Any] | None:
    want = set()
    for n in names:
        want |= _fold_name(n)
    for key, entry in tests.items():
        if not isinstance(entry, dict):
            continue
        have = _fold_name(key) | _fold_name(str(entry.get("folder") or "")) | _fold_name(
            str(entry.get("excel_sheet") or "")
        )
        if want & have:
            return entry
    return None


def attach_known_values(tests: dict[str, Any], sheets: list[str], xlsx: Path | None) -> None:
    sheet_set = {str(s) for s in sheets}
    if "VOX" in sheet_set:
        voh = _pick_entry(tests, "voh", "voh_load")
        vol = _pick_entry(tests, "vol", "vol_load")
        if voh is not None:
            _merge_values(voh, _VOX_VOH, "VOX")
        if vol is not None:
            _merge_values(vol, _VOX_VOL, "VOX")
    if "ICC" in sheet_set:
        icc = _pick_entry(tests, "supply_current", "supply_current_sweep", "icc")
        # RS0204 Icc is a condition grid -- only the Logic ICC sheet gets D10.
        if icc is not None and str(icc.get("excel_sheet") or "") != "Icc":
            _merge_values(icc, _ICC_MAX, "ICC")
    if "Iplus" in sheet_set:
        ip = _pick_entry(tests, "iplus")
        if ip is not None:
            _merge_values(ip, _IPLUS_STUB, "Iplus")
            if xlsx is not None and xlsx.is_file():
                _ensure_iplus_label(xlsx)
    if xlsx is None or not xlsx.is_file():
        return
    from openpyxl import load_workbook

    ttsop = False
    wb = load_workbook(xlsx, data_only=False)
    try:
        if "GBW" in sheet_set and "GBW" in wb.sheetnames:
            gbw = _pick_entry(tests, "gbw")
            if gbw is not None:
                ws = wb["GBW"]
                if _cell_ok(ws, "R20"):
                    ttsop = True
                    _merge_values(gbw, _GBW_TTSOP)
                elif _cell_ok(ws, "C21"):
                    _merge_values(gbw, _GBW_SOP8)
        if "VOS" in sheet_set and "VOS" in wb.sheetnames:
            vos = _pick_entry(tests, "vos", "vos_sweep")
            if vos is not None:
                ws = wb["VOS"]
                if _cell_ok(ws, "R16"):
                    ttsop = True
                    _merge_values(vos, _VOS_TTSOP)
                elif _cell_ok(ws, "B16"):
                    _merge_values(vos, _VOS_SOP8)
        if not ttsop and "GBW" in wb.sheetnames:
            ttsop = _cell_ok(wb["GBW"], "R20")
    finally:
        wb.close()
    attach_known_photos(tests, sheets, ttsop=ttsop)


def _ensure_iplus_label(xlsx: Path) -> None:
    from openpyxl import load_workbook

    wb = load_workbook(xlsx)
    try:
        if "Iplus" not in wb.sheetnames:
            return
        ws = wb["Iplus"]
        if not ws["A2"].value:
            ws["A2"] = "ATE IPLUS_uA"
            wb.save(xlsx)
    finally:
        wb.close()


def tests_from_sheets(sheets: list[str], *, family: str, sample: int) -> dict[str, Any]:
    tests: dict[str, Any] = {}
    used: set[str] = set()
    have = {str(s) for s in sheets}
    for name in sheets:
        if name in _SKIP_SHEETS:
            continue
        if name == "VOX":
            for key in ("VOH", "VOL"):
                if key in used:
                    continue
                used.add(key)
                tests[key] = outline_test(
                    folder=key,
                    excel_sheet="VOX",
                    fixture_mode=_infer_mode(key, family),
                    sample=sample,
                )
            continue
        if name in ("VOH", "VOL") and "VOX" in have:
            continue
        if name == "ICC":
            key = "Supply_Current"
            if key not in used:
                used.add(key)
                tests[key] = outline_test(
                    folder=key,
                    excel_sheet="ICC",
                    fixture_mode=_infer_mode(key, family),
                    sample=sample,
                )
            continue
        key = _folder_key(name)
        base = key
        n = 2
        while key in used:
            key = f"{base}{n}"
            n += 1
        used.add(key)
        tests[key] = outline_test(
            folder=key,
            excel_sheet=name,
            fixture_mode=_infer_mode(key, family),
            sample=sample,
            automated=True,
        )
    return tests


def outline_from_workbook(
    *,
    component: str,
    part: str,
    package: str,
    version: str,
    sample_size: int,
    workbook_name: str,
    sheets: list[str],
    family: str = "",
    operator: str = "",
    xlsx: Path | None = None,
) -> dict[str, Any]:
    fam = family or _family_from_component(component)
    data = campaign_header(
        component=component,
        part=part,
        package=package,
        version=version,
        sample_size=sample_size,
        workbook_name=workbook_name,
        operator=operator,
    )
    data["tests"] = tests_from_sheets(sheets, family=fam, sample=int(sample_size or 4))
    attach_known_values(data["tests"], sheets, xlsx)
    return data


def upgrade_sheet_map(
    data: dict[str, Any],
    *,
    family: str = "",
    sample: int = 4,
    sheets: list[str] | None = None,
    xlsx: Path | None = None,
) -> dict[str, Any]:
    out = deepcopy(data)
    fam = family or _family_from_component(str(out.get("component") or ""))
    out.setdefault("sample_size", max(1, int(sample or 4)))
    out.setdefault("naming", dict(_NAMING))
    if isinstance(out.get("naming"), dict):
        nam = dict(out["naming"])
        nam.setdefault("screenshot", _NAMING["screenshot"])
        nam.setdefault("graph", _NAMING["graph"])
        out["naming"] = nam
    tests = out.get("tests")
    if not isinstance(tests, dict) or not tests:
        if sheets:
            out["tests"] = tests_from_sheets(sheets, family=fam, sample=int(out["sample_size"]))
            tests = out["tests"]
        else:
            out["tests"] = {}
            tests = out["tests"]
    sample_n = int(out.get("sample_size") or sample or 4)
    for key, entry in list(tests.items()):
        if not isinstance(entry, dict):
            tests.pop(key, None)
            continue
        sheet = str(entry.get("excel_sheet") or "")
        folder = str(entry.get("folder") or key)
        if sheet in _SKIP_SHEETS or folder in _SKIP_SHEETS or key in _SKIP_SHEETS:
            tests.pop(key, None)
            continue
        entry.setdefault("folder", key)
        entry.setdefault("excel_sheet", str(entry.get("folder") or key))
        mode = str(entry.get("fixture_mode") or "")
        was_fill = (not mode) or mode.upper() in _FILL
        if was_fill:
            entry["fixture_mode"] = _infer_mode(str(entry.get("folder") or key), fam)
        if "automated" not in entry or was_fill:
            entry["automated"] = True
        entry.setdefault("dut_iterations", sample_n)
        _clean_paste(entry)
    attach_known_values(tests, list(sheets or []), xlsx)
    return out


def iter_campaign_maps(base: Path | None = None) -> list[Path]:
    root = Path(base) if base else TEST_DB_ROOT
    if not root.is_dir():
        return []
    out: list[Path] = []
    for p in root.rglob("sheet_map.yaml"):
        if p.parent.name != "_manifest":
            continue
        if any(part.startswith("_") and part not in {"_manifest"} for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def outline_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("component", "part", "package", "version", "sample_size", "tests"):
        if key not in data or data.get(key) in (None, ""):
            errors.append(f"missing {key}")
    nam = data.get("naming")
    if not isinstance(nam, dict) or not nam.get("screenshot") or not nam.get("graph"):
        errors.append("naming.screenshot/graph missing")
    wb = data.get("workbook")
    if not isinstance(wb, dict) or not wb.get("path"):
        errors.append("workbook.path missing")
    tests = data.get("tests")
    if not isinstance(tests, dict):
        errors.append("tests must be a map")
        return errors
    for key, entry in tests.items():
        if not isinstance(entry, dict):
            errors.append(f"{key}: not a map")
            continue
        for field in TEST_OUTLINE:
            if field not in entry or entry.get(field) in (None, ""):
                errors.append(f"{key}: missing {field}")
        mode = str(entry.get("fixture_mode") or "")
        if mode.upper() in _FILL:
            errors.append(f"{key}: fixture_mode FILL_ME")
        paste = entry.get("paste")
        if isinstance(paste, dict):
            vals = paste.get("values")
            if _is_fill(vals) or (isinstance(vals, dict) and any(_is_fill(v) for v in vals.values())):
                errors.append(f"{key}: paste.values still FILL_ME")
            if _is_fill(paste.get("photos")):
                errors.append(f"{key}: paste.photos FILL_ME (omit until measured)")
        elif _is_fill(paste):
            errors.append(f"{key}: paste FILL_ME")
    return errors


def apply_campaign_map(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raw = {}
    xlsx = _xlsx_from_map(path, raw)
    sheets: list[str] = []
    if xlsx is not None:
        from openpyxl import load_workbook

        try:
            wb = load_workbook(xlsx, read_only=True)
            try:
                sheets = list(wb.sheetnames)
            finally:
                wb.close()
        except Exception:
            sheets = []
            xlsx = None
    try:
        fam = _family_from_component(str(raw.get("component") or path.parents[5].name))
    except IndexError:
        fam = _family_from_component(str(raw.get("component") or ""))
    sample = int(raw.get("sample_size") or 4)
    upgraded = upgrade_sheet_map(raw, family=fam, sample=sample, sheets=sheets, xlsx=xlsx)
    if upgraded == raw:
        return {"path": str(path), "wrote": False}
    path.write_text(yaml.safe_dump(upgraded, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {"path": str(path), "wrote": True}


def apply_all(base: Path | None = None) -> dict[str, Any]:
    wrote = 0
    kept = 0
    for p in iter_campaign_maps(base):
        row = apply_campaign_map(p)
        if row.get("wrote"):
            wrote += 1
        else:
            kept += 1
    return {"ok": True, "wrote": wrote, "kept": kept, "count": wrote + kept}


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if "--apply" in args:
        res = apply_all()
        print(f"OK campaign_outline apply wrote={res['wrote']} kept={res['kept']} count={res['count']}")
        return 0
    from ate.core.check_campaign_outline import main as check_main

    return check_main()


if __name__ == "__main__":
    raise SystemExit(main())
