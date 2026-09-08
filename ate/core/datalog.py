"""STS8200-shaped rolling session report (ate.datalog.v1).

Keeps per-START session_{ts}.json. Adds:
  sessions/report.json          -- living overwrite per campaign
  sessions/archive/{id}.json    -- snapshot at end_session
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

MYT = timezone(timedelta(hours=8))
SCHEMA = "ate.datalog.v1"


def report_path(ctx) -> Path:
    return ctx.sessions_dir() / "report.json"


def archive_dir(ctx) -> Path:
    return ctx.sessions_dir() / "archive"


def _empty_report(ctx, session: dict[str, Any] | None = None) -> dict[str, Any]:
    from ate.core.tags import load_tags

    ident = dict((session or {}).get("context") or ctx.identity())
    try:
        t = load_tags(ctx)
        ident["tags"] = list(t.get("tags") or [])
        ident["boards"] = list(t.get("boards") or [])
    except Exception:
        ident.setdefault("tags", [])
        ident.setdefault("boards", [])
    started = str((session or {}).get("started_at") or datetime.now(MYT).isoformat(timespec="seconds"))
    return {
        "schema": SCHEMA,
        "header": {
            "time": datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S"),
            "program": "ate.worker",
            "user": str(ident.get("operator") or ""),
            "lot_id": "",
            "total": 0,
            "pass": 0,
            "fail": 0,
            "beginning_time": started,
            "ending_time": "",
            "total_testing_time_s": 0,
            "idle_time_s": 0,
            "session_id": str((session or {}).get("session_id") or ""),
            "status": str((session or {}).get("status") or "running"),
        },
        "identity": ident,
        "params": dict((session or {}).get("params") or {}),
        "instrument_map": dict((session or {}).get("instrument_map") or {}),
        "sites": [],
        "steps": [],
        "artifacts": [],
    }


def _ensure_sites(doc: dict[str, Any], dut_indices: list[int] | None) -> None:
    sites = doc.setdefault("sites", [])
    if not isinstance(sites, list):
        doc["sites"] = []
        sites = doc["sites"]
    have = {int(s.get("site")) for s in sites if isinstance(s, dict) and s.get("site") is not None}
    for dut in dut_indices or []:
        d = int(dut)
        if d not in have:
            sites.append({"site": d, "part_id": d, "sbin": 0, "measurements": []})
            have.add(d)


def _recompute_header(doc: dict[str, Any], session: dict[str, Any] | None = None) -> None:
    steps = [s for s in (doc.get("steps") or []) if isinstance(s, dict)]
    total = len(steps)
    passed = sum(1 for s in steps if s.get("success") is True)
    failed = sum(1 for s in steps if s.get("success") is False)
    hdr = doc.setdefault("header", {})
    hdr["total"] = total
    hdr["pass"] = passed
    hdr["fail"] = failed
    hdr["time"] = datetime.now(MYT).strftime("%Y-%m-%d %H:%M:%S")
    if session:
        hdr["session_id"] = str(session.get("session_id") or hdr.get("session_id") or "")
        hdr["status"] = str(session.get("status") or hdr.get("status") or "")
        if session.get("started_at"):
            hdr["beginning_time"] = str(session["started_at"])
        if session.get("finished_at"):
            hdr["ending_time"] = str(session["finished_at"])
            try:
                t0 = datetime.fromisoformat(str(session["started_at"]))
                t1 = datetime.fromisoformat(str(session["finished_at"]))
                hdr["total_testing_time_s"] = max(0, int((t1 - t0).total_seconds()))
            except Exception:
                pass


def sync_report_from_session(session: dict[str, Any], *, ctx=None) -> Path:
    """Overwrite sessions/report.json from the active RunSession dict."""
    from ate.core.database import get_context

    c = ctx or get_context()
    c.sessions_dir().mkdir(parents=True, exist_ok=True)
    path = report_path(c)
    doc = _empty_report(c, session)
    doc["steps"] = list(session.get("steps") or [])
    doc["artifacts"] = list(session.get("artifacts") or [])
    params = session.get("params") or {}
    duts = params.get("dut_indices") if isinstance(params, dict) else None
    if not duts:
        duts = [int(params.get("unit_index") or 1)] if isinstance(params, dict) else [1]
    _ensure_sites(doc, [int(x) for x in duts])

    # Fold optional measurements from steps into matching site
    for step in doc["steps"]:
        if not isinstance(step, dict):
            continue
        meas = step.get("measurements")
        if not isinstance(meas, list) or not meas:
            continue
        site_n = int(step.get("dut") or step.get("site") or params.get("unit_index") or 1)
        for site in doc["sites"]:
            if int(site.get("site") or 0) != site_n:
                continue
            for m in meas:
                if isinstance(m, dict):
                    site.setdefault("measurements", []).append(dict(m))
            break

    _recompute_header(doc, session)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return path


def archive_report(session: dict[str, Any], *, ctx=None) -> Optional[Path]:
    """Copy current report.json to sessions/archive/{session_id}.json."""
    from ate.core.database import get_context

    c = ctx or get_context()
    src = report_path(c)
    if not src.is_file():
        sync_report_from_session(session, ctx=c)
    dest_dir = archive_dir(c)
    dest_dir.mkdir(parents=True, exist_ok=True)
    sid = str(session.get("session_id") or "session_unknown")
    dest = dest_dir / f"{sid}.json"
    # Prefer the just-synced report contents
    if src.is_file():
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        dest.write_text(json.dumps(session, indent=2), encoding="utf-8")
    return dest


def load_report(ctx=None) -> dict[str, Any]:
    from ate.core.database import get_context

    c = ctx or get_context()
    path = report_path(c)
    if not path.is_file():
        return _empty_report(c)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else _empty_report(c)
