"""Session-end auto-paste of Test_Database photos into campaign workbook.

Uses sheet_map paste.photos + lab_report.place_mapped_photos. Skips FILL_ME.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_LOG = logging.getLogger("ate.session_paste")
_FILL = {"fill_me", "fill-me", "todo", "tbd", ""}


def _is_real_cell(val: Any) -> bool:
    s = str(val or "").strip()
    if not s:
        return False
    if s.lower() in _FILL or s.upper().startswith("FILL"):
        return False
    return True


def _latest_image(folder: Path) -> Path | None:
    if not folder.is_dir():
        return None
    files = [
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        and not p.name.startswith("_tmp")
    ]
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def paste_session_photos(session: dict[str, Any] | None = None) -> dict[str, Any]:
    """Paste latest graphs/screenshots for every sheet_map test with real anchors."""
    from ate.core.database import get_context
    from ate.reporting.lab_report import place_mapped_photos
    from ate.reporting.photo_layout import parse_photo_key

    ctx = get_context()
    sm = ctx.load_sheet_map()
    tests = sm.get("tests") if isinstance(sm, dict) else {}
    if not isinstance(tests, dict):
        return {"pasted": 0, "skipped": 0, "errors": ["no sheet_map tests"]}

    pasted = 0
    skipped = 0
    errors: list[str] = []
    sample = max(1, int(ctx.sample_size or 4))

    for key, entry in tests.items():
        if not isinstance(entry, dict):
            continue
        photos = entry.get("paste", {}).get("photos") if isinstance(entry.get("paste"), dict) else None
        if photos is None:
            photos = entry.get("paste.photos")  # unlikely
        if not isinstance(photos, dict) or not photos:
            # also accept entry["paste"]["photos"] already handled; try nested
            paste_block = entry.get("paste")
            if isinstance(paste_block, dict):
                photos = paste_block.get("photos")
            if not isinstance(photos, dict) or not photos:
                skipped += 1
                continue
        folder = str(entry.get("folder") or key)
        for pkey, cell in photos.items():
            if not _is_real_cell(cell):
                skipped += 1
                continue
            meta = parse_photo_key(str(pkey))
            if not meta:
                skipped += 1
                continue
            unit = int(meta["unit"])
            if unit < 1 or unit > sample:
                skipped += 1
                continue
            ch = str(meta["channel"])
            pol = meta.get("polarity")
            graph_dir = ctx.graph_dir(folder, unit)
            shot_dir = ctx.screenshot_dir(folder, unit)
            img = _latest_image(graph_dir) or _latest_image(shot_dir)
            if img is None:
                skipped += 1
                continue
            try:
                place_mapped_photos(
                    test_key=str(key),
                    photo_path=img,
                    unit_index=unit,
                    channel=ch,
                    polarity=pol,
                )
                pasted += 1
            except Exception as exc:
                errors.append(f"{key}/{pkey}: {exc}")
                _LOG.warning("paste failed %s %s: %s", key, pkey, exc)

    return {"pasted": pasted, "skipped": skipped, "errors": errors}
