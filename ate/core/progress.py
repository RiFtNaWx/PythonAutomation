"""Open progress board: last-seen, run counts, comments. No login.

Files live under #Test_Database/_ate (OneDrive). GitHub issues are optional
on clone PCs with `gh`. Tests patch BOARD_PATH / PRESENCE_DIR.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from ate.core.paths import TEST_DB_ROOT

MYT = timezone(timedelta(hours=8))
GH_REPO = "RiFtNaWx/PythonAutomation"
BOARD_PATH: Path | None = None
PRESENCE_DIR: Path | None = None
_ID_RE = re.compile(r"^[a-z][a-z0-9]*$")


def _ate_dir() -> Path:
    return Path(TEST_DB_ROOT) / "_ate"


def board_file() -> Path:
    return Path(BOARD_PATH) if BOARD_PATH is not None else _ate_dir() / "board.yaml"


def presence_dir() -> Path:
    return Path(PRESENCE_DIR) if PRESENCE_DIR is not None else _ate_dir() / "presence"


def _now() -> str:
    return datetime.now(MYT).isoformat(timespec="seconds")


def _safe_id(raw: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "", str(raw or "").strip().lower())
    if not s or not _ID_RE.match(s):
        return "unknown"
    return s


def heartbeat(
    *,
    owner_id: str,
    label: str = "",
    campaign: str = "",
) -> dict[str, Any]:
    oid = _safe_id(owner_id)
    if oid in ("unknown", "all"):
        return {"skipped": True, "reason": "observer"}
    folder = presence_dir()
    folder.mkdir(parents=True, exist_ok=True)
    row = {
        "id": oid,
        "label": str(label or owner_id).strip() or oid,
        "ts": _now(),
        "campaign": str(campaign or "").strip(),
    }
    (folder / f"{oid}.json").write_text(json.dumps(row, indent=0) + "\n", encoding="utf-8")
    return row


def list_presence() -> list[dict[str, Any]]:
    folder = presence_dir()
    if not folder.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for fp in sorted(folder.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("id"):
            out.append(data)
    return out


def board_list() -> list[dict[str, Any]]:
    path = board_file()
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return []
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict) and str(x.get("text") or "").strip()]


def board_add(
    *,
    author: str,
    text: str,
    kind: str = "comment",
) -> dict[str, Any]:
    body = str(text or "").strip()
    if not body:
        raise ValueError("text required")
    who = str(author or "").strip() or "anon"
    k = str(kind or "comment").strip().lower()
    if k not in ("comment", "question"):
        k = "comment"
    item = {"ts": _now(), "author": who, "kind": k, "text": body[:2000]}
    items = board_list()
    items.append(item)
    path = board_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"items": items}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return {"item": item, "count": len(items)}


def open_github_issue(*, title: str, body: str = "") -> dict[str, Any]:
    """Clone PCs with gh. Zip users keep the board row only."""
    t = str(title or "").strip()[:80]
    if not t:
        raise ValueError("title required")
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}
    try:
        r = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                GH_REPO,
                "--title",
                t,
                "--body",
                str(body or t),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "gh is not on this PC. The note stays on the board. "
            "Open a GitHub issue from a git clone after `gh auth login`."
        ) from exc
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "gh failed").strip().splitlines()
        raise RuntimeError(
            (err[-1] if err else "gh failed")
            + ". Note is on the board. Clone + gh auth to open an issue."
        )
    url = (r.stdout or "").strip().splitlines()
    return {"url": url[-1] if url else "", "repo": GH_REPO}


def _person_fold(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(raw or "").strip().lower())


def _idle_label(last: str) -> str:
    if not last:
        return "no runs"
    raw = str(last).strip()
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return "no runs"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=MYT)
    hours = (datetime.now(ts.tzinfo) - ts).total_seconds() / 3600.0
    if hours < 24:
        return "today"
    days = int(hours / 24)
    if days < 3:
        return f"{days}d"
    return f"{days}d idle"


def sku_ownership(runs: list[dict[str, Any]] | None = None) -> dict[str, list[dict[str, Any]]]:
    """Tracking PIC + owners.yaml parts. Unowned = no lab PIC on this package."""
    from ate.core.database import canonical_person_label, load_owners
    from ate.core.new_product import lab_pic_id, load_inventory, part_key_for

    last_by_sku: dict[tuple[str, str], dict[str, str]] = {}
    for row in runs or []:
        if not isinstance(row, dict):
            continue
        part = str(row.get("part") or "").strip().upper()
        pkg = str(row.get("package") or "").strip()
        started = str(row.get("started") or "")
        if not part or not started:
            continue
        key = (part, pkg)
        prev = str((last_by_sku.get(key) or {}).get("last") or "")
        if started >= prev:
            last_by_sku[key] = {
                "last": started,
                "operator": canonical_person_label(str(row.get("operator") or ""))
                or str(row.get("operator") or ""),
            }

    assignees: dict[str, list[str]] = {}
    for owner in load_owners():
        oid = str(owner.get("id") or "").lower()
        if oid in ("all", "kevin", "ate") or str(owner.get("role") or "").lower() == "observer":
            continue
        if owner.get("alias_of"):
            continue
        lab = canonical_person_label(str(owner.get("label") or oid)) or str(
            owner.get("label") or oid
        )
        for p in owner.get("parts") or []:
            pk = str(p or "").strip().lower()
            if not pk:
                continue
            slot = assignees.setdefault(pk, [])
            if lab not in slot:
                slot.append(lab)

    owned: list[dict[str, Any]] = []
    unowned: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in load_inventory():
        part = str(row.get("part") or "").strip().upper()
        pkg = str(row.get("package") or "").strip()
        if not part or not pkg:
            continue
        status = str(row.get("status") or "").strip().upper()
        if status in ("PASS", "COMPLETED", "DONE"):
            continue
        key = (part, pkg)
        if key in seen:
            continue
        seen.add(key)
        pic = lab_pic_id(str(row.get("pic") or ""))
        if pic:
            pic = canonical_person_label(pic) or pic
        pk = part_key_for(part)
        last = last_by_sku.get(key) or {}
        item = {
            "part": part,
            "package": pkg,
            "model": str(row.get("model") or part),
            "category": str(row.get("category") or ""),
            "pic": pic,
            "owners": list(assignees.get(pk) or []),
            "last": str(last.get("last") or ""),
            "last_operator": str(last.get("operator") or ""),
            "status": str(row.get("status") or ""),
        }
        if pic:
            owned.append(item)
        else:
            unowned.append(item)
    return {"owned": owned, "unowned": unowned}


def who_has_tests(*, limit: int = 400) -> list[dict[str, Any]]:
    """Operator x SKU x enabled test id x source file:line (no folder rewrite)."""
    from ate.core.database import canonical_person_label, load_owners
    from ate.core.paths import PARTS_DIR
    from ate.core.test_detect import snippet_for_id
    from ate.fixture.modes import enabled_tests_for_part

    out: list[dict[str, Any]] = []
    for owner in load_owners():
        oid = str(owner.get("id") or "").lower()
        if oid in ("all", "kevin", "ate") or str(owner.get("role") or "").lower() == "observer":
            continue
        if owner.get("alias_of"):
            continue
        lab = canonical_person_label(str(owner.get("label") or oid)) or str(
            owner.get("label") or oid
        )
        for p in owner.get("parts") or []:
            pk = str(p or "").strip().lower()
            if not pk:
                continue
            enabled = enabled_tests_for_part(pk) or []
            part_path = PARTS_DIR / f"{pk}.yaml"
            for tid in enabled:
                tid_s = str(tid or "").strip().lower()
                if not tid_s:
                    continue
                snip = snippet_for_id(tid_s) or {}
                file_s = str(snip.get("file") or "").replace("\\", "/")
                lineno = snip.get("lineno")
                from ate.core.paths import CONFIG_DIR

                recipe_fp = CONFIG_DIR / "recipes" / f"{tid_s}.yaml"
                if recipe_fp.is_file():
                    kind = "recipe"
                    src = f"recipe:{tid_s}"
                elif file_s and "/ate/tests/" in f"/{file_s}":
                    kind = "path-b"
                    short = "/".join(file_s.split("/")[-2:])
                    src = f"{short}:{lineno}" if lineno not in (None, "") else short
                elif file_s:
                    kind = "golden"
                    short = "/".join(file_s.split("/")[-2:])
                    src = f"{short}:{lineno}" if lineno not in (None, "") else short
                else:
                    kind = "catalog"
                    src = ""
                out.append(
                    {
                        "operator": lab,
                        "part": pk.upper(),
                        "part_key": pk,
                        "test_id": tid_s,
                        "source": src,
                        "kind": kind,
                        "has_yaml": part_path.is_file(),
                    }
                )
                if len(out) >= max(1, min(2000, int(limit or 400))):
                    return out
    return out


def progress_summary(*, limit: int = 200) -> dict[str, Any]:
    from ate.core.database import canonical_person_label, load_owners
    from ate.core.datalog import list_runs

    listed = list_runs(scope="all", limit=max(1, min(200, int(limit or 200))))
    runs = listed.get("runs") if isinstance(listed, dict) else []
    if not isinstance(runs, list):
        runs = []
    people: dict[str, dict[str, Any]] = {}
    for row in runs:
        if not isinstance(row, dict):
            continue
        who = str(row.get("operator") or "").strip() or "?"
        who = canonical_person_label(who) or who
        slot = people.setdefault(
            who,
            {
                "operator": who,
                "runs": 0,
                "pass": 0,
                "fail": 0,
                "last": "",
                "part": "",
                "package": "",
            },
        )
        slot["runs"] += 1
        slot["pass"] += int(row.get("pass") or 0)
        slot["fail"] += int(row.get("fail") or 0)
        started = str(row.get("started") or "")
        if started >= str(slot.get("last") or ""):
            slot["last"] = started
            slot["part"] = str(row.get("part") or slot.get("part") or "")
            slot["package"] = str(row.get("package") or slot.get("package") or "")
    by_lower = {_person_fold(k): k for k in people}
    for owner in load_owners():
        oid = str(owner.get("id") or "").lower()
        if oid in ("all", "kevin", "ate") or str(owner.get("role") or "").lower() == "observer":
            continue
        if owner.get("alias_of"):
            continue
        lab = canonical_person_label(str(owner.get("label") or oid)) or str(
            owner.get("label") or oid
        )
        if _person_fold(lab) in by_lower or oid in by_lower:
            continue
        people[lab] = {
            "operator": lab,
            "runs": 0,
            "pass": 0,
            "fail": 0,
            "last": "",
            "part": "",
            "package": "",
        }
        by_lower[_person_fold(lab)] = lab
    rows = sorted(
        people.values(),
        key=lambda r: (str(r.get("last") or ""), str(r.get("operator") or "")),
        reverse=True,
    )
    for slot in rows:
        slot["idle"] = _idle_label(str(slot.get("last") or ""))
    skus = sku_ownership(runs)
    return {
        "root": str(listed.get("root") or TEST_DB_ROOT),
        "cloud_kind": listed.get("cloud_kind"),
        "people": rows,
        "presence": list_presence(),
        "board": board_list()[-40:],
        "run_count": listed.get("count") or len(runs),
        "owned": skus["owned"],
        "unowned": skus["unowned"],
        "who_tests": who_has_tests(limit=400),
    }
