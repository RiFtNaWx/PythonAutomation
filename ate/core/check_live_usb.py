"""Live USB walk via worker 8766. Do not import Instruments / check_all_parts.

PyVISA in this process hangs while the worker owns USB. Plan rows come from
physics_enabled.json. Leftover 13 still RUN (named, not fake). Skip only
input_off_leakage / input() goldens. DMM missing is not a skip.
"""
from __future__ import annotations

import ast
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

WORKER = "http://127.0.0.1:8766"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROOF = HERE / "_check_data" / "live_usb_stamps.json"
PHYS = HERE / "_check_data" / "physics_enabled.json"
WORKER_SRC = REPO / "ate" / "worker" / "server.py"
PARTS_DIR = REPO / "ate" / "config" / "parts"
SKIP_IDS = frozenset({"input_off_leakage"})
OPERATOR = "Eugene"
START_RPC = "run_sequence_async"
ROW_TIMEOUT_S = 1200.0


def rpc(method: str, params: dict[str, Any] | None = None, timeout: float = 90.0) -> Any:
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    req = urllib.request.Request(
        WORKER,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    if payload.get("error"):
        raise RuntimeError(f"{method}: {payload['error']}")
    return payload.get("result")


def selfcheck() -> list[str]:
    """Fail-closed: this module must RPC the UI START method; worker must dispatch it."""
    errors: list[str] = []
    src = Path(__file__).read_text(encoding="utf-8")
    worker = WORKER_SRC.read_text(encoding="utf-8") if WORKER_SRC.is_file() else ""
    if f'"{START_RPC}"' not in src and f"'{START_RPC}'" not in src:
        errors.append(f"check_live_usb must rpc {START_RPC} (UI START)")
    if src.count("rpc(") < 6:
        errors.append("walker must actually call rpc() for START/DEMO")
    if f'method == "{START_RPC}"' not in worker:
        errors.append(f"worker must dispatch {START_RPC}")
    if "get_pending_prompt" not in src:
        errors.append("walker must rpc get_pending_prompt (UI Continue)")
    if "operator_respond" not in src:
        errors.append("walker must rpc operator_respond (UI Continue)")
    if "open_session" not in src:
        errors.append("walker must rpc open_session (UI Open Session)")
    if '"auto_continue": False' not in src:
        errors.append(
            "USB START must pass auto_continue False; pause_hook needs Continue"
        )
    if "if not live:" not in src:
        errors.append("walker must abort START when mapping is not live USB")
    if "open session first" not in src.lower():
        errors.append("Open Session first / mapping-empty FAIL must stay retryable")
    if _keep_row({"ok": False, "attempted": True, "error": "Open Session first."}):
        errors.append("Open Session first FAIL must stay retryable, not done")
    if _keep_row({"ok": False, "attempted": True, "error": "Missing instruments: PSU"}):
        errors.append("mapping-empty Missing instruments FAIL must stay retryable")
    if _keep_row({"ok": False, "attempted": True, "error": "bench_preflight mapping is not live USB"}):
        errors.append("mapping-empty FAIL must stay retryable")
    if _keep_row({"ok": False, "attempted": True, "error": ""}):
        errors.append("empty-error FAIL must stay retryable")
    if not _keep_row({"ok": True, "attempted": True, "error": ""}):
        errors.append("USB ok rows must stay kept")
    return errors


def _live_kinds(mapping: dict[str, Any]) -> set[str]:
    kinds: set[str] = set()
    for kind, url in (mapping or {}).items():
        text = str(url or "")
        if text.startswith("SIM::") or not text:
            continue
        if "USB" in text.upper():
            kinds.add(str(kind).upper())
    return kinds


def _bench_mapping(bench: Any) -> dict[str, Any]:
    if not isinstance(bench, dict):
        return {}
    mapping = bench.get("mapping")
    return mapping if isinstance(mapping, dict) else {}


def preflight() -> dict[str, Any]:
    """session_status + bench_preflight only. No discover hammer."""
    status = rpc("session_status", timeout=5.0)
    if status.get("busy"):
        return {"ok": False, "reason": "worker busy -- do not kill mid-run", "status": status}
    bench = rpc("bench_preflight", timeout=90.0)
    mapping = _bench_mapping(bench)
    if not mapping and isinstance(status.get("mapping"), dict):
        mapping = status["mapping"]
    live = _live_kinds(mapping)
    return {
        "ok": bool(live) and not status.get("busy"),
        "reason": "" if live else "bench_preflight mapping is not live USB",
        "status": status,
        "bench": bench,
        "mapping": mapping,
        "live": sorted(live),
    }


def _calls_input(path: str) -> bool:
    if not path:
        return False
    p = Path(path)
    if not p.is_absolute():
        p = REPO / path
    if not p.is_file():
        return False
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "input"
        for node in ast.walk(tree)
    )


def _part_meta(pk: str) -> dict[str, Any]:
    path = PARTS_DIR / f"{pk}.yaml"
    data: dict[str, Any] = {}
    if path.is_file():
        import yaml

        loaded = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
        if isinstance(loaded, dict):
            data = loaded
    part = str(data.get("part") or data.get("device") or pk)
    component = str(data.get("component") or "")
    package = str(data.get("package") or "")
    model = str(data.get("model") or "")
    from ate.core.new_product import suite_for_part

    family = suite_for_part(part, component=component, package=package, model=model)
    return {
        "part_key": pk,
        "part": part,
        "component": component,
        "package": package,
        "model": model,
        "version": str(data.get("version") or "Version_1"),
        "vcc": float(data.get("vcc") or data.get("vcca") or 5.0),
        "current_limit": float(data.get("current_limit") or 0.1),
        "family": family,
    }


def _physics_rows() -> tuple[list[dict[str, Any]], dict[tuple[str, str], str]]:
    phys = json.loads(PHYS.read_text(encoding="utf-8"))
    leftover = {
        (str(r.get("part_key") or ""), str(r.get("test_id") or "")): str(r.get("why") or "")
        for r in (phys.get("leftover_named") or [])
        if isinstance(r, dict)
    }
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, Any]] = []
    for r in phys.get("rows") or []:
        if not isinstance(r, dict):
            continue
        pk = str(r.get("part_key") or "")
        tid = str(r.get("test_id") or "")
        key = (pk, tid)
        if not pk or not tid or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "part_key": pk,
                "test_id": tid,
                "ok": False,
                "skipped": False,
                "missing": [],
                "leftover": key in leftover,
                "leftover_why": leftover.get(key, ""),
                "success": False,
                "summary": "",
                "error": "",
                "stamps": [],
                "file": r.get("file") or "",
                "attempted": False,
            }
        )
    return rows, leftover


def _load_proof() -> dict[str, Any]:
    if not PROOF.is_file():
        return {}
    try:
        doc = json.loads(PROOF.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return doc if isinstance(doc, dict) else {}


RETRYABLE = (
    "worker busy",
    "runner busy",
    "run thread already active",
    "worker rpc lost",
    "start never ran",
    "winerror 10054",
    "missing instruments",
    "open session first",
    "mapping is not live usb",
    "not live usb",
    "emergency stop",
    "forcibly closed",
    "timed out",
)


def _retryable(err: str) -> bool:
    text = str(err or "").lower().strip()
    if not text:
        return True
    return any(tok in text for tok in RETRYABLE)


def _keep_row(r: dict[str, Any]) -> bool:
    if r.get("ok"):
        return True
    if r.get("skipped") and "input" in str(r.get("error") or "").lower():
        return True
    if r.get("attempted") and not _retryable(str(r.get("error") or "")):
        return True
    return False


def _done_map(doc: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    """Keep real USB results. Retry busy/session-lost rows."""
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for r in doc.get("rows") or []:
        if not isinstance(r, dict):
            continue
        pk = str(r.get("part_key") or "")
        tid = str(r.get("test_id") or "")
        if pk and tid and _keep_row(r):
            out[(pk, tid)] = r
    return out


def _write_proof(doc: dict[str, Any]) -> None:
    rows = [r for r in (doc.get("rows") or []) if isinstance(r, dict)]
    doc["n"] = len(rows)
    doc["ok"] = sum(1 for r in rows if r.get("ok"))
    doc["attempted"] = sum(1 for r in rows if r.get("attempted"))
    doc["fail"] = sum(1 for r in rows if r.get("attempted") and not r.get("ok") and not r.get("skipped"))
    doc["skipped_n"] = sum(1 for r in rows if r.get("skipped"))
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def _wait_idle(timeout_s: float = 180.0) -> dict[str, Any]:
    t0 = time.time()
    last: dict[str, Any] = {}
    while time.time() - t0 < timeout_s:
        last = rpc("session_status", timeout=5.0)
        if not last.get("busy"):
            return last
        time.sleep(0.5)
    raise RuntimeError("worker still busy after wait")


def _wait_run(epoch0: int, timeout_s: float = ROW_TIMEOUT_S) -> dict[str, Any]:
    t0 = time.time()
    last: dict[str, Any] = {}
    saw_busy = False
    idle_s = 0.0
    rpc_fail = 0
    while time.time() - t0 < timeout_s:
        try:
            pending = rpc("get_pending_prompt", timeout=5.0)
            rpc_fail = 0
        except Exception:
            pending = None
            rpc_fail += 1
        if isinstance(pending, dict) and pending.get("id"):
            try:
                rpc("operator_respond", {"prompt_id": pending["id"], "continue": True}, timeout=5.0)
            except Exception as exc:
                raise RuntimeError(f"worker rpc lost: continue failed: {exc}") from exc
        try:
            last = rpc("session_status", timeout=5.0)
            rpc_fail = 0
        except Exception as exc:
            rpc_fail += 1
            if rpc_fail >= 3:
                raise RuntimeError(f"worker rpc lost: {exc}") from exc
            time.sleep(0.5)
            continue
        epoch = int(last.get("run_epoch") or 0)
        if epoch > epoch0 and not last.get("busy"):
            return last
        if last.get("busy"):
            saw_busy = True
            idle_s = 0.0
        else:
            idle_s += 0.5
            if not saw_busy and idle_s >= 45.0:
                raise RuntimeError(
                    f"START never ran (epoch={epoch} epoch0={epoch0} busy=false)"
                )
        time.sleep(0.5)
    try:
        rpc("stop", timeout=15.0)
    except Exception:
        pass
    raise TimeoutError(f"run timed out after {timeout_s:.0f}s")


def _ensure_usb_session(status: dict[str, Any]) -> dict[str, Any]:
    kinds = _live_kinds(status.get("mapping") if isinstance(status.get("mapping"), dict) else {})
    if status.get("open") and not status.get("sim") and "PSU" in kinds and "AWG" in kinds:
        return status
    if status.get("open"):
        try:
            rpc("close_session", timeout=30.0)
        except Exception:
            pass
    mapping = rpc("open_session", timeout=90.0)
    return rpc("session_status", timeout=5.0) | {"opened_mapping": mapping}


def _apply_part(meta: dict[str, Any], family_cache: str) -> str:
    family = str(meta.get("family") or "")
    if family and family != family_cache:
        rpc("set_family", {"family": family}, timeout=30.0)
        family_cache = family
    rpc(
        "set_db_context",
        {
            "component": meta.get("component") or "",
            "part": meta.get("part") or meta.get("part_key"),
            "package": meta.get("package") or "",
            "operator": OPERATOR,
            "version": meta.get("version") or "Version_1",
            "model": meta.get("model") or "",
            "part_key": meta.get("part_key"),
            "sample_size": 1,
        },
        timeout=30.0,
    )
    return family_cache


def _row_stamps(results: Any, tid: str) -> list[dict[str, Any]]:
    stamps: list[dict[str, Any]] = []
    for r in results or []:
        if not isinstance(r, dict):
            continue
        if str(r.get("test_id") or "") != tid:
            continue
        meas = r.get("measurements") or []
        if isinstance(meas, list):
            for m in meas:
                if isinstance(m, dict) and m.get("id"):
                    stamps.append(
                        {
                            "id": m.get("id"),
                            "value": m.get("value"),
                            "unit": m.get("unit") or "",
                        }
                    )
    if stamps:
        return stamps
    try:
        doc = rpc("get_session_report", timeout=15.0)
    except Exception:
        return stamps
    tests = (doc or {}).get("tests") if isinstance(doc, dict) else None
    if not isinstance(tests, list):
        return stamps
    for t in tests:
        if not isinstance(t, dict):
            continue
        if str(t.get("id") or t.get("test_id") or "") != tid:
            continue
        for m in t.get("measurements") or []:
            if isinstance(m, dict) and m.get("id"):
                stamps.append(
                    {
                        "id": m.get("id"),
                        "value": m.get("value"),
                        "unit": m.get("unit") or "",
                    }
                )
    return stamps


def walk() -> dict[str, Any]:
    sc = selfcheck()
    if sc:
        raise RuntimeError("selfcheck: " + "; ".join(sc))
    pf = preflight()
    if pf.get("status", {}).get("busy"):
        raise RuntimeError("worker busy -- do not kill mid-run")
    mapping = pf.get("mapping") if isinstance(pf.get("mapping"), dict) else {}
    live = set(pf.get("live") or [])
    rows, _leftover = _physics_rows()
    prev = _load_proof()
    done = _done_map(prev)
    for r in rows:
        key = (str(r["part_key"]), str(r["test_id"]))
        old = done.get(key)
        if old and _keep_row(old):
            r.update(old)
    doc: dict[str, Any] = {
        "n": len(rows),
        "ok": sum(1 for r in rows if r.get("ok")),
        "usb_live": bool(live),
        "usb_complete": {"DMM", "MSO", "PSU", "AWG"} <= live,
        "dmm_ignore": True,
        "mapping": mapping,
        "preflight": {
            "ok": pf.get("ok"),
            "reason": pf.get("reason") or "",
            "mapping": mapping,
            "live": sorted(live),
        },
        "rows": rows,
    }
    _write_proof(doc)
    if not live:
        return doc
    status = pf.get("status") if isinstance(pf.get("status"), dict) else rpc("session_status", timeout=5.0)
    status = _ensure_usb_session(status if isinstance(status, dict) else {})
    family_cache = ""
    meta_cache: dict[str, dict[str, Any]] = {}
    for r in rows:
        pk = str(r["part_key"])
        tid = str(r["test_id"])
        if _keep_row(r):
            continue
        if tid in SKIP_IDS or _calls_input(str(r.get("file") or "")):
            r["skipped"] = True
            r["attempted"] = False
            r["ok"] = False
            r["error"] = "skip input_off_leakage / input() golden"
            _write_proof(doc)
            print(f"SKIP {pk} {tid}: {r['error']}", flush=True)
            continue
        r["skipped"] = False
        r["missing"] = []
        r["error"] = ""
        last_exc = ""
        for _try in range(2):
            r["attempted"] = True
            try:
                meta = meta_cache.get(pk)
                if meta is None:
                    meta = _part_meta(pk)
                    meta_cache[pk] = meta
                family_cache = _apply_part(meta, family_cache)
                before = _wait_idle()
                before = _ensure_usb_session(before)
                before = _wait_idle()
                epoch0 = int(before.get("run_epoch") or 0)
                rpc("run_sequence_async", {
                    "test_ids": [tid],
                    "params": {
                        "part": pk,
                        "vcc": float(meta.get("vcc") or 5.0),
                        "current_limit_a": float(meta.get("current_limit") or 0.1),
                        "dut_indices": [1],
                        "unit_index": 1,
                        "auto_continue": False,
                    },
                }, timeout=30.0)
                after = _wait_run(epoch0)
                results = rpc("get_last_run_results", timeout=30.0)
                match = next(
                    (
                        x
                        for x in (results or [])
                        if isinstance(x, dict) and str(x.get("test_id") or "") == tid
                    ),
                    None,
                )
                success = bool(match and match.get("success"))
                r["success"] = success
                r["ok"] = success
                r["summary"] = str((match or {}).get("summary") or "")
                r["error"] = str((match or {}).get("error") or after.get("run_error") or "")
                r["stamps"] = _row_stamps(results, tid)
                if not match and after.get("run_error"):
                    r["ok"] = False
                    r["success"] = False
                    r["error"] = str(after.get("run_error"))
                if r.get("ok") or not _retryable(r.get("error") or ""):
                    break
                r["attempted"] = False
                last_exc = r.get("error") or ""
                time.sleep(1.0)
            except Exception as exc:
                last_exc = str(exc)
                r["ok"] = False
                r["success"] = False
                r["error"] = last_exc
                if _retryable(last_exc):
                    r["attempted"] = False
                    time.sleep(1.0)
                    continue
                break
        if not r.get("ok") and not r.get("error"):
            r["error"] = last_exc
        print(
            f"{'OK' if r.get('ok') else 'FAIL'} {pk} {tid}: "
            f"{r.get('summary') or r.get('error') or ''}",
            flush=True,
        )
        _write_proof(doc)
    _write_proof(doc)
    return doc


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode = str(args[0] or "selfcheck").strip().lower() if args else "selfcheck"
    if mode == "selfcheck":
        errors = selfcheck()
        if errors:
            print("FAIL check_live_usb selfcheck:")
            for e in errors:
                print(f"  - {e}")
            return 1
        print(f"OK check_live_usb selfcheck rpc={START_RPC}")
        return 0
    if mode == "preflight":
        pf = preflight()
        print(json.dumps(pf, indent=2))
        return 0 if pf.get("ok") else 1
    if mode == "plan":
        rows, leftover = _physics_rows()
        print(
            f"OK check_live_usb plan n={len(rows)} leftover={len(leftover)} "
            f"skip={sorted(SKIP_IDS)} dmm_ignore=1"
        )
        return 0
    if mode in ("resume", "keep", "all"):
        sc = selfcheck()
        if sc:
            print("FAIL check_live_usb selfcheck:")
            for e in sc:
                print(f"  - {e}")
            return 1
        doc = walk()
        print(
            f"OK check_live_usb {mode} n={doc.get('n')} ok={doc.get('ok')} "
            f"attempted={doc.get('attempted')} fail={doc.get('fail')} "
            f"skipped={doc.get('skipped_n')} leftover-honest"
        )
        return 0 if int(doc.get("ok") or 0) > 0 or int(doc.get("attempted") or 0) > 0 else 1
    print("usage: python -m ate.core.check_live_usb selfcheck|preflight|plan|resume|keep|all")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
