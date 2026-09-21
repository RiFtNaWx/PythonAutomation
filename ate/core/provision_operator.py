"""Provision an operator across inventory SKUs + clean golden workbooks.

Replicable. Logs to #Test_Database/_ate/provision_log.json + .xlsx (sorted).

  python -m ate.core.provision_operator JianHong
  python -m ate.core.provision_operator JianHong --dry-run
  python -m ate.core.check_provision_operator
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from ate.core.paths import TEST_DB_ROOT

MYT = timezone(timedelta(hours=8))
_HEADER_FILL = "1F4E79"
_HEADER_FONT = "FFFFFF"


def unique_inventory_skus() -> list[dict[str, Any]]:
    """One row per part+package from inventory.yaml. No scrape."""
    from ate.core.new_product import load_inventory, part_key_for

    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in load_inventory():
        part = str(row.get("part") or "").strip().upper()
        package = str(row.get("package") or "").strip() or "SOT23"
        if not part:
            continue
        key = (part, package)
        if key in seen:
            continue
        seen.add(key)
        cat = str(row.get("category") or "opamp").strip() or "opamp"
        out.append(
            {
                "part": part,
                "package": package,
                "model": str(row.get("model") or part).strip(),
                "category": cat,
                "part_key": part_key_for(part),
                "sheet_class": str(row.get("sheet_class") or ""),
            }
        )
    out.sort(key=lambda r: (r["category"], r["part"], r["package"]))
    return out


def _load_sheet_map(root: Path) -> dict[str, Any]:
    path = root / "_manifest" / "sheet_map.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _under_live_db(root: Path) -> bool:
    try:
        root.resolve().relative_to(Path(TEST_DB_ROOT).resolve())
        return True
    except ValueError:
        return False


def _write_sheet_map_from_xlsx(
    root: Path,
    dest: Path,
    *,
    part: str,
    package: str,
    operator: str,
) -> list[str]:
    """Probe this xlsx into sheet_map.yaml. Cells come from the book, not A91."""
    from openpyxl import load_workbook

    from ate.core.campaign_outline import outline_from_workbook

    wb = load_workbook(dest, read_only=True, data_only=False)
    try:
        sheets = list(wb.sheetnames)
    finally:
        wb.close()
    parts = root.parts
    component = str(parts[-5]) if len(parts) >= 5 else "Logic"
    version = root.name if str(root.name).lower().startswith("version") else "Version_1"
    data = outline_from_workbook(
        component=component,
        part=part,
        package=package,
        version=version,
        sample_size=4,
        workbook_name=dest.name,
        sheets=sheets,
        operator=operator,
        xlsx=dest,
    )
    man = root / "_manifest"
    man.mkdir(parents=True, exist_ok=True)
    header = (
        "# Campaign outline. Paste cells probed from this workbook.\n"
        "# Do not write FILL_ME. Do not apply OpAmp layout_rules on Logic VIX/VOX.\n"
    )
    (man / "sheet_map.yaml").write_text(
        header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return sheets


def _campaign_component(root: Path) -> str:
    try:
        return str(root.parts[-5])
    except Exception:
        return "Logic"


def _enabled_param_plan(
    part: str, package: str, *, component: str = ""
) -> list[tuple[str, str, tuple[str, ...]]]:
    from ate.core.campaign_outline import _TEST_DUT_MIDS
    from ate.core.new_product import part_key_for, suite_for_part, _test_track_rows

    pk = part_key_for(part)
    fam = suite_for_part(part, component=component, package=package)
    out: list[tuple[str, str, tuple[str, ...]]] = []
    seen: set[str] = set()
    for tid, folder in _test_track_rows(pk, fam):
        name = str(folder or tid).strip()[:31]
        if not name or name in seen:
            continue
        seen.add(name)
        out.append((tid, name, _TEST_DUT_MIDS.get(tid, ())))
    return out


def _fill_param_sheet(ws, n: int, mids: tuple[str, ...] = ()) -> None:
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    headers = ["Parameter", "Unit", "Min", "Max", "Typ"] + [
        f"DUT_{i}" for i in range(1, n + 1)
    ] + ["Result"]
    for col, h in enumerate(headers, 1):
        ws.cell(1, col).value = h
    _style_header(ws, 1, len(headers))
    if mids:
        for i, mid in enumerate(mids):
            ws.cell(2 + i, 1).value = mid
    else:
        ws["A2"] = "(empty -- run START to fill)"
        ws["A2"].font = Font(italic=True, color="666666")
    ws.row_dimensions[1].height = 22
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 12
    ws.column_dimensions["A"].width = 22


def _write_tracked_sheet_map(
    root: Path,
    dest: Path,
    *,
    part: str,
    package: str,
    operator: str,
    sample_size: int,
) -> list[str]:
    from ate.core.campaign_outline import apply_campaign_map
    from ate.core.new_product import part_key_for, suite_for_part, _tracked_sheet_map

    component = _campaign_component(root)
    pk = part_key_for(part)
    fam = suite_for_part(part, component=component, package=package)
    cat = {"component": component}
    text = _tracked_sheet_map(
        cat, part, package, operator, pk, fam, int(sample_size or 4)
    )
    man = root / "_manifest"
    man.mkdir(parents=True, exist_ok=True)
    header = (
        "# Campaign outline. Paste cells probed from this workbook.\n"
        "# Do not write FILL_ME. Do not apply OpAmp layout_rules on Logic VIX/VOX.\n"
    )
    path = man / "sheet_map.yaml"
    path.write_text(header + text, encoding="utf-8")
    apply_campaign_map(path, xlsx=dest)
    return list(_load_sheet_map(root).get("tests") or {})


def _fold_sheet(name: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "", str(name or "").lower())


# Golden tab names that already cover a TestSpec lab_sheet (do not add a second Parameter tab).
_SHEET_ALIAS: dict[str, tuple[str, ...]] = {
    "tp": ("tp", "tpd"),
    "tpd": ("tp", "tpd"),
    "vihvil": ("vihvil", "vix", "vihl"),
    "voh": ("voh", "vox"),
    "vol": ("vol", "vox"),
    "idd": ("idd", "icc", "supplycurrent"),
    "supplycurrent": ("supplycurrent", "idd", "icc"),
    "supplycurrentsweep": ("supplycurrentsweep", "icc", "idd"),
    "ioffleakage": ("ioffleakage", "ioff"),
    "cin": ("cin",),
    "cpd": ("cpd",),
}


def _sheet_present(name: str, have_folded: set[str]) -> bool:
    n = _fold_sheet(name)
    if n in have_folded or n in ("summary", "sweep", "checklist", "setup"):
        return True
    return any(alt in have_folded for alt in _SHEET_ALIAS.get(n, ()))


def _sync_stub_param_sheets(
    dest: Path,
    *,
    root: Path,
    part: str,
    package: str,
    sample_size: int,
) -> list[str]:
    from openpyxl import load_workbook

    n = max(1, int(sample_size or 4))
    plan = _enabled_param_plan(part, package, component=_campaign_component(root))
    wb = load_workbook(dest)
    added: list[str] = []
    try:
        have = set(wb.sheetnames)
        have_folded = {_fold_sheet(s) for s in have}
        for _tid, name, mids in plan:
            if _sheet_present(name, have_folded):
                continue
            ws = wb.create_sheet(title=name)
            _fill_param_sheet(ws, n, mids)
            added.append(name)
            have.add(name)
            have_folded.add(_fold_sheet(name))
        if added:
            wb.save(dest)
    finally:
        wb.close()
    return added


def _style_header(ws, row: int, cols: int) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    fill = PatternFill("solid", fgColor=_HEADER_FILL)
    font = Font(name="Calibri", bold=True, color=_HEADER_FONT, size=11)
    align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for c in range(1, cols + 1):
        cell = ws.cell(row, c)
        cell.fill = fill
        cell.font = font
        cell.alignment = align


def create_clean_golden_workbook(
    root: Path,
    *,
    part: str,
    package: str,
    operator: str,
    sample_size: int = 4,
    force: bool = False,
) -> dict[str, Any]:
    """Copy the per-SKU golden ref when one exists. Stub Parameter table only if none."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    from ate.core.golden_refs import is_stub_workbook, resolve_golden

    wb_dir = root / "workbook"
    wb_dir.mkdir(parents=True, exist_ok=True)
    dest = wb_dir / f"{part}_Lab_Report.xlsx"
    if not dest.is_file():
        alts = [
            p
            for p in wb_dir.glob(f"{part}_Lab_Report*.xlsx")
            if p.is_file()
            and "_filled" not in p.name.lower()
            and not p.name.startswith("~$")
        ]
        if alts:
            dest = sorted(alts, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    ref = resolve_golden(part, package) if _under_live_db(root) else None
    dest_exists = dest.is_file()
    dest_stub = bool(dest_exists and is_stub_workbook(dest))
    if dest_exists and not dest_stub:
        # Never replace a senior lab book (Ariff / ChangThong / real report).
        return {
            "ok": True,
            "path": str(dest),
            "action": "exists",
            "sheets": [],
        }
    if dest_exists and dest_stub:
        # Keep the Parameter stub. Do not copy2 a golden over it.
        n = max(1, int(sample_size or 4))
        added = _sync_stub_param_sheets(
            dest, root=root, part=part, package=package, sample_size=n
        )
        sheets = _write_tracked_sheet_map(
            root,
            dest,
            part=part,
            package=package,
            operator=operator,
            sample_size=n,
        )
        return {
            "ok": True,
            "path": str(dest),
            "action": "updated" if added else "exists",
            "sheets": added or sheets,
        }
    if ref is not None and ref.is_file():
        import shutil

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(ref, dest)
        except PermissionError:
            tmp = Path(dest.parent / f".{dest.name}.tmp")
            shutil.copy2(ref, tmp)
            tmp.replace(dest)
        sheets = _write_sheet_map_from_xlsx(
            root, dest, part=part, package=package, operator=operator
        )
        if is_stub_workbook(dest):
            n = max(1, int(sample_size or 4))
            added = _sync_stub_param_sheets(
                dest, root=root, part=part, package=package, sample_size=n
            )
            from ate.core.campaign_outline import apply_campaign_map

            man = root / "_manifest" / "sheet_map.yaml"
            if man.is_file():
                apply_campaign_map(man, xlsx=dest)
            if added:
                sheets = list(sheets) + added
        return {
            "ok": True,
            "path": str(dest),
            "action": "copied_ref",
            "sheets": sheets,
            "golden": str(ref),
        }

    sm = _load_sheet_map(root)
    tests = sm.get("tests") if isinstance(sm.get("tests"), dict) else {}
    sheet_names: list[str] = []
    seen: set[str] = set()
    for tid, entry in tests.items():
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("excel_sheet") or entry.get("folder") or tid).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        sheet_names.append(name)
    if not sheet_names:
        plan = _enabled_param_plan(
            part, package, component=_campaign_component(root)
        )
        sheet_names = [name for _tid, name, _mids in plan]
    if not sheet_names:
        sheet_names = ["Setup"]

    n = max(1, int(sample_size or 4))
    plan_mids = {
        name: mids
        for _tid, name, mids in _enabled_param_plan(
            part, package, component=_campaign_component(root)
        )
    }
    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    summary["A1"] = "Device"
    summary["B1"] = part
    summary["A2"] = "Package"
    summary["B2"] = package
    summary["A3"] = "Operator"
    summary["B3"] = operator
    summary["A4"] = "Sample Size"
    summary["B4"] = n
    summary["A5"] = "Version"
    summary["B5"] = "Version_1"
    summary["A6"] = "Tags"
    summary["B6"] = ""
    summary["A8"] = "Note"
    summary["B8"] = "Clean golden template -- no measured values. Fill via START / Fill Excel."
    for r in range(1, 7):
        summary.cell(r, 1).font = Font(bold=True)
    summary.column_dimensions["A"].width = 16
    summary.column_dimensions["B"].width = 36

    created_sheets: list[str] = ["Summary"]
    for name in sheet_names:
        ws = wb.create_sheet(title=name[:31])
        _fill_param_sheet(ws, n, plan_mids.get(name, ()))
        created_sheets.append(name)

    sweep = wb.create_sheet("Sweep")
    sweep_headers = ["test_id", "dut", "channel", "VCC", "freq_hz", "AWG", "value", "unit", "result"]
    for col, h in enumerate(sweep_headers, 1):
        sweep.cell(1, col).value = h
    _style_header(sweep, 1, len(sweep_headers))
    sweep["A2"] = "(sorted sweep rows land here after Fill Excel / DEMO)"
    sweep["A2"].font = Font(italic=True, color="666666")
    sweep.freeze_panes = "A2"
    sweep.auto_filter.ref = f"A1:{get_column_letter(len(sweep_headers))}1"
    for col in range(1, len(sweep_headers) + 1):
        sweep.column_dimensions[get_column_letter(col)].width = 12
    created_sheets.append("Sweep")

    checklist = wb.create_sheet("Checklist")
    checklist["A1"] = "Item"
    checklist["B1"] = "Status"
    _style_header(checklist, 1, 2)
    for i, item in enumerate(
        (
            "Board selected (Setup)",
            "Open Session / DEMO",
            "START walk Continue",
            "Fill Excel numbers",
            "STS datalog PDF",
        ),
        2,
    ):
        checklist.cell(i, 1).value = item
        checklist.cell(i, 2).value = ""
    checklist.column_dimensions["A"].width = 28
    checklist.column_dimensions["B"].width = 14
    created_sheets.append("Checklist")

    dest.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dest)
    wb.close()
    _write_tracked_sheet_map(
        root,
        dest,
        part=part,
        package=package,
        operator=operator,
        sample_size=n,
    )
    # Clean stub only -- no measured values. OpAmp photo-box golden is separate
    # (apply_golden_workbook) once real ORT sheets exist.
    return {
        "ok": True,
        "path": str(dest),
        "action": "created",
        "sheets": created_sheets,
    }


def _write_provision_log(rows: list[dict[str, Any]], *, operator: str) -> dict[str, str]:
    """Sorted clear log: JSON + pretty Excel under #Test_Database/_ate."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    ate = Path(TEST_DB_ROOT) / "_ate"
    ate.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    payload = {
        "operator": operator,
        "generated": datetime.now(MYT).isoformat(timespec="seconds"),
        "count": len(rows),
        "rows": rows,
    }
    jpath = ate / f"provision_{operator}_{stamp}.json"
    jpath.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    latest = ate / f"provision_{operator}_latest.json"
    latest.write_text(jpath.read_text(encoding="utf-8"), encoding="utf-8")

    xlsx = ate / f"provision_{operator}_latest.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Provision"
    headers = [
        "category",
        "part",
        "package",
        "model",
        "root",
        "workbook",
        "workbook_action",
        "sheets",
        "ok",
        "error",
    ]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(1, col, h)
        cell.font = Font(bold=True, color="FFFFFF")
    from openpyxl.styles import PatternFill

    fill = PatternFill("solid", fgColor=_HEADER_FILL)
    for col in range(1, len(headers) + 1):
        ws.cell(1, col).fill = fill
    sorted_rows = sorted(
        rows,
        key=lambda r: (
            str(r.get("category") or ""),
            str(r.get("part") or ""),
            str(r.get("package") or ""),
        ),
    )
    for i, row in enumerate(sorted_rows, 2):
        ws.cell(i, 1).value = row.get("category")
        ws.cell(i, 2).value = row.get("part")
        ws.cell(i, 3).value = row.get("package")
        ws.cell(i, 4).value = row.get("model")
        ws.cell(i, 5).value = row.get("root")
        ws.cell(i, 6).value = row.get("workbook")
        ws.cell(i, 7).value = row.get("workbook_action")
        sheets = row.get("sheets") or []
        ws.cell(i, 8).value = ", ".join(sheets) if isinstance(sheets, list) else str(sheets)
        ws.cell(i, 9).value = "yes" if row.get("ok") else "no"
        ws.cell(i, 10).value = row.get("error") or ""
    from openpyxl.utils import get_column_letter

    for col, width in enumerate((12, 12, 18, 18, 48, 48, 14, 28, 6, 40), 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    last = max(2, len(sorted_rows) + 1)
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{last}"
    ws.freeze_panes = "A2"
    wb.save(xlsx)
    wb.close()
    return {"json": str(jpath), "latest_json": str(latest), "xlsx": str(xlsx)}


def provision_operator(
    label: str,
    *,
    with_workbook: bool = True,
    force_workbook: bool = False,
    dry_run: bool = False,
    base: Optional[Path] = None,
    sample_size: int = 4,
    only_parts: Optional[list[str]] = None,
    only_skus: Optional[list] = None,
    all_skus: bool = False,
) -> dict[str, Any]:
    """Assign ticked SKUs to this person. all_skus=True is the explicit dump."""
    from ate.core.database import load_owners, replace_owner_parts, require_write_operator
    from ate.core.new_product import ensure_product

    name = require_write_operator(label)
    skus = unique_inventory_skus()
    sku_keys: set[tuple[str, str]] = set()
    for row in only_skus or []:
        if not isinstance(row, dict):
            continue
        p = str(row.get("part") or "").strip().upper()
        pkg = str(row.get("package") or "").strip()
        if p:
            sku_keys.add((p, pkg))
    want = {str(p or "").strip().lower() for p in (only_parts or []) if str(p or "").strip()}
    if not sku_keys and not want and not all_skus:
        raise ValueError(
            "Tick one product, or pass all_skus=True. Will not dump every tracking SKU onto this person."
        )
    if sku_keys:
        skus = [
            s
            for s in skus
            if (str(s.get("part") or ""), str(s.get("package") or "")) in sku_keys
        ]
        if not skus:
            raise ValueError("no matching tracking SKUs (inventory.yaml only -- no scrape)")
    elif want:
        skus = [
            s
            for s in skus
            if str(s.get("part_key") or "").lower() in want
            or str(s.get("part") or "").lower() in want
        ]
        if not skus:
            raise ValueError("no matching tracking SKUs (inventory.yaml only -- no scrape)")
    rows: list[dict[str, Any]] = []
    part_keys: list[str] = []
    if dry_run:
        for sku in skus:
            rows.append(
                {
                    **sku,
                    "ok": True,
                    "root": "(dry-run)",
                    "workbook": "",
                    "workbook_action": "dry-run",
                    "sheets": [],
                }
            )
            part_keys.append(sku["part_key"])
        logs = _write_provision_log(rows, operator=name) if base is None else {}
        return {
            "operator": name,
            "dry_run": True,
            "count": len(rows),
            "rows": rows,
            "logs": logs,
        }

    for sku in skus:
        err = ""
        root = ""
        wb_path = ""
        wb_action = ""
        sheets: list[str] = []
        ok = True
        try:
            out = ensure_product(
                category_id=str(sku["category"]),
                part=str(sku["part"]),
                package=str(sku["package"]),
                model=str(sku.get("model") or ""),
                sample_size=int(sample_size or 4),
                operator=name,
                open_folder=False,
                apply=False,
                base=base,
            )
            root = str(out.get("root") or "")
            part_keys.append(str(sku["part_key"]))
            if with_workbook and root:
                wb = create_clean_golden_workbook(
                    Path(root),
                    part=str(sku["part"]),
                    package=str(sku["package"]),
                    operator=name,
                    sample_size=int(sample_size or 4),
                    force=force_workbook,
                )
                wb_path = str(wb.get("path") or "")
                wb_action = str(wb.get("action") or "")
                sheets = list(wb.get("sheets") or [])
        except Exception as exc:
            ok = False
            err = str(exc)
        rows.append(
            {
                **sku,
                "ok": ok,
                "root": root,
                "workbook": wb_path,
                "workbook_action": wb_action,
                "sheets": sheets,
                "error": err,
            }
        )

    # Dedupe part_keys preserving order
    seen_pk: set[str] = set()
    clean_keys: list[str] = []
    for pk in part_keys:
        if pk in seen_pk:
            continue
        seen_pk.add(pk)
        clean_keys.append(pk)
    if base is None:
        first = next((r for r in rows if r.get("ok")), None)
        parts_out = list(clean_keys)
        if want or sku_keys:
            found = next(
                (
                    o
                    for o in load_owners()
                    if str(o.get("label") or "").lower() == name.lower()
                ),
                None,
            )
            merged: list[str] = []
            seen_m: set[str] = set()
            for k in list((found or {}).get("parts") or []) + clean_keys:
                kk = str(k or "").strip().lower()
                if not kk or kk in seen_m:
                    continue
                seen_m.add(kk)
                merged.append(kk)
            parts_out = merged
        replace_owner_parts(
            label=name,
            parts=parts_out,
            default_family=str((first or {}).get("category") or "opamp"),
            default_part=str((first or {}).get("part_key") or ""),
            default_component="",
            default_package=str((first or {}).get("package") or ""),
            task=str((first or {}).get("part") or ""),
        )
    logs = _write_provision_log(rows, operator=name) if base is None else {}
    failed = [r for r in rows if not r.get("ok")]
    return {
        "operator": name,
        "dry_run": False,
        "count": len(rows),
        "ok_count": len(rows) - len(failed),
        "fail_count": len(failed),
        "parts": parts_out if base is None else clean_keys,
        "rows": rows,
        "logs": logs,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operator", help="Operator folder label (e.g. JianHong)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-workbook", action="store_true")
    p.add_argument("--force-workbook", action="store_true")
    p.add_argument("--sample-size", type=int, default=4)
    p.add_argument(
        "--all",
        action="store_true",
        help="every inventory.yaml SKU (explicit; default refuses the dump)",
    )
    p.add_argument("--parts", nargs="*", default=[], help="part keys only (rs1g07 ...)")
    args = p.parse_args(argv)
    res = provision_operator(
        args.operator,
        with_workbook=not args.no_workbook,
        force_workbook=bool(args.force_workbook),
        dry_run=bool(args.dry_run),
        sample_size=int(args.sample_size or 4),
        only_parts=list(args.parts) if args.parts else None,
        all_skus=bool(args.all),
    )
    print(
        f"OK provision {res['operator']}: skus={res['count']} "
        f"ok={res.get('ok_count', res['count'])} fail={res.get('fail_count', 0)} "
        f"dry_run={res.get('dry_run')}"
    )
    logs = res.get("logs") or {}
    if logs.get("xlsx"):
        print(f"  log xlsx: {logs['xlsx']}")
    if logs.get("latest_json"):
        print(f"  log json: {logs['latest_json']}")
    return 0 if not res.get("fail_count") else 1


if __name__ == "__main__":
    raise SystemExit(main())
