"""Copy an existing lab xlsx into a campaign workbook/ and outline sheet_map.

Known numeric cells come from ate.core.campaign_outline (RS622-shaped).
Do not write FILL_ME. Do not invent photo cells. A map that already has
real paste.values is upgraded in place, not replaced.
"""
from __future__ import annotations

import re
import shutil
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

MYT = timezone(timedelta(hours=8))
_CELL_RE = re.compile(r"^[A-Z]{1,3}\d{1,5}$")
_FILL_TOKENS = {"FILL_ME", "STUB", "TODO", "TBD", ""}


def _is_real_cell(value: Any) -> bool:
    if isinstance(value, str):
        token = value.split("#", 1)[0].strip()
        if token.upper() in _FILL_TOKENS:
            return False
        return bool(_CELL_RE.match(token))
    if isinstance(value, (list, tuple)):
        return any(_is_real_cell(v) for v in value)
    if isinstance(value, dict):
        return any(_is_real_cell(v) for v in value.values())
    return False


def sheet_map_has_paste_anchors(data: dict[str, Any]) -> bool:
    tests = data.get("tests")
    if not isinstance(tests, dict) or not tests:
        return False
    for entry in tests.values():
        if not isinstance(entry, dict):
            continue
        paste = entry.get("paste")
        if _is_real_cell(paste):
            return True
    return False


def _backup(path: Path) -> Optional[Path]:
    if not path.is_file():
        return None
    ts = datetime.now(MYT).strftime("%Y%m%d_%H%M%S")
    dest = path.with_name(f"{path.stem}.bak_{ts}{path.suffix}")
    shutil.copy2(path, dest)
    return dest


def _sheet_names(xlsx: Path) -> list[str]:
    from openpyxl import load_workbook

    wb = load_workbook(xlsx, read_only=True, data_only=False)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def _pick_xlsx_dialog() -> str:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    path = filedialog.askopenfilename(
        title="Select existing lab workbook (.xlsx)",
        filetypes=[("Excel workbook", "*.xlsx"), ("All files", "*.*")],
    )
    root.destroy()
    return str(path or "")


def _outline_sheet_map(ctx, dest_name: str, sheets: list[str], xlsx: Path) -> dict[str, Any]:
    from ate.core.campaign_outline import campaign_header, upgrade_sheet_map
    from ate.core.database import family_for_component

    existing = ctx.load_sheet_map() if hasattr(ctx, "load_sheet_map") else {}
    if not isinstance(existing, dict) or not existing:
        existing = campaign_header(
            component=ctx.component,
            part=ctx.part,
            package=ctx.package,
            version=ctx.version,
            sample_size=int(ctx.sample_size or 4),
            workbook_name=dest_name,
            operator=str(getattr(ctx, "operator", "") or ""),
        )
    else:
        existing = deepcopy(existing)
    existing["workbook"] = {"path": f"../workbook/{dest_name}"}
    existing.setdefault("component", ctx.component)
    existing.setdefault("part", ctx.part)
    existing.setdefault("package", ctx.package)
    existing.setdefault("version", ctx.version)
    fam = family_for_component(ctx.component)
    return upgrade_sheet_map(
        existing,
        family=fam,
        sample=int(ctx.sample_size or 4),
        sheets=sheets,
        xlsx=xlsx,
    )


def _write_outline_yaml(path: Path, data: dict[str, Any]) -> None:
    header = (
        "# Campaign outline (RS622 keys). Known paste.values live in campaign_outline.py.\n"
        "# Omit paste.photos until measured. Do not write FILL_ME.\n"
    )
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + body, encoding="utf-8")


def import_workbook(
    *,
    source_path: str = "",
    dest_name: str = "",
    pick: bool = False,
) -> dict[str, Any]:
    """Copy xlsx into the active campaign workbook/ and stub sheet_map if needed."""
    from ate.core.database import get_context

    src_str = str(source_path or "").strip()
    if pick or not src_str:
        src_str = _pick_xlsx_dialog()
    if not src_str:
        raise ValueError("No workbook selected")

    src = Path(src_str).expanduser()
    if not src.is_file():
        raise FileNotFoundError(f"Workbook not found: {src}")
    if src.suffix.lower() != ".xlsx":
        raise ValueError("Only .xlsx workbooks can be imported")

    name = Path(dest_name).name if dest_name else src.name
    if not name.lower().endswith(".xlsx"):
        name = f"{name}.xlsx"
    if not name or name.startswith("."):
        raise ValueError("Invalid destination workbook name")

    ctx = get_context()
    ctx.ensure_tree()
    wb_dir = ctx.workbook_dir()
    wb_dir.mkdir(parents=True, exist_ok=True)
    dest = wb_dir / name

    xlsx_backup = None
    copied = True
    if dest.resolve() == src.resolve():
        copied = False
    else:
        if dest.is_file():
            xlsx_backup = _backup(dest)
        shutil.copy2(src, dest)

    sheets = _sheet_names(dest)
    sm_path = ctx.sheet_map_path()
    existing = ctx.load_sheet_map()
    map_backup = None
    outlined = _outline_sheet_map(ctx, name, sheets, dest)
    if existing and existing == outlined:
        action = "left_intact"
        note = "Existing sheet_map already matches campaign outline."
    else:
        if existing:
            map_backup = _backup(sm_path)
        _write_outline_yaml(sm_path, outlined)
        action = "outlined"
        note = (
            "sheet_map upgraded to RS622 outline. Known numeric cells attached; "
            "photos omitted until measured."
        )

    created = ctx.ensure_tree()
    return {
        "ok": True,
        "source": str(src),
        "workbook": str(dest),
        "copied": copied,
        "xlsx_backup": str(xlsx_backup) if xlsx_backup else None,
        "sheet_map": str(sm_path),
        "sheet_map_action": action,
        "sheet_map_backup": str(map_backup) if map_backup else None,
        "sheets": sheets,
        "note": note,
        "context": ctx.identity(),
        "created": created,
    }
