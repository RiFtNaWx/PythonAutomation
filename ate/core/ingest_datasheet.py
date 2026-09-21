"""Datasheet -> limits yaml -> Excel codes -> golden copy fill -> sweep summary.

OCR only if PDF text is thin. Cloud (one SKU HTML) before local OCR autodownload.
Never writes PDFs into #Test_Database. Golden xlsx source stays clean.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from ate.core.ocr_engine import text_is_thin
from ate.core.paths import CONFIG_DIR, PATH_RULE, store_config_path, store_portable
from ate.core.specs import LIMITS_DIR
from ate.reporting.session_paste import _is_real_cell

MYT = timezone(timedelta(hours=8))
TABLES_DIR = CONFIG_DIR / "datasheets" / "tables"
_SKIP_KEYS = frozenset(
    {"VCC", "vcc", "AWG", "INPUT_A_V", "INPUT_B_V", "freq_hz", "I_uA", "INPUT_A", "INPUT_B"}
)


def _part_key(part: str) -> str:
    return re.sub(r"[^A-Za-z0-9\-]+", "", str(part or "")).lower()


def export_part_tables(part: str, *, xlsx_rel: str = "") -> dict[str, Any]:
    """JSON index for later AI export. YAML stays canonical (limits + parts truth_table)."""
    from ate.core.specs import load_part_specs, load_part_yaml

    sku = str(part or "").strip().upper()
    pk = _part_key(sku)
    part_yaml = load_part_yaml(pk)
    pm = part_yaml.get("product_model") if isinstance(part_yaml.get("product_model"), dict) else {}
    tt = part_yaml.get("truth_table")
    if not tt:
        tt = pm.get("truth_table") if isinstance(pm, dict) else None
    voh = part_yaml.get("voh_table") if isinstance(part_yaml, dict) else None
    vol = part_yaml.get("vol_table") if isinstance(part_yaml, dict) else None
    specs = load_part_specs(pk)
    doc = {
        "part": sku,
        "part_key": pk,
        "path_rule": PATH_RULE,
        "canonical": {
            "specs": f"ate/config/limits/{pk}.yaml",
            "truth_table": f"ate/config/parts/{pk}.yaml",
            "extract": f"ate/config/datasheets/text/{pk}.txt",
            "xlsx": str(xlsx_rel or ""),
        },
        "specs": specs,
        "truth_table": tt if isinstance(tt, dict) else ({"rows": tt} if tt else {}),
        "voh_table": voh if isinstance(voh, list) else [],
        "vol_table": vol if isinstance(vol, list) else [],
        "format": "json",
        "note": "Edit yaml, then re-ingest. Do not treat this JSON as SoT. XML is not used.",
    }
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    dest = TABLES_DIR / f"{pk}.json"
    dest.write_text(json.dumps(doc, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    doc["path"] = store_config_path(dest)
    return doc


def accept_upload(pdf: Path, part: str) -> Path:
    """Copy an operator PDF into local Reference. Not #Test_Database."""
    from ate.core.lookup import reference_root, resolve_pdf

    sku = str(part or "").strip().upper()
    src = Path(pdf).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"missing pdf: {src}")
    hit = resolve_pdf(sku)
    if hit and hit.is_file() and hit.resolve() == src:
        return hit
    root = reference_root()
    root.mkdir(parents=True, exist_ok=True)
    dest = root / f"{sku}_(RevUpload).pdf"
    if dest.resolve() != src:
        shutil.copy2(src, dest)
    return dest


def extract_text(part: str, pdf: Path | None = None, *, ocr: str = "auto") -> dict[str, Any]:
    from ate.core.lookup import extract_and_store_text, resolve_pdf
    from ate.core.ocr_engine import extract_pdf

    sku = str(part or "").strip().upper()
    pk = _part_key(sku)
    path = Path(pdf) if pdf else resolve_pdf(sku)
    if path is None or not Path(path).is_file():
        return {"part": sku, "engine": "none", "text": "", "thin": True, "pdf": ""}
    path = Path(path)
    got = extract_pdf(path, engine="text")
    blob = str(got.get("text") or "")
    engine = "text"
    if text_is_thin(blob) and ocr not in ("off", "false", "0"):
        got = extract_pdf(path, engine=ocr if ocr != "auto" else "auto")
        blob = str(got.get("text") or blob)
        engine = str(got.get("engine") or engine)
    dest = extract_and_store_text(pk, path)
    if blob and dest.is_file() and len(blob) > len(dest.read_text(encoding="utf-8")):
        dest.write_text(blob, encoding="utf-8")
    elif blob and dest.is_file() and engine != "text":
        dest.write_text(blob, encoding="utf-8")
    return {
        "part": sku,
        "part_key": pk,
        "pdf": str(path),
        "engine": engine,
        "text_len": len(blob.strip()),
        "thin": text_is_thin(blob),
        "extract": str(dest),
    }


def excel_map(*, ctx=None) -> dict[str, Any]:
    """Measurement id -> sheet!cell from this Version sheet_map. Does not guess."""
    try:
        from ate.core.database import get_context

        c = ctx or get_context()
        sm = c.load_sheet_map() if hasattr(c, "load_sheet_map") else {}
        sm_path = str(c.sheet_map_path()) if hasattr(c, "sheet_map_path") else ""
    except Exception as exc:
        return {"mapped": [], "note": str(exc)}
    tests = sm.get("tests") if isinstance(sm, dict) else {}
    mapped: list[dict[str, Any]] = []
    if not isinstance(tests, dict):
        return {"mapped": [], "unmapped_tests": []}
    for key, entry in tests.items():
        if not isinstance(entry, dict):
            continue
        sheet = str(entry.get("excel_sheet") or key)
        paste = entry.get("paste") if isinstance(entry.get("paste"), dict) else {}
        values = paste.get("values") if isinstance(paste, dict) else {}
        if not isinstance(values, dict):
            continue
        for mid, raw in values.items():
            mapped.append(
                {
                    "test": str(key),
                    "id": str(mid),
                    "sheet": sheet,
                    "cells": raw,
                    "ok": bool(_is_real_cell(raw) or isinstance(raw, (list, dict))),
                }
            )
    return {"mapped": mapped, "sheet_map": sm_path}


def _row_sort_key(row: dict[str, Any]) -> tuple:
    vcc = row.get("VCC", row.get("vcc"))
    freq = row.get("freq_hz") or 0
    awg = str(row.get("AWG") or "")
    try:
        v = float(vcc) if vcc is not None else 0.0
    except (TypeError, ValueError):
        v = 0.0
    try:
        f = float(freq)
    except (TypeError, ValueError):
        f = 0.0
    return (v, f, awg)


def organize_sweeps(report: dict[str, Any] | None = None, *, ctx=None) -> dict[str, Any]:
    """Sort sweep rows and write sessions/sweep_summary.md. Copilot uses unmapped ids."""
    from ate.core.database import get_context
    from ate.core.datalog import load_report

    c = ctx or get_context()
    doc = report if isinstance(report, dict) else load_report(ctx=c)
    blocks: list[dict[str, Any]] = []
    for step in doc.get("steps") or []:
        if not isinstance(step, dict):
            continue
        data = step.get("data") if isinstance(step.get("data"), dict) else {}
        rows = data.get("rows") if isinstance(data, dict) else None
        if not isinstance(rows, list) or not rows:
            continue
        clean = [r for r in rows if isinstance(r, dict)]
        clean.sort(key=_row_sort_key)
        blocks.append(
            {
                "test_id": str(step.get("test_id") or ""),
                "dut": step.get("dut") or 1,
                "channel": str(step.get("channel") or "CHA"),
                "rows": clean,
            }
        )
    dest_dir = c.sessions_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    md = dest_dir / "sweep_summary.md"
    js = dest_dir / "sweep_summary.json"
    lines = [
        f"# Sweep summary  {datetime.now(MYT).isoformat(timespec='seconds')}",
        "",
        "Preset sheet `Sweep` on the golden *copy*: row1 headers, data from row 2, sorted by VCC then freq then AWG.",
        "",
    ]
    for b in blocks:
        lines.append(f"## {b['test_id']} DUT{b['dut']} {b['channel']}")
        keys: list[str] = []
        for r in b["rows"]:
            for k in r:
                if k not in keys:
                    keys.append(str(k))
        if not keys:
            continue
        lines.append("| " + " | ".join(keys) + " |")
        lines.append("| " + " | ".join("---" for _ in keys) + " |")
        for r in b["rows"]:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
        lines.append("")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    js.write_text(json.dumps(blocks, indent=2, default=str), encoding="utf-8")
    return {"blocks": len(blocks), "markdown": str(md), "json": str(js), "sweeps": blocks}


def copilot_prompt(
    *,
    part: str,
    limits: dict[str, Any],
    excel: dict[str, Any],
    extract: dict[str, Any],
    fill: dict[str, Any] | None = None,
    sweeps: dict[str, Any] | None = None,
) -> str:
    pk = _part_key(part)
    specs = limits.get("specs") if isinstance(limits.get("specs"), list) else []
    ids = [str(s.get("id")) for s in specs if isinstance(s, dict) and s.get("id")]
    mapped = excel.get("mapped") if isinstance(excel, dict) else []
    mapped_ids = {str(m.get("id")) for m in (mapped or []) if isinstance(m, dict)}
    unmapped = [i for i in ids if i not in mapped_ids]
    fill_path = (fill or {}).get("excel") or ""
    sweep_md = (sweeps or {}).get("markdown") or ""
    return "\n".join(
        [
            "Read AGENTS.md / CLAUDE.md / AI.md first. Do not paste a Copilot block.",
            f"- Job: ingest {part} -> ate/config/limits/{pk}.yaml then golden *_filled.xlsx",
            f"- OCR engine: {extract.get('engine')} text_len={extract.get('text_len')} thin={extract.get('thin')}",
            f"- Spec ids: {', '.join(ids) or '(none)'}",
            f"- Excel mapped: {len(mapped or [])} paste.values. Unmapped: {', '.join(unmapped) or '(none)'}",
            f"- Golden fill: {fill_path or 'workbook/*_filled.xlsx (source untouched)'}",
            f"- Sweep summary: {sweep_md or 'sessions/sweep_summary.md'}",
            f"- Path rule: {PATH_RULE}",
            "- Do not guess A91. Probe live xlsx. Do not scrape into #Test_Database.",
            "Proof: python -m ate.core.check_ingest_datasheet then DEMO.",
        ]
    )


def ingest(
    part: str,
    *,
    pdf: str | Path | None = None,
    xlsx: str | Path | None = None,
    part_key: str = "",
    web_ok: bool = True,
    ocr: str = "auto",
    fill_excel: bool = True,
    copy_golden: bool = True,
    ctx=None,
) -> dict[str, Any]:
    from ate.core.database import get_context, set_context
    from ate.core.lookup import sync_limits_from_local
    from ate.reporting.session_values import fill_workbook_from_report

    sku = str(part or "").strip().upper()
    pk = str(part_key or _part_key(sku) or "")
    if ctx is None and sku == "RS0204":
        ctx = set_context(
            component="Level",
            part="RS0204",
            package="TSSOP14",
            operator="ChangThong",
            version="Version_1",
            part_key="rs0204",
        )
    c = ctx or get_context()
    if not sku:
        sku = str(getattr(c, "part", "") or "").strip().upper()
        pk = str(part_key or _part_key(sku) or getattr(c, "part_key", "") or "")
    uploaded = ""
    if pdf:
        dest = accept_upload(Path(pdf), sku)
        uploaded = str(dest)
    extracted = extract_text(sku, Path(uploaded) if uploaded else None, ocr=ocr)
    if extracted.get("thin") and web_ok and extracted.get("engine") == "text":
        from ate.core.datasheet import fetch_and_store

        web = fetch_and_store(sku, part_key=pk)
        limits = web
        extracted["engine"] = str(web.get("source") or "web")
        extracted["note"] = "cloud HTML used because local text was thin"
    else:
        limits = sync_limits_from_local(sku, part_key=pk, web_ok=web_ok)
    xlsx_path = Path(xlsx).expanduser() if xlsx else None
    sheet_wrote = False
    if xlsx_path is not None and xlsx_path.is_file() and hasattr(c, "sheet_map_path"):
        from ate.core.campaign_outline import apply_campaign_map

        try:
            sm_path = c.sheet_map_path()
            if sm_path.is_file():
                row = apply_campaign_map(sm_path, xlsx=xlsx_path)
                sheet_wrote = bool(row.get("wrote"))
        except Exception:
            sheet_wrote = False
    excel = excel_map(ctx=c)
    try:
        sweeps = organize_sweeps(ctx=c)
    except Exception as exc:
        sweeps = {"blocks": 0, "error": str(exc)}
    fill: dict[str, Any] = {}
    if fill_excel:
        try:
            fill = fill_workbook_from_report(
                ctx=c,
                demo=False,
                copy_golden=copy_golden,
                workbook_path=xlsx_path if xlsx_path and xlsx_path.is_file() else None,
            )
        except Exception as exc:
            fill = {"status": "error", "error": str(exc)}
    prompt = copilot_prompt(
        part=sku,
        limits=limits if isinstance(limits, dict) else {},
        excel=excel,
        extract=extracted,
        fill=fill,
        sweeps=sweeps,
    )
    tables = export_part_tables(sku, xlsx_rel=store_portable(xlsx_path) if xlsx_path else "")
    out = {
        "ok": True,
        "part": sku,
        "part_key": pk,
        "path_rule": PATH_RULE,
        "extract": extracted,
        "limits": {
            "yaml": store_config_path(limits.get("yaml")) if isinstance(limits, dict) and limits.get("yaml") else f"ate/config/limits/{pk}.yaml",
            "source": limits.get("source") if isinstance(limits, dict) else "",
            "specs": limits.get("specs") if isinstance(limits, dict) else [],
            "wrote": limits.get("wrote") if isinstance(limits, dict) else False,
        },
        "excel": excel,
        "fill": fill,
        "sheet_map_wrote": sheet_wrote,
        "sweeps": {"markdown": sweeps.get("markdown"), "json": sweeps.get("json"), "blocks": sweeps.get("blocks")},
        "tables": {"path": tables.get("path"), "canonical": tables.get("canonical")},
        "copilot": prompt,
        "preset": "Sweep sheet on the filled copy: headers row 1, sorted VCC/freq/AWG. Source xlsx is golden.",
    }
    if isinstance(extracted, dict):
        if extracted.get("pdf"):
            extracted["pdf"] = store_portable(extracted["pdf"])
        if extracted.get("extract"):
            extracted["extract"] = store_config_path(extracted["extract"])
    dest = CONFIG_DIR / "datasheets" / "last_ingest.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dump = {k: v for k, v in out.items() if k != "copilot"}
    dest.write_text(json.dumps(dump, indent=2, default=str), encoding="utf-8")
    out["ingest_json"] = store_config_path(dest)
    return out


def main() -> int:
    import argparse
    import json as _json

    p = argparse.ArgumentParser(description="Ingest one SKU datasheet into limits + golden Excel copy")
    p.add_argument("part", nargs="?")
    p.add_argument("--pdf", default="")
    p.add_argument("--xlsx", default="")
    p.add_argument("--ocr", default="auto")
    p.add_argument("--no-web", action="store_true")
    p.add_argument("--no-excel", action="store_true")
    p.add_argument("--audit", action="store_true", help="Scan all inventory reports vs TestSpecs")
    args = p.parse_args()
    if args.audit:
        from ate.core.report_coverage import audit

        got = audit(write=True)
        print(
            _json.dumps(
                {"n": got.get("n"), "formats": got.get("formats"), "path": got.get("path")},
                indent=2,
            )
        )
        return 0
    if not args.part:
        p.error("part required unless --audit")
    out = ingest(
        args.part,
        pdf=args.pdf or None,
        xlsx=args.xlsx or None,
        web_ok=not args.no_web,
        ocr=args.ocr,
        fill_excel=not args.no_excel,
        copy_golden=True,
    )
    print(out.get("copilot") or "")
    print(f"yaml={out['limits'].get('yaml')} engine={out['extract'].get('engine')} fill={out['fill'].get('excel')}")
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

