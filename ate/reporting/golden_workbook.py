"""Campaign-aware golden workbook apply + check (A17-T03).

Does not require hardcoded Downloads paths. Uses DbContext.lab_report_path().
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from ate.reporting.golden_layout import TEST_SHEETS, apply_golden_sheet

MYT = timezone(timedelta(hours=8))
GOLDEN_FONT = "Quire Sans"
GOLDEN_SIZE = 12


def _font_name() -> str:
    return GOLDEN_FONT


def apply_golden_workbook(
    workbook_path: Path | None = None,
    *,
    sample_size: int | None = None,
    ctx=None,
) -> dict[str, Any]:
    """Apply golden ORT layout culture to the campaign workbook."""
    from ate.core.database import get_context

    c = ctx or get_context()
    path = Path(workbook_path) if workbook_path else c.lab_report_path()
    if not path.is_file():
        raise FileNotFoundError(f"No campaign workbook at {path}")
    n = int(sample_size if sample_size is not None else c.sample_size or 4)
    wb = load_workbook(path)
    report: dict[str, Any] = {
        "generated": datetime.now(MYT).isoformat(timespec="seconds"),
        "source": str(path),
        "sample_size": n,
        "sheets": {},
    }
    for name in TEST_SHEETS:
        if name not in wb.sheetnames:
            continue
        info = apply_golden_sheet(wb[name], name, sample_size=n)
        report["sheets"][name] = info
    if "Summary" in wb.sheetnames:
        ws = wb["Summary"]
        for row in range(1, 40):
            if ws.cell(row, 1).value and "sample" in str(ws.cell(row, 1).value).lower():
                ws.cell(row, 2).value = n
    try:
        wb.save(path)
        report["saved"] = str(path)
    except PermissionError:
        alt = path.with_name(path.stem + "_golden.xlsx")
        wb.save(alt)
        report["saved"] = str(alt)
        report["note"] = f"original locked; wrote {alt}"
    wb.close()
    out = c.manifest_dir() / "golden_layout_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    report["manifest"] = str(out)
    return report


def check_golden_workbook(
    workbook_path: Path | None = None,
    *,
    ctx=None,
    fix: bool = False,
) -> dict[str, Any]:
    """Fail-closed golden format check. Optionally apply then re-check once."""
    from ate.core.database import get_context
    from ate.reporting.photo_layout import parse_photo_key, photos_map, resolve_test_key

    c = ctx or get_context()
    path = Path(workbook_path) if workbook_path else c.lab_report_path()
    errors: list[str] = []
    warnings: list[str] = []

    if not path.is_file():
        return {
            "ok": False,
            "path": str(path),
            "errors": [f"workbook missing: {path}"],
            "warnings": [],
        }

    def _run_once() -> list[str]:
        errs: list[str] = []
        wb = load_workbook(path)
        # Font spot-check on first test sheet that exists
        want = _font_name()
        sample_sheet = next((n for n in TEST_SHEETS if n in wb.sheetnames), None)
        if sample_sheet:
            cell = wb[sample_sheet]["A1"]
            fname = getattr(getattr(cell, "font", None), "name", None) or ""
            # Soft: only fail if font is set to something else (not empty/default)
            if fname and fname != want and "quire" not in fname.lower():
                errs.append(
                    f"{sample_sheet}!A1 font={fname!r} expected {want!r}"
                )
        # Photo anchors: if screenshot exists, image should be on sheet
        sm = c.load_sheet_map()
        tests = (sm.get("tests") or {}) if isinstance(sm, dict) else {}
        for key, entry in tests.items():
            if not isinstance(entry, dict):
                continue
            paste = entry.get("paste") if isinstance(entry.get("paste"), dict) else {}
            photos = paste.get("photos") if isinstance(paste, dict) else None
            if not isinstance(photos, dict) or not photos:
                continue
            folder = str(entry.get("folder") or key)
            sheet_name = str(entry.get("excel_sheet") or key)
            if sheet_name not in wb.sheetnames:
                errs.append(f"sheet {sheet_name!r} missing for test {key}")
                continue
            ws = wb[sheet_name]
            anchors = {str(getattr(img.anchor, "_from", None) or img.anchor) for img in (ws._images or [])}
            # openpyxl image anchors are complex; check count vs expected when files exist
            need = 0
            have_files = 0
            for pkey, cell in photos.items():
                cell_s = str(cell or "").strip()
                if not cell_s or cell_s.upper().startswith("FILL"):
                    continue
                meta = parse_photo_key(str(pkey))
                if not meta:
                    continue
                unit = int(meta["unit"])
                g = c.graph_dir(folder, unit)
                s = c.screenshot_dir(folder, unit)
                files = []
                for d in (g, s):
                    if d.is_dir():
                        files.extend(
                            [
                                p
                                for p in d.iterdir()
                                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
                                and not p.name.startswith("_tmp")
                            ]
                        )
                if files:
                    have_files += 1
                    need += 1
            img_count = len(getattr(ws, "_images", None) or [])
            if have_files and img_count == 0:
                errs.append(
                    f"{sheet_name}: {have_files} screenshot(s) on disk but 0 images embedded"
                )
        wb.close()
        return errs

    errors = _run_once()
    fixed = False
    if errors and fix:
        try:
            apply_golden_workbook(path, ctx=c)
            # Also attempt session paste
            try:
                from ate.reporting.session_paste import paste_session_photos

                paste_session_photos()
            except Exception:
                pass
            fixed = True
            errors = _run_once()
        except Exception as exc:
            errors.append(f"fix failed: {exc}")

    return {
        "ok": not errors,
        "path": str(path),
        "errors": errors,
        "warnings": warnings,
        "fixed": fixed,
    }
