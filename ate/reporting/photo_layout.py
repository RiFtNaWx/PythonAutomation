"""Workbook photo-grid SoT.

Change Excel image boxes in campaign::

    #Test_Database/.../Version_N/_manifest/sheet_map.yaml
    tests.<key>.paste.photos    # e.g. u1_chA: A91  or  pos_u1_chA: A46

or Results -> Waveform layout on http://127.0.0.1:5174 (Save writes that YAML).

Python paste (lab_report.place_*) must call photo_anchor() here. Do not hardcode A91.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

_KEY_RE = re.compile(
    r"^(?:(?P<pol>pos|neg)_)?u(?P<unit>\d+)_ch(?P<ch>[ab])$",
    re.IGNORECASE,
)
_CELL_RE = re.compile(r"^[A-Z]{1,3}[1-9][0-9]{0,3}$")
_TEST_HEADER = re.compile(r"^  ([A-Za-z0-9_]+):\s*$")
_PHOTO_KEY_LINE = re.compile(
    r"^([ \t]*)([A-Za-z0-9_]+):\s*(\S+)(?:\s+(#.*))?$"
)
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_TMP_PREFIX = "_tmp"


def _ctx():
    from ate.core.database import get_context

    return get_context()


def canonical_key(unit: int, channel: str, polarity: str | None = None) -> str:
    ch = "chA" if "A" in str(channel).upper() else "chB"
    if polarity:
        pol = "pos" if str(polarity).upper().startswith("POS") else "neg"
        return f"{pol}_u{int(unit)}_{ch}"
    return f"u{int(unit)}_{ch}"


def parse_photo_key(key: str) -> dict[str, Any] | None:
    m = _KEY_RE.match(str(key).strip())
    if not m:
        return None
    pol = m.group("pol")
    unit = int(m.group("unit"))
    ch = "CHA" if m.group("ch").upper() == "A" else "CHB"
    polarity = pol.upper() if pol else None
    return {
        "key": canonical_key(unit, ch, polarity),
        "raw": str(key).strip(),
        "unit": unit,
        "channel": ch,
        "polarity": polarity,
    }


def _tests(sheet_map: dict[str, Any] | None = None) -> dict[str, Any]:
    sm = sheet_map if sheet_map is not None else _ctx().load_sheet_map()
    tests = (sm or {}).get("tests") or {}
    return tests if isinstance(tests, dict) else {}


def resolve_test_key(test_key: str, sheet_map: dict[str, Any] | None = None) -> str:
    """Return the yaml tests. key (folder key), accepting excel_sheet / folder aliases."""
    tests = _tests(sheet_map)
    want = str(test_key or "").strip()
    if want in tests:
        return want
    want_l = want.lower().replace("_", "")
    for key, entry in tests.items():
        if not isinstance(entry, dict):
            continue
        names = [str(key), str(entry.get("folder") or ""), str(entry.get("excel_sheet") or "")]
        if any(n.lower().replace("_", "") == want_l for n in names if n):
            return str(key)
        if entry.get("folder") == want or entry.get("excel_sheet") == want:
            return str(key)
    raise KeyError(f"sheet_map has no test {want!r}")


def photos_map(test_key: str, sheet_map: dict[str, Any] | None = None) -> dict[str, str]:
    """Canonical key -> Excel cell from paste.photos."""
    sm = sheet_map if sheet_map is not None else _ctx().load_sheet_map()
    yaml_key = resolve_test_key(test_key, sm)
    entry = _tests(sm).get(yaml_key) or {}
    paste = entry.get("paste") if isinstance(entry, dict) else None
    photos = (paste or {}).get("photos") if isinstance(paste, dict) else None
    if not isinstance(photos, dict):
        raise KeyError(f"{yaml_key} has no paste.photos in sheet_map.yaml")
    out: dict[str, str] = {}
    for raw, cell in photos.items():
        parsed = parse_photo_key(str(raw))
        ck = parsed["key"] if parsed else str(raw)
        val = str(cell).strip()
        if val:
            out[ck] = val
    return out


def photo_anchor(
    test_key: str,
    unit: int,
    channel: str = "CHA",
    polarity: str | None = None,
) -> str:
    """Excel cell for one photo box. ORT falls back to LayoutSpec if yaml misses a key."""
    key = canonical_key(unit, channel, polarity)
    try:
        grid = photos_map(test_key)
        if key in grid:
            return grid[key]
    except KeyError:
        grid = {}
    if str(test_key).upper() in {"ORT", "OVERLOAD"} or polarity:
        from ate.reporting.sheet_layout import ort_photo_anchor_map

        return ort_photo_anchor_map().get(key, "A46")
    if not grid:
        raise KeyError(
            f"No paste.photos for {test_key!r}. Set tests.<key>.paste.photos in "
            f"_manifest/sheet_map.yaml (Results -> Waveform layout)."
        )
    raise KeyError(f"{test_key} paste.photos missing {key}")


def list_photo_tests(sheet_map: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    sm = sheet_map if sheet_map is not None else _ctx().load_sheet_map()
    rows: list[dict[str, Any]] = []
    for key, entry in _tests(sm).items():
        if not isinstance(entry, dict):
            continue
        paste = entry.get("paste")
        photos = paste.get("photos") if isinstance(paste, dict) else None
        if not isinstance(photos, dict) or not photos:
            continue
        rows.append(
            {
                "test_key": str(key),
                "folder": str(entry.get("folder") or key),
                "excel_sheet": str(entry.get("excel_sheet") or key),
                "n_cells": len(photos),
            }
        )
    return rows


def _is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in _IMAGE_EXT and not path.name.startswith(_TMP_PREFIX)


def _name_match(path: Path, channel: str, polarity: str | None) -> bool:
    name = path.name.upper()
    if polarity:
        want = "POS" if str(polarity).upper().startswith("POS") else "NEG"
        other = "NEG" if want == "POS" else "POS"
        if other in name and want not in name:
            return False
        if want not in name and ("POS" in name or "NEG" in name):
            return False
    has_cha = "CHA" in name
    has_chb = "CHB" in name
    if has_cha or has_chb:
        return has_cha if str(channel).upper() != "CHB" else has_chb
    return True


def _shot_payload(root: Path, path: Path) -> dict[str, Any]:
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    st = path.stat()
    kind = "graph" if "graphs" in path.parts else "screenshot"
    return {
        "rel": rel,
        "name": path.name,
        "kind": kind,
        "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "url": f"http://127.0.0.1:8766/shot?rel={quote(rel, safe='/')}",
    }


def _collect_shots(
    ctx,
    folder: str,
    unit: int,
    channel: str,
    polarity: str | None,
) -> list[dict[str, Any]]:
    root = ctx.root()
    found: list[Path] = []
    for getter in (ctx.graph_dir, ctx.screenshot_dir):
        d = getter(folder, unit)
        if not d.is_dir():
            continue
        found.extend(p for p in d.iterdir() if _is_image(p) and _name_match(p, channel, polarity))
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [_shot_payload(root, p) for p in found]


def layout_preview(test_key: str | None = None) -> dict[str, Any]:
    ctx = _ctx()
    sm = ctx.load_sheet_map()
    tests = list_photo_tests(sm)
    if not tests:
        return {
            "source": str(ctx.sheet_map_path()),
            "hint": "No paste.photos in sheet_map.yaml yet.",
            "tests": [],
            "cells": [],
        }
    chosen = str(test_key or tests[0]["test_key"])
    yaml_key = resolve_test_key(chosen, sm)
    entry = _tests(sm).get(yaml_key) or {}
    folder = str(entry.get("folder") or yaml_key)
    photos = photos_map(yaml_key, sm)
    cells: list[dict[str, Any]] = []
    raw_photos = ((entry.get("paste") or {}) if isinstance(entry, dict) else {}).get("photos") or {}
    for raw, cell in raw_photos.items() if isinstance(raw_photos, dict) else []:
        parsed = parse_photo_key(str(raw)) or {
            "key": str(raw),
            "unit": 1,
            "channel": "CHA",
            "polarity": None,
        }
        shots = _collect_shots(
            ctx,
            folder,
            int(parsed.get("unit") or 1),
            str(parsed.get("channel") or "CHA"),
            parsed.get("polarity"),
        )
        cells.append(
            {
                "raw": str(raw),
                "key": parsed.get("key") or str(raw),
                "unit": parsed.get("unit"),
                "channel": parsed.get("channel"),
                "polarity": parsed.get("polarity"),
                "anchor": str(cell),
                "latest": shots[0] if shots else None,
                "previous": shots[1] if len(shots) > 1 else None,
                "n_shots": len(shots),
            }
        )
    return {
        "source": str(ctx.sheet_map_path()),
        "hint": (
            "SoT: _manifest/sheet_map.yaml tests."
            f"{yaml_key}.paste.photos -- edit cells here or in that file."
        ),
        "test_key": yaml_key,
        "folder": folder,
        "excel_sheet": str(entry.get("excel_sheet") or yaml_key),
        "tests": tests,
        "cells": cells,
        "anchors": photos,
    }


def validate_cell(cell: str) -> str:
    val = str(cell).strip().upper()
    if not _CELL_RE.match(val):
        raise ValueError(f"Invalid Excel cell {cell!r} (want A91 / AC91)")
    return val


def patch_photos_yaml(text: str, test_key: str, photos: dict[str, str]) -> str:
    """Replace paste.photos cells for one test; keep other lines/comments."""
    want = {str(k): validate_cell(v) for k, v in photos.items()}
    lines = text.splitlines(keepends=True)
    start: int | None = None
    for i, line in enumerate(lines):
        m = _TEST_HEADER.match(line.rstrip("\r\n"))
        if m and m.group(1) == test_key:
            start = i
            break
    if start is None:
        raise KeyError(f"sheet_map.yaml has no tests.{test_key}")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = _TEST_HEADER.match(lines[j].rstrip("\r\n"))
        if m:
            end = j
            break
    block = lines[start:end]
    photo_i: int | None = None
    for k, line in enumerate(block):
        if re.match(r"^      photos:\s*$", line.rstrip("\r\n")):
            photo_i = k
            break
    if photo_i is None:
        raise KeyError(f"tests.{test_key} has no paste.photos block")
    patched: set[str] = set()
    for k in range(photo_i + 1, len(block)):
        raw_line = block[k]
        stripped = raw_line.rstrip("\r\n")
        m = _PHOTO_KEY_LINE.match(stripped)
        if not m:
            if stripped.startswith("        ") or stripped.startswith("\t"):
                continue
            break
        indent, raw, _old, comment = m.group(1), m.group(2), m.group(3), m.group(4)
        if len(indent) < 8:
            break
        parsed = parse_photo_key(raw)
        ck = parsed["key"] if parsed else raw
        cell = want.get(raw) or want.get(ck)
        if not cell:
            continue
        nl = "\r\n" if raw_line.endswith("\r\n") else "\n" if raw_line.endswith("\n") else ""
        suffix = f"  {comment}" if comment else ""
        block[k] = f"{indent}{raw}: {cell}{suffix}{nl}"
        patched.add(raw)
        patched.add(ck)
    missing = [k for k in want if k not in patched]
    if missing:
        raise KeyError(f"tests.{test_key}.paste.photos missing keys: {missing}")
    lines[start:end] = block
    return "".join(lines)


def save_photo_anchors(test_key: str, photos: dict[str, str]) -> dict[str, Any]:
    ctx = _ctx()
    path = ctx.sheet_map_path()
    if not path.is_file():
        raise FileNotFoundError(f"sheet_map missing: {path}")
    sm = ctx.load_sheet_map()
    yaml_key = resolve_test_key(test_key, sm)
    text = path.read_text(encoding="utf-8")
    path.write_text(patch_photos_yaml(text, yaml_key, photos), encoding="utf-8")
    return {
        "ok": True,
        "test_key": yaml_key,
        "sheet_map": str(path),
        "photos": {k: validate_cell(v) for k, v in photos.items()},
    }


def resolve_shot_file(rel: str) -> Path:
    """Campaign-root file under screenshots/ or graphs/ only."""
    raw = str(rel or "").replace("\\", "/").lstrip("/")
    if not raw or ".." in raw.split("/"):
        raise PermissionError("bad rel")
    root = _ctx().root().resolve()
    full = (root / raw).resolve()
    try:
        full.relative_to(root)
    except ValueError as exc:
        raise PermissionError("outside campaign") from exc
    if not full.is_file():
        raise FileNotFoundError(raw)
    parts = {p.lower() for p in full.parts}
    if "screenshots" not in parts and "graphs" not in parts:
        raise PermissionError("not a graph/screenshot")
    if full.suffix.lower() not in _IMAGE_EXT:
        raise PermissionError("not an image")
    return full
