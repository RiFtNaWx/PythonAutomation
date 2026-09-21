"""JSON-RPC worker for Tauri UI — hidden pythonw process."""
from __future__ import annotations

import json
import socketserver
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

# Ensure repo root on path
_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from ate.core.paths import JSONRPC_HOST, JSONRPC_PORT
from ate.core.registry import active_family, all_tests, family_labels, known_families, refresh_family_table
from ate.core.runner import ATECore, RunParams

WORKER_VERSION = "0.2.41"


def _merged_test_params(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    from ate.core.database import _clean_test_param_block, load_test_params

    disk = load_test_params()
    out: dict[str, dict[str, Any]] = {}
    for key, block in (disk.get("tests") or {}).items():
        if isinstance(block, dict):
            out[str(key).lower()] = dict(block)
    incoming = payload.get("test_params")
    if isinstance(incoming, dict):
        rows = incoming.get("tests") if isinstance(incoming.get("tests"), dict) else incoming
        if isinstance(rows, dict):
            for key, block in rows.items():
                tid = str(key or "").strip().lower()
                if not tid:
                    continue
                cleaned = _clean_test_param_block(block)
                if not cleaned:
                    continue
                prev = dict(out.get(tid) or {})
                prev.update(cleaned)
                out[tid] = prev
    return out


class _State:
    core: ATECore | None = None
    event_subscribers: list = []
    lock = threading.Lock()
    core_lock = threading.Lock()
    run_thread: threading.Thread | None = None


def _build_run_params(params: dict[str, Any]) -> RunParams:
    from ate.core.database import get_context
    from ate.core.param_defaults import resolve_gain_profile, noninv_gain
    from dataclasses import replace as dc_replace

    ctx = get_context()
    p = params or {}
    duts_raw = p.get("dut_indices")
    dut_indices: list[int] = []
    if isinstance(duts_raw, list) and duts_raw:
        dut_indices = [int(x) for x in duts_raw]
    part = str(p.get("part_key") or p.get("part") or ctx.part_key or "").strip().lower()
    gain_profile = str(p.get("gain_profile") or "default")
    run_label = str(p.get("run_label") or "").strip()
    raw_vccb = p.get("vccb")
    vccb = float(raw_vccb) if raw_vccb not in (None, "") else None
    rp = RunParams(
        vcc=float(p.get("vcc", 5.0)),
        freq_hz=float(p.get("freq_hz", 500.0)),
        amp_vpp=float(p.get("amp_vpp", 0.004)),
        n_repeats=int(p.get("n_repeats", 3)),
        lab_report=str(
            __import__(
                "ate.tests.logic.excel_lock",
                fromlist=["coerce_golden_auto_lab_report"],
            ).coerce_golden_auto_lab_report(
                ctx, str(p.get("lab_report") or ctx.lab_report_path())
            )
        ),
        research_excel=str(p.get("research_excel") or ""),
        reset_before_run=bool(p.get("reset_before_run", False)),
        unit_index=int(p.get("unit_index", 1)),
        dut_indices=dut_indices,
        part=part,
        channel=str(p.get("channel") or "CHA").upper(),
        channels=[
            str(c).upper()
            for c in (p.get("channels") or [])
            if str(c).strip()
        ],
        walk_order=str(p.get("walk_order") or "channel"),
        run_label=run_label,
        gain_profile=gain_profile,
        current_limit_a=float(p.get("current_limit_a", 0.10)),
        vccb=vccb,
        auto_continue=bool(p.get("auto_continue")),
        vcc_start=float(p.get("vcc_start", 0.0) or 0.0),
        vcc_stop=float(p.get("vcc_stop", 5.0) if p.get("vcc_stop") not in (None, "") else 5.0),
        vcc_step=float(p.get("vcc_step", 0.5) or 0.5),
        freq_start=float(p.get("freq_start", 1.0) or 1.0),
        freq_stop=float(p.get("freq_stop", 10.0) if p.get("freq_stop") not in (None, "") else 10.0),
        freq_step=float(p.get("freq_step", 4.0) or 4.0),
        test_params=_merged_test_params(p),
    )
    ids_hint = list(p.get("test_ids") or [])
    if "gbw" in ids_hint:
        prof = resolve_gain_profile("G11", gain_profile, part)
        if prof.get("gain") is not None:
            rp = dc_replace(
                rp,
                gain=float(prof["gain"]),
                rf=str(prof.get("rf") or ""),
                ri=str(prof.get("ri") or ""),
            )
        if not rp.run_label and prof.get("label"):
            rp = dc_replace(rp, run_label=str(prof["label"]))
    if p.get("rf") and p.get("ri"):
        rp = dc_replace(
            rp,
            rf=str(p.get("rf")),
            ri=str(p.get("ri")),
            gain=float(noninv_gain(str(p.get("rf")), str(p.get("ri")))),
        )
    if not rp.research_excel:
        from ate.core.paths import RESEARCH_EXCEL_PATH

        rp.research_excel = str(RESEARCH_EXCEL_PATH)
    return rp


def _pin_run_campaign(p: dict[str, Any]) -> None:
    """Bind worker campaign to START payload before instruments run. PIC cannot steal."""
    op = str((p or {}).get("operator") or "").strip()
    if not op:
        return
    from ate.core.database import set_context

    set_context(
        component=(p or {}).get("component"),
        part=(p or {}).get("part"),
        package=(p or {}).get("package"),
        operator=op,
        version=(p or {}).get("version"),
        model=(p or {}).get("model"),
        part_key=(p or {}).get("part_key"),
        year=(p or {}).get("year"),
    )


def _session_bound_ctx(p: dict[str, Any] | None = None):
    """Excel/STS writes follow START folder. UI payload wins if the SKU differs."""
    from ate.core.database import context_from_identity, get_context, last_session_identity

    payload = p or {}
    ident = last_session_identity()
    op = str(payload.get("operator") or "").strip()
    if op:
        _pin_run_campaign(payload)
        same_part = str(ident.get("part") or "").strip().lower() == str(
            payload.get("part") or ""
        ).strip().lower()
        same_op = str(ident.get("operator") or "").strip().lower() == op.lower()
        if ident.get("part") and same_part and same_op:
            return context_from_identity(ident)
        return get_context()
    if ident.get("part"):
        return context_from_identity(ident)
    return get_context()


def _run_sequence_worker(ids: list[str], rp: RunParams) -> None:
    core = _core()
    try:
        core.run_sequence(ids, rp)
    except Exception as exc:
        _emit(
            {
                "type": "log",
                "payload": {"text": f"Run failed: {exc}\n", "level": "error"},
            }
        )


def _emit(event: dict) -> None:
    # Events are polled via get_events; keep a ring buffer
    with _State.lock:
        _State.event_subscribers.append(event)
        if len(_State.event_subscribers) > 500:
            _State.event_subscribers = _State.event_subscribers[-300:]


def _core() -> ATECore:
    with _State.core_lock:
        if _State.core is None:
            _State.core = ATECore(emit=_emit)
        return _State.core


def dispatch(method: str, params: dict[str, Any]) -> Any:
    # ping must not wait for ATECore / load_family / OneDrive mkdir
    if method == "ping":
        from ate.core.paths import TEST_DB_ROOT, cloud_kind

        return {
            "ok": True,
            "version": WORKER_VERSION,
            "ready": _State.core is not None,
            "test_database_root": str(TEST_DB_ROOT),
            "cloud_kind": cloud_kind(TEST_DB_ROOT),
        }

    core = _core()

    if method == "sync_repo":
        if core.busy:
            return {"action": "busy", "message": "A run is in progress. Update skipped."}
        from ate.core.sync_repo import run_sync

        return run_sync(force=bool(params.get("force")))

    if method == "get_family":
        return {
            "family": core.family or active_family() or "opamp",
            "known": known_families(),
            "labels": family_labels(),
            "default": "opamp",
        }

    if method == "list_owners":
        from ate.core.database import load_owners

        return {"owners": load_owners()}

    if method == "upsert_owner":
        from ate.core.database import upsert_owner

        return upsert_owner(
            label=str(params.get("label") or params.get("operator") or ""),
            owner_id=str(params.get("id") or params.get("owner_id") or ""),
            default_family=str(params.get("default_family") or params.get("family") or ""),
            default_part=str(params.get("default_part") or params.get("part") or ""),
            default_component=str(params.get("default_component") or params.get("component") or ""),
            default_package=str(params.get("default_package") or params.get("package") or ""),
            task=str(params.get("task") or params.get("part") or ""),
            parts=list(params.get("parts") or []) if isinstance(params.get("parts"), list) else None,
            update_defaults=bool(params.get("update_defaults", True)),
        )

    if method == "remove_owner":
        from ate.core.database import remove_owner

        return remove_owner(
            str(params.get("owner") or params.get("label") or params.get("id") or ""),
            confirm_text=str(params.get("confirm_text") or params.get("phrase") or ""),
            delete_folders=bool(params.get("delete_folders") or params.get("wipe")),
        )

    if method == "assign_owner_products":
        from ate.core.new_product import assign_owner_products

        parts = params.get("parts") or params.get("codes") or []
        unassign = params.get("unassign") or []
        if not isinstance(parts, list):
            parts = []
        if not isinstance(unassign, list):
            unassign = []
        return assign_owner_products(
            label=str(params.get("label") or params.get("operator") or ""),
            parts=list(parts),
            unassign=list(unassign),
            replace_parts=bool(params.get("replace_parts", False)),
            sample_size=int(params.get("sample_size") or 4),
        )

    if method == "provision_operator":
        from ate.core.provision_operator import provision_operator

        only = params.get("only_parts") or params.get("parts") or []
        if not isinstance(only, list):
            only = []
        only_skus = params.get("only_skus") or []
        if not isinstance(only_skus, list):
            only_skus = []
        return provision_operator(
            str(params.get("label") or params.get("operator") or ""),
            with_workbook=bool(params.get("with_workbook", True)),
            force_workbook=bool(params.get("force_workbook", False)),
            dry_run=bool(params.get("dry_run", False)),
            sample_size=int(params.get("sample_size") or 4),
            only_parts=list(only) if only else None,
            only_skus=list(only_skus) if only_skus else None,
            all_skus=bool(params.get("all_skus")),
        )

    if method == "set_family":
        if core.busy:
            raise RuntimeError("Runner busy — wait for run to finish")
        fam = str(params.get("family") or "").strip().lower() or None
        loaded = core.load_family(fam)
        return {"family": loaded, "test_count": len(all_tests())}

    if method == "list_tests":
        from ate.core.timeline import short_test_tag
        from ate.core.specs import apply_version_spec_overlay, load_part_specs, test_info_map

        specs = list(all_tests())
        from ate.core.database import get_context, load_test_params
        from ate.core.param_defaults import catalog_for_ui
        from ate.fixture.modes import enabled_tests_for_part

        ctx = get_context()
        defaults = {
            "logic": "rs29511",
            "lim": "rs2323",
            "switch": "rs2323",
            "power": "rs3213",
            "opamp": "rs622",
            "level": "rs0204",
        }
        pk = str(ctx.part_key or "") or defaults.get(core.family or "", "")
        enabled = enabled_tests_for_part(pk, catalog=ctx.load_test_catalog()) if pk else None
        if enabled is not None:
            allow = set(enabled)
            filtered = [t for t in specs if t.id in allow]
            if filtered:
                specs = filtered
            elif not allow:
                specs = []
            else:
                fallback = defaults.get(core.family or "", "")
                if fallback and fallback != pk:
                    enabled2 = enabled_tests_for_part(fallback)
                    if enabled2:
                        allow2 = set(enabled2)
                        specs = [t for t in specs if t.id in allow2]
        info_map = test_info_map(pk)
        part_specs = apply_version_spec_overlay(load_part_specs(pk))
        from ate.core.stimulus import for_test as stimulus_for
        from ate.core.test_detect import source_for_spec

        fam = str(core.family or "")
        cat = catalog_for_ui(pk, fam)
        saved = (load_test_params(ctx).get("tests") or {})
        from ate.core.param_defaults import coerce_screenshot_from

        out = []
        for t in specs:
            source = source_for_spec(t)
            defaults_row = dict((cat.get("tests") or {}).get(t.id) or {})
            overlay = dict(saved.get(str(t.id).lower()) or {})
            merged = {**defaults_row, **overlay}
            shot_def = coerce_screenshot_from("", t.required_instruments)
            defaults_row.setdefault("screenshot_from", shot_def)
            merged["screenshot_from"] = coerce_screenshot_from(
                merged.get("screenshot_from"), t.required_instruments
            )
            spec_rows = [
                s
                for s in part_specs
                if str(s.get("test") or "").lower() == t.id.lower()
                or str(s.get("id") or "").lower() == t.id.lower()
            ]
            if overlay.get("specs"):
                spec_rows = apply_version_spec_overlay(spec_rows)
            out.append(
                {
                    "id": t.id,
                    "label": t.label,
                    "short_tag": short_test_tag(t),
                    "fixture_mode": t.fixture_mode,
                    "lab_sheet": t.lab_sheet,
                    "required_instruments": sorted(t.required_instruments),
                    "notes": t.notes,
                    "stimulus": stimulus_for(t.id, family=fam, part=pk),
                    "fixed_steps": list(t.fixed_steps) if t.fixed_steps else [],
                    "dual_channel": bool(getattr(t, "dual_channel", True)),
                    "specs": spec_rows,
                    "info": info_map.get(t.id) or {},
                    "source": source,
                    "defaults": defaults_row,
                    "params": merged,
                }
            )
        return out

    if method == "list_fixture_modes":
        from ate.core.database import get_context

        ctx = get_context()
        part = str(params.get("part") or ctx.part_key or "").strip()
        if core.family == "opamp":
            from ate.fixture.modes import catalog_for_ui

            return catalog_for_ui(part)
        if core.family in ("logic", "level"):
            from ate.fixture.modes import logic_catalog_for_ui

            level_default = "rs0204" if core.family == "level" else "rs29511"
            return logic_catalog_for_ui(part if part != "rs622" else level_default)
        if core.family in ("lim", "switch"):
            from ate.fixture.modes import logic_catalog_for_ui

            return logic_catalog_for_ui(part if part not in ("rs622", "") else "rs2323")
        if core.family == "power":
            from ate.fixture.modes import logic_catalog_for_ui

            return logic_catalog_for_ui(part if part not in ("rs622", "") else "rs3213")
        return []

    if method == "list_db_tree":
        from ate.core.database import list_tree
        from ate.core.paths import TEST_DB_ROOT

        try:
            return list_tree()
        except Exception as exc:
            return {
                "root": str(TEST_DB_ROOT),
                "components": {},
                "error": str(exc),
            }

    if method == "get_db_context":
        from ate.core.database import get_context, how_to_use, list_test_folders

        ctx = get_context()
        return {
            "context": ctx.identity(),
            "tests": list_test_folders(ctx),
            "guide": how_to_use(),
        }

    if method == "set_db_context":
        from ate.core.database import get_context, list_test_folders, remember_operator, set_context
        from ate.core.paths import sync_defaults_from_context

        if core.busy:
            ctx = get_context()
            return {
                "context": ctx.identity(),
                "tests": list_test_folders(ctx),
                "created": [],
                "family": core.family,
                "test_count": len(all_tests()),
                "busy_locked": True,
                "family_error": "Runner busy -- campaign locked until the run finishes",
            }

        op_raw = str(params.get("operator") or "").strip()
        if op_raw:
            remember_operator(
                op_raw,
                component=str(params.get("component") or ""),
                part=str(params.get("part") or ""),
                package=str(params.get("package") or ""),
            )
        ctx = set_context(
            component=params.get("component"),
            part=params.get("part"),
            package=params.get("package"),
            operator=params.get("operator"),
            version=params.get("version"),
            model=params.get("model"),
            part_key=params.get("part_key"),
            year=params.get("year"),
            sample_size=params.get("sample_size"),
        )
        sync_defaults_from_context()
        from ate.core.new_product import suite_for_part

        wanted = suite_for_part(
            ctx.part,
            component=ctx.component,
            package=ctx.package,
            model=ctx.model,
        )
        family = core.family
        family_error = ""
        if wanted and wanted != family:
            if core.busy:
                family_error = "Runner busy — campaign saved; switch family after the run"
            else:
                try:
                    family = core.load_family(wanted)
                except ValueError as exc:
                    family_error = str(exc)
        elif not wanted:
            if core.busy:
                family_error = "Runner busy — campaign saved; switch family after the run"
            else:
                family = core.load_family("")
                family_error = "RUN-IC class has no ATE suite yet; empty test list"
        out = {
            "context": ctx.identity(),
            "tests": list_test_folders(ctx),
            "created": ctx.ensure_tree(),
            "family": family,
            "test_count": len(all_tests()),
        }
        if family_error:
            out["family_error"] = family_error
        return out

    if method == "db_how_to":
        from ate.core.database import how_to_use

        return how_to_use()

    if method == "open_db_root":
        from ate.core.database import get_context
        import os

        folder = get_context().root()
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))
        return {"folder": str(folder)}

    if method == "cloud_db_status":
        from ate.core.paths import cloud_db_status

        return cloud_db_status()

    if method == "pick_cloud_db":
        from ate.core.paths import apply_test_db_root, descend_to_campaign, pick_test_db_folder, cloud_db_status

        raw = str(params.get("path") or "").strip()
        if raw:
            chosen = Path(raw)
            if not chosen.is_dir():
                raise FileNotFoundError(f"Folder not found: {raw}")
            chosen = descend_to_campaign(chosen)
        else:
            chosen = pick_test_db_folder()
            if chosen is None:
                return {"cancelled": True, **cloud_db_status()}
        root = apply_test_db_root(chosen)
        return {"folder": str(root), "cancelled": False, **cloud_db_status()}

    if method == "open_central_db":
        from ate.core.paths import cloud_kind, load_test_db_root, sharepoint_url
        import os

        root = load_test_db_root()
        if root.is_dir():
            os.startfile(str(root))
            return {"folder": str(root), "cloud_kind": cloud_kind(root), "missing": False}
        url = sharepoint_url()
        if url:
            os.startfile(url)
            return {
                "folder": str(root),
                "opened": "sharepoint_url",
                "url": url,
                "missing": True,
                "note": "Local sync folder missing. Opened SharePoint in the browser. Setup -> Choose folder to pick the OneDrive #Test_Database (or any save folder).",
            }
        return {
            "folder": str(root),
            "missing": True,
            "note": "Central #Test_Database is not on this PC. Setup -> Choose folder and pick the OneDrive shortcut (or a local save folder). Console stays open.",
        }

    if method == "open_golden_bank":
        from ate.core.paths import REPO_ROOT
        import os

        gold = (REPO_ROOT / "goldens").resolve()
        if not gold.is_dir():
            raise FileNotFoundError("goldens/ missing -- run python -m ate.core.golden_gateway --import")
        raw = str(params.get("file") or params.get("path") or "").strip()
        target = gold
        if raw:
            p = Path(raw)
            if not p.is_absolute():
                p = REPO_ROOT / raw
            try:
                resolved = p.resolve()
                if (gold == resolved or gold in resolved.parents) and (
                    resolved.is_file() or resolved.is_dir()
                ):
                    target = resolved
            except OSError:
                target = gold
        os.startfile(str(target))
        return {
            "folder": str(gold),
            "opened": str(target),
            "guide": str(gold / "GUIDE.md"),
            "index": str(gold / "INDEX.md"),
            "tutorial": str(gold / "TUTORIAL.md"),
        }

    if method == "open_path":
        from ate.core.datalog import _safe_session_json
        from ate.core.paths import TEST_DB_ROOT
        import os

        raw = str(params.get("path") or "").strip()
        if not raw:
            raise ValueError("path required")
        p = Path(raw)
        if p.is_dir():
            root = TEST_DB_ROOT.resolve()
            resolved = p.resolve()
            if root not in resolved.parents and resolved != root:
                raise PermissionError("path is outside #Test_Database")
            os.startfile(str(resolved))
            return {"folder": str(resolved)}
        target = _safe_session_json(p, TEST_DB_ROOT)
        os.startfile(str(target))
        return {"path": str(target)}

    if method == "open_sessions":
        from ate.core.database import get_context
        import os

        folder = get_context().sessions_dir()
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))
        return {"folder": str(folder)}

    if method == "import_workbook":
        from ate.core.workbook_import import import_workbook

        return import_workbook(
            source_path=str(params.get("source_path") or params.get("path") or ""),
            dest_name=str(params.get("dest_name") or ""),
            pick=bool(params.get("pick")),
        )

    if method == "import_family":
        from ate.core.family_ingest import import_family

        result = import_family(
            source=str(params.get("source") or params.get("url") or params.get("source_url") or ""),
            family=str(params.get("family") or params.get("family_key") or ""),
            local_path=str(params.get("local_path") or params.get("path") or ""),
        )
        fam = str(result.get("family") or "").strip()
        if fam and not core.busy:
            try:
                loaded = core.load_family(fam)
                result["loaded_family"] = loaded
                result["test_count"] = len(all_tests())
            except Exception as exc:
                result["load_error"] = str(exc)
        elif fam and core.busy:
            result["load_error"] = "Runner busy — family files written; switch family after the run"
        return result

    if method == "reload_families":
        known = sorted(refresh_family_table())
        return {
            "ok": True,
            "known": known,
            "family": core.family or active_family() or "opamp",
            "restart_hint": "If a new family is missing, run restart_ate_app.bat (ports 8766/5174; leave 8765).",
        }

    if method == "discover":
        return core.discover()

    if method == "bench_preflight":
        return core.bench_preflight()

    if method == "open_session":
        return core.open_session(sim=bool(params.get("sim")))

    if method == "close_session":
        core.close_session()
        return {"ok": True}

    if method == "session_status":
        from ate.core.database import current_session, get_context

        status = {
            "open": core.session_open,
            "mapping": core.mapping,
            "busy": core.busy,
            "sim": core.simulated,
            "visa_backend": core.visa_backend,
            "run_error": core.last_run_error,
            "run_epoch": core.run_epoch,
            "db": get_context().identity(),
            "run_session": current_session(),
            "timeline": core.timeline_snapshot(),
        }
        if core.simulated:
            from ate.instruments.sim import bus_snapshot

            status["sim_bus"] = bus_snapshot()
        try:
            from ate.instruments.discovery import last_usb_map, pnp_present

            status["usb"] = last_usb_map()
            status["pnp"] = pnp_present()
        except Exception:
            status["usb"] = {}
            status["pnp"] = {}
        return status

    if method == "get_timeline":
        return core.timeline_snapshot()

    if method == "screenshot":
        path = core.capture_screenshot(
            prefix=params.get("prefix", "manual"),
            test_key=str(params.get("test_key") or "ORT"),
        )
        return {"path": path}

    if method == "open_screenshots":
        from ate.core.database import get_context
        from ate.reporting.lab_report import ensure_screenshot_dir
        import os

        ctx = get_context()
        unit = params.get("unit_index")
        test_key = str(params.get("test_key") or "ORT")
        dut = int(unit) if unit is not None else None
        folder = ensure_screenshot_dir(test_key, dut)
        os.startfile(str(folder))
        return {"folder": str(folder), "db": ctx.identity()}

    if method == "list_param_defaults":
        from ate.core.database import get_context
        from ate.core.param_defaults import catalog_for_ui

        ctx = get_context()
        part = str(params.get("part") or ctx.part_key or "").strip()
        family = str(params.get("family") or core.family or active_family() or "opamp")
        return catalog_for_ui(part, family=family)

    if method == "run_sequence":
        ids = list(params.get("test_ids") or [])
        p = params.get("params") or {}
        _pin_run_campaign(p)
        rp = _build_run_params({**p, "test_ids": ids})
        results = core.run_sequence(ids, rp)
        return [
            {
                "test_id": r.test_id,
                "success": r.success,
                "summary": r.summary,
                "error": r.error,
                "dut": r.dut,
                "channel": r.channel,
                "fixture_mode": r.fixture_mode,
            }
            for r in results
        ]

    if method == "run_sequence_async":
        ids = list(params.get("test_ids") or [])
        p = params.get("params") or {}
        if core.busy:
            raise RuntimeError("Runner busy")
        with _State.lock:
            if _State.run_thread and _State.run_thread.is_alive():
                raise RuntimeError("Run thread already active")
            core.claim_async_run()
            try:
                _pin_run_campaign(p)
                rp = _build_run_params({**p, "test_ids": ids})
            except Exception:
                with core._lock:
                    core._busy = False
                    core._async_claimed = False
                raise
            _State.run_thread = threading.Thread(
                target=_run_sequence_worker,
                args=(ids, rp),
                daemon=True,
            )
            try:
                _State.run_thread.start()
            except Exception:
                with core._lock:
                    core._busy = False
                    core._async_claimed = False
                raise
        return {"ok": True, "started": True}

    if method == "get_last_run_results":
        return core.last_run_results()
    if method == "operator_respond":
        core.operator_respond(params)
        return {"ok": True}

    if method == "operator_force_continue":
        pending = core.pending_operator()
        if not pending:
            return {"ok": False, "reason": "no_pending"}
        core.operator_respond({"prompt_id": pending["id"], "continue": True})
        return {"ok": True, "prompt_id": pending["id"]}

    if method == "get_pending_prompt":
        return core.pending_operator()

    if method == "get_events":
        with _State.lock:
            ev = list(_State.event_subscribers)
            _State.event_subscribers.clear()
        # Re-attach pending prompt so UI recovers after refresh / drained events
        pending = core.pending_operator()
        if pending and not any(e.get("type") == "operator_prompt" for e in ev):
            ev.append({"type": "operator_prompt", "payload": pending})
        return ev

    if method == "stop":
        core.request_cancel()
        core.emergency_cleanup()
        return {"ok": True, "stopped": True}

    if method == "emergency_cleanup":
        core.request_cancel()
        core.emergency_cleanup()
        return {"ok": True}

    if method == "layout_preview":
        from ate.reporting.photo_layout import layout_preview

        key = params.get("test_key")
        return layout_preview(str(key) if key else None)

    if method == "save_photo_layout":
        from ate.reporting.photo_layout import save_photo_anchors

        photos = params.get("photos") or {}
        if not isinstance(photos, dict):
            raise ValueError("photos must be a map of key -> Excel cell")
        return save_photo_anchors(str(params.get("test_key") or ""), photos)

    if method == "mapped_coverage":
        from ate.core.check_mapped_tests import coverage_payload

        return coverage_payload(core.mapping)

    if method == "list_categories":
        from ate.core.new_product import load_categories

        return {"categories": load_categories(), "source": "https://en.run-ic.com/"}

    if method == "list_inventory":
        from ate.core.new_product import load_inventory

        return {"parts": load_inventory()}

    if method == "ensure_product":
        from ate.core.new_product import ensure_product

        result = ensure_product(
            category_id=str(params.get("category") or params.get("category_id") or "opamp"),
            part=str(params.get("part") or ""),
            package=str(params.get("package") or "SOT23"),
            model=str(params.get("model") or ""),
            sample_size=int(params.get("sample_size") or 4),
            operator=str(params.get("operator") or ""),
            open_folder=bool(params.get("open_folder", True)),
            apply=True,
        )
        fam = str(result.get("family") or "")
        if fam and result.get("live") and not core.busy:
            try:
                loaded = core.load_family(fam)
                result["loaded_family"] = loaded
                result["test_count"] = len(all_tests())
            except Exception as exc:
                result["family_error"] = str(exc)
        return result

    if method == "run_demo":
        if core.busy:
            raise RuntimeError("Runner busy — wait for run to finish")
        from ate.core.new_product import run_demo

        ids = list(params.get("test_ids") or [])
        p = params.get("params") or {}
        return run_demo(ids, p)

    if method == "list_detected_tests":
        from ate.core.database import get_context
        from ate.core.test_detect import list_detected_tests

        fam = str(params.get("family") or core.family or "").strip() or None
        ctx = get_context()
        return list_detected_tests(
            family=fam,
            operator=str(params.get("operator") or ctx.operator or ""),
            product=str(params.get("product") or ""),
            author=str(params.get("author") or ""),
            allow_others=bool(params.get("allow_others")),
        )

    if method == "snippet_source":
        from ate.core.test_detect import read_snippet_source

        return read_snippet_source(
            file=str(params.get("file") or ""),
            fn=str(params.get("fn") or ""),
        )

    if method == "save_snippet_source":
        from ate.core.database import get_context
        from ate.core.test_detect import save_snippet_source

        ctx = get_context()
        return save_snippet_source(
            file=str(params.get("file") or ""),
            text=str(params.get("text") or ""),
            operator=str(params.get("operator") or ctx.operator or ""),
            allow_others=bool(params.get("allow_others")),
        )

    if method == "cursor_prompt":
        from ate.core.ate_prompt import fill_prompt
        from ate.core.database import get_context

        ctx = get_context()
        return {
            "ok": True,
            "text": fill_prompt(
                path=str(params.get("path") or "b"),
                operator=str(params.get("operator") or ctx.operator or ""),
                family=str(params.get("family") or core.family or "logic"),
                part=str(params.get("part") or ctx.part or ""),
                package=str(params.get("package") or ctx.package or ""),
                version=str(params.get("version") or ctx.version or "Version_1"),
                test_id=str(params.get("test_id") or ""),
            ),
        }

    if method == "path_b_template":
        from ate.core.test_detect import path_b_template

        return path_b_template(
            test_id=str(params.get("test_id") or params.get("id") or ""),
            label=str(params.get("label") or ""),
            family=str(params.get("family") or core.family or "logic"),
            lab_sheet=str(params.get("lab_sheet") or ""),
        )

    if method == "save_path_b_test":
        from ate.core.database import get_context
        from ate.core.test_detect import save_path_b_test

        ctx = get_context()
        return save_path_b_test(
            family=str(params.get("family") or core.family or "logic"),
            test_id=str(params.get("test_id") or params.get("id") or ""),
            text=str(params.get("text") or ""),
            enable_part=str(params.get("enable_part") or params.get("part") or ctx.part_key or ""),
            label=str(params.get("label") or ""),
            lab_sheet=str(params.get("lab_sheet") or ""),
        )

    if method == "list_recipes":
        from ate.core.recipe_store import list_recipes

        return {
            "recipes": list_recipes(family=str(params.get("family") or core.family or ""))
        }

    if method == "load_recipe":
        from ate.core.recipe_store import load_recipe, version_overlay_for

        rid = str(params.get("recipe_id") or params.get("id") or "")
        overlay = version_overlay_for(rid) if params.get("use_overlay", True) else None
        return {"recipe": load_recipe(rid, overlay=overlay)}

    if method == "save_recipe":
        from ate.core.database import get_context, set_context
        from ate.core.paths import sync_defaults_from_context
        from ate.core.recipe_store import save_recipe
        from ate.core.recipe_walk import register_recipe_specs
        from ate.core.registry import load_family

        if any(params.get(k) for k in ("component", "part", "package", "operator", "version")):
            set_context(
                component=params.get("component"),
                part=params.get("part"),
                package=params.get("package"),
                operator=params.get("operator"),
                version=params.get("version"),
                model=params.get("model"),
                year=params.get("year"),
            )
            sync_defaults_from_context()
        graph = params.get("graph") if isinstance(params.get("graph"), dict) else {}
        # Allow flat payload fields on params too
        if params.get("nodes") and not graph.get("nodes"):
            graph = {
                "nodes": params.get("nodes"),
                "edges": params.get("edges") or [],
                "vcc_list": params.get("vcc_list"),
                "logic_inputs": params.get("logic_inputs"),
                "levels": params.get("levels"),
                "rails": params.get("rails"),
            }
        result = save_recipe(
            recipe_id=str(params.get("recipe_id") or params.get("id") or ""),
            graph=graph,
            family=str(params.get("family") or core.family or "logic"),
            label=str(params.get("label") or ""),
            shortform=str(params.get("shortform") or ""),
            details=str(params.get("details") or ""),
            products=list(params.get("products") or []),
            version_overlay=bool(params.get("version_overlay")),
        )
        fam = str(params.get("family") or core.family or "logic")
        if fam and fam != "comparator" and not core.busy:
            try:
                load_family(fam)
                result["loaded_family"] = fam
                result["registered"] = register_recipe_specs(fam)
            except Exception as exc:
                result["family_error"] = str(exc)
        result["root"] = str(get_context().root())
        return result

    if method == "preview_corners":
        from ate.core.recipe_store import preview_corners

        return preview_corners(
            logic_inputs=int(params.get("logic_inputs") or params.get("n") or 2),
            levels=params.get("levels"),
        )

    if method == "grep_products":
        from ate.core.recipe_store import grep_products

        return {"hits": grep_products(str(params.get("q") or params.get("query") or ""))}

    if method == "grep_people":
        from ate.core.recipe_store import grep_people

        return {"hits": grep_people(str(params.get("q") or params.get("query") or ""))}

    if method == "attach_product":
        from ate.core.recipe_store import attach_product

        return attach_product(
            label=str(params.get("label") or params.get("operator") or ""),
            part_code=str(params.get("part") or params.get("part_code") or params.get("q") or ""),
        )

    if method == "attach_person":
        from ate.core.recipe_store import attach_person

        return attach_person(
            label=str(params.get("label") or params.get("name") or ""),
            part_code=str(params.get("part") or params.get("part_code") or ""),
        )

    if method == "wrap_detected_test":
        if core.busy:
            raise RuntimeError("Runner busy — wait for run to finish")
        from ate.core.database import get_context
        from ate.core.test_detect import wrap_detected_test

        fam = str(params.get("family") or core.family or "logic").strip()
        camp = str(core.family or "").strip().lower()
        wrap_fam = fam.strip().lower()
        if camp == "lim":
            camp = "switch"
        if wrap_fam == "lim":
            wrap_fam = "switch"
        if camp and wrap_fam and camp != wrap_fam:
            raise ValueError(
                f"Wrap family must match campaign category ({camp})"
            )
        if camp:
            fam = camp
        ctx = get_context()
        result = wrap_detected_test(
            file=str(params.get("file") or ""),
            fn=str(params.get("fn") or ""),
            test_id=str(params.get("test_id") or params.get("id") or ""),
            family=fam,
            enable_part=str(params.get("enable_part") or params.get("part") or ""),
            lab_sheet=str(params.get("lab_sheet") or ""),
            operator=str(params.get("operator") or ctx.operator or ""),
            allow_others=bool(params.get("allow_others")),
        )
        if result.get("family") and not core.busy:
            try:
                core.load_family(str(result["family"]))
                result["loaded_family"] = core.family
                result["test_count"] = len(all_tests())
            except Exception as exc:
                result["family_error"] = str(exc)
        return result

    if method == "enable_tests_on_part":
        from ate.core.test_detect import copy_enabled_tests, enable_tests_on_part

        src = str(params.get("source_part") or "").strip()
        dest = str(params.get("dest_part") or params.get("part") or "").strip()
        ids = list(params.get("test_ids") or [])
        if src and dest and not ids:
            return copy_enabled_tests(source_part=src, dest_part=dest)
        return enable_tests_on_part(
            dest_part=dest,
            test_ids=ids,
            family=str(params.get("family") or core.family or ""),
            source_part=src,
            update_part_yaml=bool(params.get("update_part_yaml", False)),
        )

    if method == "list_campaign_tests":
        from ate.core.test_detect import list_campaign_tests

        return list_campaign_tests()

    if method == "set_campaign_enabled_tests":
        from ate.core.test_detect import set_campaign_enabled_tests

        ids = list(params.get("test_ids") or [])
        return set_campaign_enabled_tests(
            ids,
            family=str(params.get("family") or core.family or ""),
        )

    if method == "add_missing_campaign_tests":
        from ate.core.test_detect import add_missing_campaign_tests

        return add_missing_campaign_tests()

    if method == "ensure_version":
        from ate.core.new_product import ensure_version

        return ensure_version(
            component=str(params.get("component") or ""),
            part=str(params.get("part") or ""),
            package=str(params.get("package") or ""),
            operator=str(params.get("operator") or ""),
            version=str(params.get("version") or ""),
            sample_size=int(params.get("sample_size") or 4),
            copy_from_version=str(params.get("copy_from_version") or ""),
            open_folder=bool(params.get("open_folder", False)),
            apply=bool(params.get("apply", True)),
        )

    if method == "new_run_session":
        from ate.core.new_product import new_run_session

        return new_run_session(
            run_label=str(params.get("run_label") or params.get("label") or ""),
            params=params.get("params") if isinstance(params.get("params"), dict) else None,
        )

    if method == "list_tags":
        from ate.core.tags import list_tags_rpc

        return list_tags_rpc()

    if method == "save_tags":
        from ate.core.tags import save_tags

        tags = params.get("tags") if isinstance(params.get("tags"), list) else None
        boards = params.get("boards") if isinstance(params.get("boards"), list) else None
        labels = params.get("labels") if isinstance(params.get("labels"), list) else None
        scope = str(params.get("remember_scope") or params.get("scope") or "campaign")
        return save_tags(tags, boards, labels=labels, remember_scope=scope)

    if method == "set_run_prefs":
        from ate.core.database import save_run_prefs

        return save_run_prefs(
            str(params.get("walk_order") or ""),
            sample_size=params.get("sample_size"),
            probe_channels=params.get("probe_channels") or params.get("channels"),
        )

    if method == "set_test_params" or method == "save_test_params":
        from ate.core.database import get_context, save_test_params, set_context
        from ate.core.paths import sync_defaults_from_context

        if any(params.get(k) for k in ("component", "part", "package", "operator", "version")):
            if not core.busy:
                set_context(
                    component=params.get("component"),
                    part=params.get("part"),
                    package=params.get("package"),
                    operator=params.get("operator"),
                    version=params.get("version"),
                    model=params.get("model"),
                    year=params.get("year"),
                )
                sync_defaults_from_context()
        blob = save_test_params(
            str(params.get("test_id") or params.get("id") or ""),
            params.get("params") if isinstance(params.get("params"), dict) else {},
        )
        ctx = get_context()
        out = {**blob, "root": str(ctx.root())}
        if core.busy:
            out["busy_locked"] = True
        return out

    if method == "import_tags":
        from ate.core.tags import import_tags

        src = str(params.get("from_root") or params.get("source") or "").strip()
        if not src:
            raise ValueError("from_root required")
        return import_tags(src, merge=bool(params.get("merge", True)))

    if method == "list_boards":
        from ate.core.tags import list_boards

        return {
            "boards": list_boards(
                family=str(params.get("family") or ""),
                package=str(params.get("package") or ""),
            )
        }

    if method == "filter_campaigns_by_tag":
        from ate.core.tags import filter_campaigns_by_tag

        tag = str(params.get("tag") or "").strip()
        if not tag:
            raise ValueError("tag required")
        return {
            "campaigns": filter_campaigns_by_tag(
                tag, component=str(params.get("component") or "")
            )
        }

    if method == "get_session_report":
        from ate.core.datalog import load_report

        return load_report()

    if method == "list_runs":
        from ate.core.datalog import list_runs

        return list_runs(
            scope=str(params.get("scope") or "part"),
            component=str(params.get("component") or ""),
            part=str(params.get("part") or ""),
            package=str(params.get("package") or ""),
            operator=str(params.get("operator") or ""),
            version=str(params.get("version") or ""),
            limit=int(params.get("limit") or 80),
        )

    if method == "progress_summary":
        from ate.core.progress import progress_summary

        return progress_summary(limit=int(params.get("limit") or 200))

    if method == "heartbeat":
        from ate.core.progress import heartbeat

        return heartbeat(
            owner_id=str(params.get("id") or params.get("owner_id") or ""),
            label=str(params.get("label") or ""),
            campaign=str(params.get("campaign") or ""),
        )

    if method == "board_list":
        from ate.core.progress import board_list

        return {"items": board_list()}

    if method == "board_add":
        from ate.core.progress import board_add

        return board_add(
            author=str(params.get("author") or ""),
            text=str(params.get("text") or ""),
            kind=str(params.get("kind") or "comment"),
        )

    if method == "board_claim":
        from ate.core.new_product import claim_sku

        return claim_sku(
            label=str(params.get("label") or params.get("operator") or ""),
            part=str(params.get("part") or ""),
            package=str(params.get("package") or ""),
            category=str(params.get("category") or params.get("class") or ""),
            model=str(params.get("model") or ""),
            create=bool(params.get("create")),
            sample_size=int(params.get("sample_size") or 4),
        )

    if method == "open_github_issue":
        from ate.core.progress import open_github_issue

        return open_github_issue(
            title=str(params.get("title") or ""),
            body=str(params.get("body") or ""),
        )

    if method == "delete_run":
        from ate.core.datalog import delete_run_file

        path = str(params.get("path") or "").strip()
        if not path:
            raise ValueError("path required")
        return delete_run_file(path)

    if method == "export_datalog":
        from ate.core.datalog import load_report, report_path
        from ate.reporting.sts_datalog import export_latest_report

        c = _session_bound_ctx(params or {})
        doc = load_report(ctx=c)
        paths = export_latest_report(
            doc, sessions_dir=c.sessions_dir(), version_dir=c.root()
        )
        return {"ok": True, **paths, "report": str(report_path(c))}

    if method == "fetch_datasheet":
        from ate.core.database import get_context
        from ate.core.ingest_datasheet import ingest

        ctx = get_context()
        part = str(params.get("part") or ctx.part or "")
        pdf = str(params.get("pdf") or "").strip()
        xlsx = str(params.get("xlsx") or "").strip()
        return ingest(
            part,
            pdf=pdf or None,
            xlsx=xlsx or None,
            part_key=str(params.get("part_key") or ctx.part_key or ""),
            web_ok=True,
            ocr=str(params.get("ocr") or "auto"),
            fill_excel=True,
            copy_golden=True,
            ctx=ctx,
        )

    if method == "sync_datasheet_index":
        from ate.core.lookup import sync_inventory_limits

        return sync_inventory_limits(web_ok=False)

    if method == "fill_workbook":
        from ate.reporting.session_values import fill_workbook_from_report

        ctx = _session_bound_ctx(params or {})
        return fill_workbook_from_report(
            demo=bool(core.simulated),
            copy_golden=True,
            ctx=ctx,
        )

    if method == "list_specs":
        from ate.core.database import get_context
        from ate.core.specs import load_part_datasheet, load_part_specs, test_info_map

        ctx = get_context()
        pk = str(params.get("part_key") or ctx.part_key or "")
        return {
            "part_key": pk,
            "specs": load_part_specs(pk),
            "test_info": test_info_map(pk),
            "datasheet": load_part_datasheet(pk),
        }

    if method == "paste_session_photos":
        from ate.reporting.session_paste import paste_session_photos

        return paste_session_photos()

    if method == "apply_golden_workbook":
        from ate.reporting.golden_workbook import apply_golden_workbook

        path = str(params.get("path") or "").strip() or None
        return apply_golden_workbook(path)

    if method == "check_golden_workbook":
        from ate.reporting.golden_workbook import check_golden_workbook

        path = str(params.get("path") or "").strip() or None
        return check_golden_workbook(path, fix=bool(params.get("fix", False)))

    if method == "get_product_model":
        from ate.core.database import get_context
        from ate.tests.logic.product_model import panel_payload

        ctx = get_context()
        part = str(params.get("part") or params.get("part_key") or ctx.part_key or "")
        return panel_payload(part)

    if method == "save_product_model":
        from ate.core.database import get_context
        from ate.tests.logic.product_model import save_product_model_fields

        ctx = get_context()
        part = str(params.get("part") or params.get("part_key") or ctx.part_key or "")
        patch = params.get("patch") if isinstance(params.get("patch"), dict) else params
        return save_product_model_fields(part, patch)

    raise ValueError(f"Unknown method: {method}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("RPC %s - %s\n" % (self.address_string(), fmt % args))

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_HEAD(self) -> None:
        if self._try_serve_shot(body=False):
            return
        self._reply_browser_probe(body=False)

    def do_GET(self) -> None:
        """Health/probe for browsers. /shot serves campaign graphs. RPC remains POST."""
        if self._try_serve_shot(body=True):
            return
        self._reply_browser_probe(body=True)

    def _try_serve_shot(self, *, body: bool) -> bool:
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") != "/shot":
            return False
        qs = parse_qs(parsed.query)
        rel = unquote((qs.get("rel") or [""])[0] or "")
        from ate.reporting.photo_layout import resolve_shot_file

        try:
            path = resolve_shot_file(rel)
        except PermissionError:
            self.send_response(403)
            self._cors()
            self.end_headers()
            return True
        except FileNotFoundError:
            self.send_response(404)
            self._cors()
            self.end_headers()
            return True
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(path.suffix.lower(), "application/octet-stream")
        data = path.read_bytes() if body else b""
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(path.stat().st_size if not body else len(data)))
        self.send_header("Cache-Control", "private, max-age=5")
        self._cors()
        self.end_headers()
        if body:
            self.wfile.write(data)
        return True

    def _reply_browser_probe(self, *, body: bool) -> None:
        accept = (self.headers.get("Accept") or "").lower()
        if "text/html" in accept:
            payload = (
                "<!doctype html><meta charset=utf-8>"
                "<title>ATE worker</title>"
                "<p>JSON-RPC worker on :8766 (POST).</p>"
                "<p>Open the console: "
                "<a href='http://127.0.0.1:5174'>http://127.0.0.1:5174</a></p>"
            ).encode()
            ctype = "text/html; charset=utf-8"
        else:
            payload = json.dumps(
                {
                    "ok": True,
                    "service": "ate-worker",
                    "rpc": "POST",
                    "ui": "http://127.0.0.1:5174",
                    "version": WORKER_VERSION,
                }
            ).encode()
            ctype = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        if body:
            self.wfile.write(payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            req = json.loads(raw.decode("utf-8"))
            method = req.get("method")
            params = req.get("params") or {}
            req_id = req.get("id")
            result = dispatch(method, params)
            body = {"jsonrpc": "2.0", "id": req_id, "result": result}
            code = 200
        except Exception as exc:
            body = {
                "jsonrpc": "2.0",
                "id": req.get("id") if "req" in dir() else None,
                "error": {"message": str(exc), "traceback": traceback.format_exc()},
            }
            code = 200
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64


def _worker_already_up() -> bool:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        f"http://{JSONRPC_HOST}:{JSONRPC_PORT}",
        data=b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}',
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return int(resp.status) == 200
    except (OSError, urllib.error.URLError):
        return False


def _bind_server(host: str, port: int) -> ThreadingHTTPServer:
    last: OSError | None = None
    for _ in range(4):
        try:
            return ThreadingHTTPServer((host, port), Handler)
        except OSError as exc:
            last = exc
            if _worker_already_up():
                print("worker already listening", flush=True)
                raise SystemExit(0)
            time.sleep(0.5)
    if last is not None:
        raise last
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    host = JSONRPC_HOST
    port = JSONRPC_PORT
    # Bind before ATECore so splash ping works while family/OneDrive warms.
    server = _bind_server(host, port)
    print(f"ATE JSON-RPC worker listening on http://{host}:{port}", flush=True)
    threading.Thread(target=_core, name="ate-core-warm", daemon=True).start()
    while True:
        try:
            server.serve_forever()
            break
        except KeyboardInterrupt:
            print("Worker stopping...", flush=True)
            try:
                _core().emergency_cleanup()
                _core().close_session()
            except Exception:
                pass
            break
        except Exception as exc:
            print(f"worker accept loop: {exc}", flush=True)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
