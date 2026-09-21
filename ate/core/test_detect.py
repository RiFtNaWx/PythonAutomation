"""Detect unmatched def test_* in golden roots + ate/tests; remember / trigger / enable.

AST-only scan -- never execute golden modules at scan time.
Remember file:lineno:fn in snippet_map.yaml. Wrap triggers the original
function; it does not rewrite the golden or write a new imported_*.py.
Refuse live trigger when source still calls input() or imports Lim/Ariff/Soo.
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from ate.core.paths import CONFIG_DIR, PARTS_DIR, REPO_ROOT

TESTS_ROOT = REPO_ROOT / "ate" / "tests"
GOLDEN_ROOTS_PATH = CONFIG_DIR / "golden_roots.yaml"

SKIP_DIR_NAMES = frozenset({
    ".git", ".github", ".venv", "venv", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".mypy_cache", "_backup",
    "site-packages",
})
_SECRET_NAME_RE = re.compile(
    r"(^|[/\\])(\.env|.*credentials.*|.*secret.*|id_rsa|.*\.pem)$",
    re.I,
)
_MAX_PY_BYTES = 1_000_000
_TEST_FN_RE = re.compile(r"^test_(.+)$")

# Family key -> package directory under ate/tests/
_FAMILY_PKG_DIR: dict[str, str] = {
    "opamp": "opa",
    "logic": "logic",
    "level": "level",
    "switch": "lim",
    "lim": "lim",
}

_FIXTURE_FOR_FAMILY: dict[str, str] = {
    "opamp": "BUFFER",
    "logic": "LOGIC",
    "level": "LOGIC",
    "switch": "LIM_RS2323",
    "lim": "LIM_RS2323",
    "power": "LDO",
}
_BUILT_IN_FAMILIES = frozenset({"opamp", "logic", "level", "switch"})
_SHEET_ID_ALIASES = {
    "slewrate": "slew",
    "settlingtime": "settling",
}

# Lab goldens name helpers test_parameter() / AWG smoke as test_*. Not measurements.
_SKIP_TEST_NAMES = frozenset({
    "test_parameter",
    "test_generator_procedures",
})

# Goldens pass instr OR bare VISA handles (See Lin / Lim threshold_tests).
_INSTR_ARG_NAMES = frozenset({
    "instr", "instruments", "inst",
    "psu", "dmm", "gen", "awg", "scope", "mso",
})

# Compact golden id -> already-registered TestSpec ids (do not show as unmatched).
_GOLDEN_ID_ALIASES = {
    "inputthreshold": ("input_thresholds", "vih_vil", "vth"),
    "inputthresholds": ("input_thresholds", "vih_vil"),
    "sr": ("slew",),
    "ssr": ("sssr",),
    "lsr": ("lssr",),
    "npr": ("no_phase_reversal",),
    "powerontime": ("power_on_time",),
    "settlingtime": ("settling",),
    "icc": ("supply_current", "supply_current_sweep", "icc"),
    "ii": ("input_leakage_sweep",),
    "ioff": ("ioff_leakage",),
    "ldoquiescentcurrent": ("iq",),
    "ldovinmin": ("vinmin",),
    "ldolir": ("lir",),
    "ldolor": ("lor",),
    "ldoioutmax": ("ioutmax",),
    "ldoenablecurrent": ("enable_current",),
    "flickernoise": ("noise",),
    "noisebucket": ("noise",),
    "deltaicc": ("delta_supply_current",),
    "deltasupplycurrent": ("delta_supply_current",),
    "voh": ("voh_load", "voh"),
    "vol": ("vol_load", "vol"),
    "gbw": ("gbw",),
}

_VENDOR_TOP = frozenset({"lim", "ariff", "soo", "seelin", "see_lin"})

_AUTHOR_OPS = {
    "seelim": "seelim",
    "lim": "seelim",
    "seelin": "seelim",
    "see_lin": "seelim",
    "see lim": "seelim",
    "ariff": "ariff",
    "eugene": "eugene",
    "soo": "soo",
}

# Path A / Test program: only this person's originals for these SKUs.
_PART_OWN_IDS = {
    "rs1g97": ("icc", "delta_icc", "ii", "input_threshold"),
    "rs1g126": (
        "ioff",
        "ioz",
        "icc",
        "ii",
        "delta_icc",
        "input_threshold",
        "voh",
        "vol",
        "ten",
        "tdis",
    ),
}

_PHYSICS_DUP = (
    frozenset({"vih_vil", "input_thresholds", "input_threshold", "vih", "vil"}),
)


def _compact_id(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(raw or "").lower())


def author_for_operator(op: str) -> str:
    from ate.core.database import canonical_person_label

    lab = (canonical_person_label(op) or op or "").strip().lower()
    return _AUTHOR_OPS.get(lab) or _AUTHOR_OPS.get(lab.replace(" ", "")) or ""


def author_for_path(path: Path | str) -> str:
    joined = str(path or "").replace("\\", "/").lower()
    if "see lim" in joined or "see_lin" in joined or "seelim" in joined:
        return "seelim"
    if "ate/tests/lim/" in joined or "ate/tests/lim\\" in joined.replace("/", "\\"):
        return "seelim"
    if "/soo/" in joined or "\\soo\\" in joined:
        return "soo"
    if "ariff" in joined:
        return "ariff"
    if "eugene_cap" in joined or "/eugene/" in joined or "\\eugene\\" in joined:
        return "eugene"
    if "rs0204" in joined:
        return "soo"
    return ""


def _author_visible(
    file_author: str,
    want_author: str,
    allow_others: bool,
    *,
    operator_set: bool,
) -> bool:
    """Own goldens first. Other people only after allow_others. Path B (no author) stays."""
    who = str(file_author or "").strip().lower()
    want = str(want_author or "").strip().lower()
    if allow_others:
        return (not want) or (not who) or who == want
    if not operator_set:
        return True
    if not who:
        return True
    if not want:
        return False
    return who == want


def _refuse_foreign_golden(
    path: Path | str,
    *,
    operator: str = "",
    allow_others: bool = False,
) -> None:
    if allow_others:
        return
    file_author = author_for_path(path)
    if not file_author:
        return
    op_author = author_for_operator(operator)
    if file_author == op_author:
        return
    raise ValueError(
        f"This is {file_author}'s golden. Tick Allow other people's goldens "
        "to import it, or stay on your own code."
    )


def guess_product_from_path(path: Path | str) -> str:
    joined = str(path or "").replace("\\", "/").upper()
    found = re.findall(r"RS[0-9A-Z]+", joined)
    best = ""
    for tok in found:
        if tok in ("RS",):
            continue
        if len(tok) > len(best):
            best = tok
    return best


def _alias_ok(path: Path) -> bool:
    """Author goldens must not look 'already registered' as another person's TestSpec."""
    joined = str(path).replace("\\", "/").lower()
    if "goldens/" in joined or "goldens\\" in joined:
        return False
    if "see lim repo" in joined or "ariff repo" in joined or "eugene repo" in joined:
        return False
    return True


def _input_bridge_reason(reason: str) -> bool:
    low = str(reason or "").lower()
    return "input()" in low and "vendor" not in low


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _snippet_map_path() -> Path:
    raw = str(os.environ.get("ATE_SNIPPET_MAP") or "").strip()
    if raw:
        return Path(raw)
    return CONFIG_DIR / "snippet_map.yaml"


def _resolve_snippet_file(file: str) -> Path:
    raw = str(file or "").strip()
    if not raw:
        return Path()
    p = Path(raw).expanduser()
    if p.is_file():
        return p
    rel = REPO_ROOT / raw.replace("\\", "/")
    if rel.is_file():
        return rel
    return p


def _store_file(path: Path) -> str:
    if not path or not str(path):
        return ""
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def load_snippet_map() -> list[dict[str, Any]]:
    data = _safe_load_yaml(_snippet_map_path())
    rows = data.get("snippets") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict) and r.get("id")]


def save_snippet_map(rows: list[dict[str, Any]]) -> None:
    path = _snippet_map_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "comment": "Pointers only. Detect scan remembers file:line. START triggers; UI never rewrites source.",
        "snippets": rows,
    }
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _snippet_allow(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        if path.stat().st_size > _MAX_PY_BYTES:
            return False
    except OSError:
        return False
    resolved = path.resolve()
    allowed = [REPO_ROOT / "goldens", TESTS_ROOT]
    for row in load_golden_roots():
        raw = str(row.get("path") or "")
        if raw:
            allowed.append(Path(raw))
    for root in allowed:
        try:
            resolved.relative_to(Path(root).resolve())
            return True
        except (ValueError, OSError):
            continue
    return False


def read_snippet_source(*, file: str, fn: str = "") -> dict[str, Any]:
    path = _resolve_snippet_file(file)
    if not _snippet_allow(path):
        raise ValueError("Snippet file not in goldens / golden_roots / ate/tests")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return {
        "ok": True,
        "file": _store_file(path),
        "text": text,
        "fn": str(fn or ""),
        "lineno": 0,
    }


def save_snippet_source(
    *,
    file: str,
    text: str,
    operator: str = "",
    allow_others: bool = False,
) -> dict[str, Any]:
    path = _resolve_snippet_file(file)
    if not _snippet_allow(path):
        raise ValueError("Refuse write: file not in allowed golden roots")
    _refuse_foreign_golden(path, operator=operator, allow_others=allow_others)
    body = str(text or "")
    if len(body.encode("utf-8")) > _MAX_PY_BYTES:
        raise ValueError("File too large")
    try:
        ast.parse(body)
    except SyntaxError as exc:
        raise ValueError(f"Syntax error, not saved: {exc}") from exc
    path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
    index_path = ""
    note = ""
    try:
        from ate.core.ingest_goldens import GOLDENS_ROOT, write_index

        gold = GOLDENS_ROOT.resolve()
        resolved = path.resolve()
        if gold == resolved or gold in resolved.parents:
            index_path = str(write_index())
            note = "INDEX.md updated"
    except Exception as exc:
        note = f"saved py; INDEX refresh skipped: {exc}"
    return {
        "ok": True,
        "file": _store_file(path),
        "index": index_path,
        "guide": "goldens/GUIDE.md",
        "tutorial": "goldens/TUTORIAL.md",
        "note": note,
    }


def _upsert_snippet(row: dict[str, Any]) -> dict[str, Any]:
    tid = str(row.get("id") or "").strip()
    fam = str(row.get("family") or row.get("family_guess") or "").strip()
    if not tid:
        return row
    rows = load_snippet_map()
    key = (fam, tid)
    out: list[dict[str, Any]] = []
    found = False
    for r in rows:
        if (str(r.get("family") or ""), str(r.get("id") or "")) == key:
            merged = dict(r)
            merged.update(row)
            out.append(merged)
            found = True
        else:
            out.append(r)
    if not found:
        out.append(row)
    save_snippet_map(out)
    return row


def snippet_for_id(tid: str) -> dict[str, Any]:
    want = str(tid or "").strip()
    if not want:
        return {}
    for row in load_snippet_map():
        if str(row.get("id") or "") == want:
            path = _resolve_snippet_file(str(row.get("file") or ""))
            return {
                "file": _store_file(path) if path.is_file() else str(row.get("file") or ""),
                "lineno": int(row.get("lineno") or 0),
                "fn": str(row.get("fn") or ""),
                "trigger": str(row.get("trigger") or ""),
                "family": str(row.get("family") or ""),
            }
    return {}


def source_for_spec(spec: Any) -> dict[str, Any]:
    """What START runs. ate/tests body wins leftover snippet_map wraps."""
    run = getattr(spec, "run", None)
    run_file = ""
    run_line = 0
    fn = str(getattr(run, "__name__", "") or "")
    if run is not None:
        try:
            run_file = inspect.getsourcefile(run) or ""
            run_line = inspect.getsourcelines(run)[1]
        except Exception:
            pass
    posix = str(run_file).replace("\\", "/").lower()
    if "ate/tests/" in posix:
        return {"file": run_file, "lineno": run_line, "fn": fn, "kind": "ate"}
    mapped = snippet_for_id(str(getattr(spec, "id", "") or ""))
    if mapped.get("file"):
        return {
            "file": mapped.get("file") or "",
            "lineno": mapped.get("lineno") or 0,
            "fn": mapped.get("fn") or fn,
            "trigger": mapped.get("trigger") or "",
            "kind": "wrap",
        }
    if run_file:
        return {"file": run_file, "lineno": run_line, "fn": fn, "kind": "ate"}
    return {}


def _ast_imports_vendor(tree: ast.AST) -> str:
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name or "" for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        for n in names:
            top = n.split(".")[0].lower().replace("-", "_")
            if top in _VENDOR_TOP:
                return n
    return ""


def _locate_registered_snippets() -> list[dict[str, Any]]:
    from ate.core.registry import active_family, all_tests

    fam = ""
    try:
        fam = active_family() or ""
    except Exception:
        fam = ""
    rows: list[dict[str, Any]] = []
    mapped = {str(r.get("id") or ""): r for r in load_snippet_map()}
    for spec in all_tests():
        file = ""
        lineno = 0
        fn = ""
        hit = mapped.get(str(spec.id))
        if hit and hit.get("file"):
            file = str(hit.get("file") or "")
            lineno = int(hit.get("lineno") or 0)
            fn = str(hit.get("fn") or "")
        else:
            try:
                file = inspect.getsourcefile(spec.run) or ""
                _lines, lineno = inspect.getsourcelines(spec.run)
                fn = getattr(spec.run, "__name__", "") or ""
            except (OSError, TypeError):
                file, lineno, fn = "", 0, ""
        rows.append(
            {
                "id": spec.id,
                "fn": fn,
                "file": file,
                "lineno": int(lineno or 0),
                "family_guess": fam,
                "blocked": False,
                "blocked_reason": "",
                "matched": True,
                "trigger": "registered",
            }
        )
    return rows


def _persist_scan(detected: list[dict[str, Any]], located: list[dict[str, Any]]) -> None:
    rows = load_snippet_map()
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for r in rows:
        by_key[(str(r.get("family") or ""), str(r.get("id") or ""))] = r
    for r in list(located) + list(detected):
        tid = str(r.get("id") or "").strip()
        if not tid:
            continue
        fam = str(r.get("family_guess") or r.get("family") or "")
        raw_file = str(r.get("file") or "")
        path = _resolve_snippet_file(raw_file) if raw_file else Path()
        stored = _store_file(path) if path and path.is_file() else raw_file
        blocked = bool(r.get("blocked"))
        matched = bool(r.get("matched"))
        trig = str(r.get("trigger") or "")
        if not trig:
            if matched:
                trig = "registered"
            elif blocked:
                trig = "blocked"
            else:
                trig = "unmatched"
        by_key[(fam, tid)] = {
            "id": tid,
            "file": stored,
            "lineno": int(r.get("lineno") or 0),
            "fn": str(r.get("fn") or ""),
            "family": fam,
            "ast_clean": not blocked,
            "blocked_reason": str(r.get("blocked_reason") or ""),
            "trigger": trig,
            "blocked": blocked,
        }
    save_snippet_map(list(by_key.values()))


def _call_snippet_fn(fn: Any, instr: Any, params: Any) -> Any:
    try:
        sig = inspect.signature(fn)
        names = set(sig.parameters)
    except (TypeError, ValueError):
        names = set()
    kwargs: dict[str, Any] = {}
    if "instr" in names:
        kwargs["instr"] = instr
    if "instruments" in names:
        kwargs["instruments"] = instr
    if "params" in names:
        kwargs["params"] = params
    if instr is not None:
        for key in ("psu", "dmm", "gen", "awg", "scope", "mso"):
            if key in names:
                kwargs[key] = getattr(instr, key, None)
    if "logger" in names:
        kwargs["logger"] = None
    if names:
        return fn(**kwargs)
    return fn(instr)


def _normalize_snippet_result(tid: str, raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and (
        "measurements" in raw or "summary" in raw or "data" in raw
    ):
        out = dict(raw)
        if "summary" not in out:
            out["summary"] = f"{tid} from snippet"
        if "data" not in out:
            out["data"] = {}
        return out
    data = raw if isinstance(raw, dict) else {"value": raw}
    measurements: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        for key, val in raw.items():
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                continue
            measurements.append({"id": str(key), "value": val, "unit": ""})
    return {
        "summary": f"{tid} from snippet",
        "data": data if isinstance(data, dict) else {},
        "measurements": measurements,
    }


def trigger_snippet(tid: str, instr: Any, params: Any = None) -> dict[str, Any]:
    """Load the remembered file:fn from disk and call it. Never import Lim/Ariff/Soo."""
    want = str(tid or "").strip()
    row = snippet_for_id(want)
    if not row:
        raise ValueError(f"No snippet pointer for {want}")
    path = _resolve_snippet_file(str(row.get("file") or ""))
    fn_name = str(row.get("fn") or "")
    if not path.is_file():
        raise ValueError(f"Snippet file missing for {want}: {path}")
    src = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        raise ValueError(f"Cannot parse snippet: {exc}") from exc
    vendor = _ast_imports_vendor(tree)
    if vendor:
        raise ValueError(f"Refusing live trigger: vendor import {vendor}")
    found: ast.FunctionDef | None = None
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name == fn_name or _fn_to_id(node.name) == want:
            found = node
            break
    if found is None:
        raise ValueError(f"def {fn_name or want} not in {path}")
    reason = _blocked_reason(
        found, input_helpers=_fns_that_call_input(tree), vendor=vendor
    )
    if reason:
        raise ValueError(f"Refusing live trigger: {reason}")
    spec = importlib.util.spec_from_file_location(f"ate_snip_{want}", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load snippet {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, found.name, None)
    if not callable(fn):
        raise ValueError(f"{found.name} missing in {path}")
    raw = _call_snippet_fn(fn, instr, params)
    return _normalize_snippet_result(want, raw)


def _make_snippet_run(tid: str):
    def _run(instr, params=None):
        return trigger_snippet(tid, instr, params)

    return _run


def register_snippet_pointers(family: str) -> int:
    """Rehydrate live-trigger TestSpecs from snippet_map.yaml. Path B ids win."""
    from ate.core.registry import TestSpec, all_tests, register

    fam = (family or "").strip().lower()
    if fam == "opa":
        fam = "opamp"
    if fam == "lim":
        fam = "switch"
    known = {t.id for t in all_tests()}
    n = 0
    for row in load_snippet_map():
        row_fam = str(row.get("family") or "").strip().lower()
        if row_fam == "opa":
            row_fam = "opamp"
        if row_fam == "lim":
            row_fam = "switch"
        if row_fam != fam:
            continue
        if str(row.get("trigger") or "") != "live":
            continue
        tid = str(row.get("id") or "").strip()
        if not tid or tid in known:
            continue
        if row.get("blocked") or row.get("ast_clean") is False:
            continue
        src_disp = str(row.get("file") or "")
        lineno = int(row.get("lineno") or 0)
        fn = str(row.get("fn") or "")
        fixture = _FIXTURE_FOR_FAMILY.get(fam, "LOGIC")
        register(
            TestSpec(
                id=tid,
                label=tid.replace("_", " ").title(),
                required_instruments=frozenset({"PSU"}),
                fixture_mode=fixture,
                lab_sheet=tid.replace("_", " ").title(),
                run=_make_snippet_run(tid),
                dual_channel=False,
                notes=f"snippet {src_disp}:{lineno} {fn}",
            )
        )
        known.add(tid)
        n += 1
    return n


def load_golden_roots() -> list[dict[str, Any]]:
    """Configured optional roots. Missing dirs omitted (not an error)."""
    data = _safe_load_yaml(GOLDEN_ROOTS_PATH)
    rows = data.get("roots") if isinstance(data, dict) else None
    out: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = str(row.get("path") or "").strip().strip('"')
        if not raw:
            continue
        from ate.core.paths import expand_user_path

        try:
            path = expand_user_path(raw)
        except ValueError:
            continue
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        else:
            path = path.resolve()
        out.append(
            {
                "path": str(path),
                "label": str(row.get("label") or path.name),
                "author": str(row.get("author") or "").strip().lower(),
                "exists": path.is_dir() or path.is_file(),
            }
        )
    return out


def scan_roots() -> list[Path]:
    """Roots that exist: always ate/tests, plus configured goldens that are present."""
    roots: list[Path] = []
    if TESTS_ROOT.is_dir():
        roots.append(TESTS_ROOT.resolve())
    for row in load_golden_roots():
        if not row.get("exists"):
            continue
        p = Path(str(row["path"])).resolve()
        if p not in roots:
            roots.append(p)
    return roots


def _iter_py_files(root: Path) -> list[Path]:
    out: list[Path] = []
    if root.is_file() and root.suffix.lower() == ".py":
        return [root]
    if not root.is_dir():
        return out
    # Prune venv/site-packages while walking. rglob still descends into them.
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            if not name.lower().endswith(".py"):
                continue
            p = Path(dirpath) / name
            if any(part in SKIP_DIR_NAMES for part in p.parts):
                continue
            if _SECRET_NAME_RE.search(str(p)):
                continue
            try:
                if p.stat().st_size > _MAX_PY_BYTES:
                    continue
            except OSError:
                continue
            out.append(p)
    return out


def guess_family_from_path(path: Path) -> str:
    """Heuristic family from path segments. Operator confirms on wrap."""
    parts = [p.lower() for p in path.parts]
    joined = "/".join(parts)
    if "ate" in parts and "tests" in parts:
        try:
            i = parts.index("tests")
            pkg = parts[i + 1] if i + 1 < len(parts) else ""
            if pkg in ("opa", "opamp"):
                return "opamp"
            if pkg == "logic":
                return "logic"
            if pkg == "level":
                return "level"
            if pkg in ("lim", "switch"):
                return "switch"
            if pkg and pkg not in ("__",):
                return pkg
        except ValueError:
            pass
    if any(
        x in joined
        for x in (
            "/ariff/",
            "\\ariff\\",
            "/soo/",
            "\\soo\\",
            "/logic/",
            "\\logic\\",
            "rs1g",
            "threshold_tests",
            "current_tests",
        )
    ):
        return "logic"
    if any(x in joined for x in ("/lim/", "\\lim\\", "rs2323", "analogswitch", "analog_switch")):
        return "switch"
    if any(x in joined for x in ("/eugene/", "\\eugene\\", "rs622", "/opa/", "\\opa\\", "opamp")):
        return "opamp"
    return ""


def _fn_to_id(name: str) -> str:
    m = _TEST_FN_RE.match(name)
    return m.group(1) if m else name


def _registered_keys(family: str | None = None) -> set[str]:
    """Ids / lab_sheets / test_* names currently registered (optionally load family)."""
    from ate.core.registry import all_tests, load_family

    if family:
        try:
            load_family(family)
        except Exception:
            pass
    keys: set[str] = set()
    for t in all_tests():
        keys.add(str(t.id).lower())
        keys.add(f"test_{t.id}".lower())
        sheet = str(getattr(t, "lab_sheet", "") or "").strip().lower()
        if sheet:
            keys.add(sheet)
            keys.add(sheet.replace(" ", "_"))
            keys.add(sheet.replace(" ", "").lower())
    return keys


def _ast_has_input(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "input":
                return True
    return False


def _ast_has_instr_param(fn: ast.FunctionDef) -> bool:
    for arg in list(fn.args.args) + list(fn.args.kwonlyargs):
        if arg.arg in _INSTR_ARG_NAMES:
            return True
    return False


def _fns_that_call_input(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in getattr(tree, "body", []) or []:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _ast_has_input(node):
            names.add(node.name)
    return names


def _calls_named(fn: ast.FunctionDef, names: set[str]) -> str:
    if not names:
        return ""
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in names:
            return node.func.id
        if isinstance(node.func, ast.Attribute) and node.func.attr in names:
            return node.func.attr
    return ""


def _blocked_reason(
    fn: ast.FunctionDef,
    *,
    input_helpers: set[str] | None = None,
    vendor: str = "",
) -> str:
    # AST Call only -- do not regex the source segment (docstrings can say "no input()").
    if vendor:
        return (
            f"vendor import {vendor} -- Path B in ate/tests; "
            "do not live-trigger Lim/Ariff/Soo"
        )
    if _ast_has_input(fn):
        return "calls input() -- rewrite to pause_hook / Continue before wrap"
    helper = _calls_named(fn, (input_helpers or set()) - {fn.name})
    if helper:
        return (
            f"calls input() via {helper} -- rewrite to pause_hook / Continue before wrap"
        )
    if not _ast_has_instr_param(fn):
        return "missing instrument handle (instr/psu/dmm/gen/scope)"
    return ""


def _is_registered_match(
    tid: str, fn: str, reg: set[str], *, allow_alias: bool = True
) -> bool:
    compact_reg = {_compact_id(k) for k in reg}
    cands = [tid, fn, f"test_{tid}"]
    for raw in cands:
        low = str(raw or "").lower()
        if low in reg or _compact_id(low) in compact_reg:
            return True
    if allow_alias:
        for alt in _GOLDEN_ID_ALIASES.get(_compact_id(tid), ()):
            if alt in reg or _compact_id(alt) in compact_reg:
                return True
    return False


def scan_file(path: Path, *, registered: set[str] | None = None) -> list[dict[str, Any]]:
    """AST-scan one .py for def test_* not already registered."""
    try:
        src = path.read_text(encoding="utf-8-sig", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError) as exc:
        return [
            {
                "id": path.stem,
                "fn": "",
                "file": str(path),
                "lineno": 0,
                "family_guess": guess_family_from_path(path),
                "blocked": True,
                "blocked_reason": f"parse error: {exc}",
                "matched": False,
            }
        ]
    reg = registered if registered is not None else set()
    input_helpers = _fns_that_call_input(tree)
    vendor = _ast_imports_vendor(tree)
    rows: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        if node.name in _SKIP_TEST_NAMES:
            continue
        tid = _fn_to_id(node.name)
        matched = _is_registered_match(
            tid, node.name, reg, allow_alias=_alias_ok(path)
        )
        # Path B ate/tests rows are listed via registry locate. Author goldens
        # stay visible so Load/Save hits the original file, not the wrapper.
        if matched and _alias_ok(path):
            continue
        reason = _blocked_reason(node, input_helpers=input_helpers, vendor=vendor)
        rows.append(
            {
                "id": tid,
                "fn": node.name,
                "file": str(path),
                "lineno": int(node.lineno or 0),
                "family_guess": guess_family_from_path(path),
                "product": guess_product_from_path(path),
                "author": author_for_path(path),
                "blocked": bool(reason) and not matched,
                "blocked_reason": "" if matched else reason,
                "input_bridge": (not matched) and _input_bridge_reason(reason),
                "matched": matched,
                "trigger": "registered" if matched else "",
            }
        )
    return rows


def _prefer_live_originals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per author+product+id. Prefer Downloads originals over goldens/ copies."""
    chosen: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row.get("author") or ""),
            str(row.get("product") or "").upper(),
            str(row.get("id") or ""),
            str(row.get("fn") or ""),
        )
        prev = chosen.get(key)
        if prev is None:
            chosen[key] = row
            continue
        rf = str(row.get("file") or "").replace("\\", "/").lower()
        pf = str(prev.get("file") or "").replace("\\", "/").lower()
        if "downloads" in rf and "downloads" not in pf:
            chosen[key] = row
    return list(chosen.values())


def _prefer_original_located(
    located: list[dict[str, Any]],
    goldens: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Drop ate/tests wrappers when the person's original file is on disk."""
    orig_ids = {str(g.get("id") or "") for g in goldens}
    out: list[dict[str, Any]] = []
    for row in located:
        tid = str(row.get("id") or "")
        joined = str(row.get("file") or "").replace("\\", "/").lower()
        if tid in orig_ids and "ate/tests/" in joined:
            continue
        out.append(row)
    for row in goldens:
        item = dict(row)
        item["matched"] = True
        item["trigger"] = "registered"
        item["blocked"] = False
        item["blocked_reason"] = ""
        item["input_bridge"] = False
        out.append(item)
    return _prefer_live_originals(out)


def list_detected_tests(
    *,
    family: str | None = None,
    operator: str | None = None,
    product: str | None = None,
    author: str | None = None,
    allow_others: bool = False,
) -> dict[str, Any]:
    """Scan roots; default this person's goldens. Other authors only if allow_others."""
    from ate.core.registry import active_family, load_family, union_registered_ids

    roots_meta = load_golden_roots()
    prev = active_family()
    registered: set[str] = set()
    try:
        registered = union_registered_ids(restore=prev or (family or ""))
        if family:
            try:
                load_family(family)
            except Exception:
                pass
        elif prev:
            try:
                load_family(prev)
            except Exception:
                pass
    finally:
        if prev and active_family() != prev:
            try:
                load_family(prev)
            except Exception:
                pass

    op_name = str(operator or "").strip()
    op_author = author_for_operator(op_name)
    requested = str(author or "").strip().lower()
    if allow_others:
        want_author = requested or op_author
    else:
        want_author = op_author
    operator_set = bool(op_name)
    want_product = str(product or "").strip().upper()
    detected: list[dict[str, Any]] = []
    scanned_files = 0
    ate_tests = TESTS_ROOT.resolve()
    for root in scan_roots():
        root_author = ""
        for meta in roots_meta:
            if Path(str(meta.get("path") or "")).resolve() == Path(root).resolve():
                root_author = str(meta.get("author") or "")
                break
        if Path(root).resolve() != ate_tests:
            if not _author_visible(
                root_author, want_author, allow_others, operator_set=operator_set
            ):
                continue
        for py in _iter_py_files(root):
            if py.name.startswith("imported_") and "ate" in py.parts and "tests" in py.parts:
                continue
            file_author = author_for_path(py) or root_author
            if not _author_visible(
                file_author, want_author, allow_others, operator_set=operator_set
            ):
                continue
            if want_author and not file_author and "ate" in py.parts and "tests" in py.parts:
                continue
            scanned_files += 1
            detected.extend(scan_file(py, registered=registered))

    detected = _prefer_live_originals(detected)
    detected = [
        r for r in detected
        if _author_visible(
            str(r.get("author") or ""), want_author, allow_others, operator_set=operator_set
        )
    ]
    if want_product:
        detected = [
            r for r in detected
            if str(r.get("product") or "").upper() in ("", want_product)
        ]
    golden_hits = [r for r in detected if r.get("matched")]
    detected = [r for r in detected if not r.get("matched")]
    detected.sort(key=lambda r: (r.get("blocked", False), str(r.get("id") or ""), str(r.get("file") or "")))
    located = _locate_registered_snippets()
    for row in located:
        row["author"] = author_for_path(str(row.get("file") or ""))
        row["product"] = guess_product_from_path(str(row.get("file") or ""))
        row["input_bridge"] = False
    located = _prefer_original_located(located, golden_hits)
    located = [
        r for r in located
        if _author_visible(
            str(r.get("author") or ""), want_author, allow_others, operator_set=operator_set
        )
    ]
    if want_product:
        located = [
            r for r in located
            if str(r.get("product") or "").upper() in ("", want_product)
        ]
    _persist_scan(detected, located)
    return {
        "ok": True,
        "roots": roots_meta,
        "author": want_author,
        "allow_others": bool(allow_others),
        "scanned_files": scanned_files,
        "detected": detected,
        "located": located,
        "count": len(detected),
        "located_count": len(located),
        "blocked_count": sum(1 for r in detected if r.get("blocked")),
    }


def _family_tests_dir(family: str) -> Path:
    key = (family or "").strip().lower()
    if key == "opa":
        key = "opamp"
    if key == "lim":
        key = "switch"
    dirname = _FAMILY_PKG_DIR.get(key, key)
    if not dirname or not re.match(r"^[a-z][a-z0-9_]*$", dirname):
        raise ValueError(f"Invalid family {family!r}")
    dest = TESTS_ROOT / dirname
    if not dest.is_dir():
        raise ValueError(f"Family package missing: {dest}")
    return dest


def _ensure_init_imports(pkg_dir: Path, module_stem: str) -> None:
    init = pkg_dir / "__init__.py"
    text = init.read_text(encoding="utf-8") if init.is_file() else ""
    pkg = f"ate.tests.{pkg_dir.name}"
    line = f"from {pkg} import {module_stem}  # noqa: F401"
    if module_stem in text and f"import {module_stem}" in text:
        return
    if not text.strip():
        text = f'"""Family package — modules call register(TestSpec)."""\n\n'
    if "__all__" in text:
        # Append import before __all__ if possible
        text = text.rstrip() + "\n" + line + "\n"
        m = re.search(r"__all__\s*=\s*\[([^\]]*)\]", text)
        if m and f'"{module_stem}"' not in m.group(0) and f"'{module_stem}'" not in m.group(0):
            inner = m.group(1).rstrip()
            sep = ", " if inner.strip() else ""
            new_inner = f'{inner}{sep}"{module_stem}"'
            text = text[: m.start(1)] + new_inner + text[m.end(1) :]
    else:
        text = text.rstrip() + "\n" + line + f'\n__all__ = ["{module_stem}"]\n'
    init.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


_RESERVED_PATH_B = frozenset({
    "runner", "registry", "server", "database", "init", "__init__",
    "imported_input_off_leakage",
})


def _pkg_for_write(family: str) -> str:
    key = (family or "").strip().lower()
    if key == "opa":
        key = "opamp"
    if key == "lim":
        key = "switch"
    # Level rail loads dual-rail from logic; empty ate/tests/level stays a stub.
    if key == "level":
        return "logic"
    dirname = _FAMILY_PKG_DIR.get(key, key)
    if not dirname or not re.match(r"^[a-z][a-z0-9_]*$", dirname):
        raise ValueError(f"Invalid family {family!r}")
    return dirname


def path_b_template(
    *,
    test_id: str,
    label: str = "",
    family: str = "logic",
    lab_sheet: str = "",
) -> dict[str, Any]:
    tid = re.sub(r"[^a-z0-9_]+", "", str(test_id or "").strip().lower())
    if not tid:
        tid = "my_slot"
    lab = str(label or "").strip() or tid.replace("_", " ").title()
    sheet = str(lab_sheet or "").strip() or lab
    fam = str(family or "logic").strip().lower() or "logic"
    if fam == "lim":
        fam = "switch"
    fix = _FIXTURE_FOR_FAMILY.get(fam) or _FIXTURE_FOR_FAMILY.get("logic") or "LOGIC"
    mid = tid.upper() + "_uA"
    pkg = _pkg_for_write(fam)
    text = (
        'from ate.core.registry import TestSpec, register\n'
        'from ate.core.runner import RunParams\n'
        '\n'
        'def run(instr, params: RunParams) -> dict:\n'
        '    hook = params.pause_hook\n'
        f'    if hook is not None and not hook("{lab}: wire PSU CH1=VCC, DMM, then Continue"):\n'
        '        return {"summary": "aborted", "data": {}}\n'
        '    from psu_setup import power_on_protected\n'
        '    vcc = float(params.vcc or 3.3)\n'
        '    ilim = float(params.current_limit_a or 0.10)\n'
        '    power_on_protected(instr.psu, 1, vcc, ilim)\n'
        '    value = 0.0\n'
        '    return {\n'
        f'        "summary": "{tid}=" + str(value),\n'
        '        "data": {"VCC": vcc},\n'
        f'        "measurements": [{{"id": "{mid}", "value": value, "unit": "uA"}}],\n'
        '    }\n'
        '\n'
        'register(TestSpec(\n'
        f'    id="{tid}",\n'
        f'    label="{lab}",\n'
        '    required_instruments=frozenset({"PSU", "DMM"}),\n'
        f'    fixture_mode="{fix}",\n'
        f'    lab_sheet="{sheet}",\n'
        '    run=run,\n'
        '    dual_channel=False,\n'
        '))\n'
    )
    return {
        "ok": True,
        "id": tid,
        "family": fam,
        "file": f"ate/tests/{pkg}/{tid}.py",
        "text": text,
    }


def _path_b_refuse(src: str) -> str:
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return f"syntax: {exc}"
    vendor = _ast_imports_vendor(tree)
    if vendor:
        return f"vendor import {vendor}"
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
        ):
            return "calls input() -- use pause_hook / Continue"
    if "register(" not in src or "TestSpec" not in src:
        return "missing register(TestSpec)"
    if "measurements" not in src:
        return "missing measurements"
    if "pause_hook" not in src:
        return "missing pause_hook"
    if "power_on_protected" not in src:
        return "missing power_on_protected"
    return ""


def save_path_b_test(
    *,
    family: str,
    test_id: str,
    text: str,
    enable_part: str = "",
    label: str = "",
    lab_sheet: str = "",
) -> dict[str, Any]:
    """Write ate/tests/<pkg>/<id>.py + __init__ import. Does not edit runner.py."""
    tid = re.sub(r"[^a-z0-9_]+", "", str(test_id or "").strip().lower())
    if not re.match(r"^[a-z][a-z0-9_]{1,40}$", tid):
        raise ValueError("test id must be lowercase slug, e.g. my_slot")
    if tid in _RESERVED_PATH_B or tid.startswith("imported_"):
        raise ValueError(f"reserved test id {tid!r}")
    fam = str(family or "").strip().lower() or "logic"
    if fam == "lim":
        fam = "switch"
    pkg_name = _pkg_for_write(fam)
    pkg_dir = TESTS_ROOT / pkg_name
    if not pkg_dir.is_dir():
        raise ValueError(f"Family package missing: {pkg_dir}")
    dest = (pkg_dir / f"{tid}.py").resolve()
    try:
        dest.relative_to(TESTS_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Refuse write outside ate/tests") from exc
    if dest.name != f"{tid}.py":
        raise ValueError("Refuse write: filename must match test id")
    body = str(text or "").strip()
    if not body:
        body = path_b_template(
            test_id=tid, label=label, family=fam, lab_sheet=lab_sheet
        )["text"]
    reason = _path_b_refuse(body)
    if reason:
        raise ValueError(f"Refuse write: {reason}")
    dest.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
    _ensure_init_imports(pkg_dir, tid)
    import importlib
    import sys

    from ate.core.registry import load_family, refresh_family_table

    modname = f"ate.tests.{pkg_name}.{tid}"
    try:
        if modname in sys.modules:
            importlib.reload(sys.modules[modname])
        else:
            importlib.import_module(modname)
        refresh_family_table()
        load_family(fam if fam != "level" else "logic")
    except Exception as exc:
        raise RuntimeError(f"Wrote {dest} but family reload failed: {exc}") from exc
    enabled = None
    if enable_part:
        enabled = enable_tests_on_part(
            dest_part=enable_part,
            test_ids=[tid],
            family=fam if fam != "level" else "logic",
            update_part_yaml=False,
        )
    return {
        "ok": True,
        "id": tid,
        "file": _store_file(dest),
        "family": fam,
        "enabled": enabled,
        "restart": True,
    }


def wrap_detected_test(
    *,
    file: str,
    fn: str = "",
    test_id: str = "",
    family: str,
    enable_part: str = "",
    lab_sheet: str = "",
    operator: str = "",
    allow_others: bool = False,
) -> dict[str, Any]:
    """Remember the golden file:line and trigger it. Does not write imported_<id>.py."""
    src_path = Path(str(file or "")).expanduser()
    if not src_path.is_file():
        raise ValueError(f"Source file not found: {file}")
    _refuse_foreign_golden(src_path, operator=operator, allow_others=allow_others)
    src = src_path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        raise ValueError(f"Cannot parse source: {exc}") from exc

    target_fn = (fn or "").strip()
    tid = (test_id or "").strip()
    found: ast.FunctionDef | None = None
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        if target_fn and node.name != target_fn:
            continue
        if tid and _fn_to_id(node.name) != tid and node.name != tid:
            continue
        if not target_fn and not tid:
            found = node
            break
        found = node
        break
    if found is None:
        raise ValueError(f"No matching def test_* in {src_path.name}")

    tid = tid or _fn_to_id(found.name)
    if not re.match(r"^[a-z][a-z0-9_]*$", tid):
        raise ValueError(f"Invalid test id {tid!r}")

    vendor = _ast_imports_vendor(tree)
    reason = _blocked_reason(
        found, input_helpers=_fns_that_call_input(tree), vendor=vendor
    )
    fam = (family or "").strip().lower()
    if fam in ("opa",):
        fam = "opamp"
    if fam == "lim":
        fam = "switch"
    pointer = {
        "id": tid,
        "file": _store_file(src_path),
        "lineno": int(found.lineno or 0),
        "fn": found.name,
        "family": fam,
        "ast_clean": not bool(reason),
        "blocked_reason": reason,
        "trigger": "blocked" if reason else "live",
        "blocked": bool(reason),
    }
    if reason:
        _upsert_snippet(pointer)
        raise ValueError(f"Refusing wrap: {reason}")

    if fam in _BUILT_IN_FAMILIES:
        try:
            from ate.core.database import family_for_component, get_context

            ctx = get_context()
            camp = family_for_part(ctx.part_key) or family_for_component(ctx.component)
            camp = (camp or "").strip().lower()
            if camp == "lim":
                camp = "switch"
            if camp in _BUILT_IN_FAMILIES and camp != fam:
                raise ValueError(
                    f"Wrap family must match campaign category: "
                    f"campaign={camp!r} wrap={fam!r}"
                )
        except ValueError:
            raise
        except Exception:
            pass

    sheet = (lab_sheet or tid.replace("_", " ").title()).strip() or tid
    from ate.core.registry import all_tests, load_family, refresh_family_table

    refresh_family_table()
    loaded = load_family(fam)
    ids = {t.id for t in all_tests()}
    if tid in ids:
        pointer["trigger"] = "registered"
        _upsert_snippet(pointer)
        mode = "enable"
    else:
        pointer["trigger"] = "live"
        _upsert_snippet(pointer)
        loaded = load_family(fam)
        ids = {t.id for t in all_tests()}
        if tid not in ids:
            raise RuntimeError(
                f"Remembered {tid!r} but it is not in registry after load_family({fam})"
            )
        mode = "trigger"

    enabled = None
    if enable_part:
        enabled = enable_tests_on_part(
            dest_part=enable_part,
            test_ids=[tid],
            family=fam,
            update_part_yaml=False,
        )

    return {
        "ok": True,
        "id": tid,
        "family": loaded,
        "mode": mode,
        "module": "",
        "lab_sheet": sheet,
        "snippet": {
            "file": pointer["file"],
            "lineno": pointer["lineno"],
            "fn": pointer["fn"],
            "trigger": pointer["trigger"],
        },
        "enabled": enabled,
        "test_count": len(ids),
    }


def _part_yaml_path(part_key: str) -> Path:
    key = re.sub(r"[^a-z0-9]+", "", (part_key or "").strip().lower())
    if not key:
        raise ValueError("part key required")
    return PARTS_DIR / f"{key}.yaml"


def family_for_part(part_key: str) -> str:
    from ate.core.database import family_for_component

    path = _part_yaml_path(part_key)
    data = _safe_load_yaml(path)
    comp = str(data.get("component") or "")
    fam = family_for_component(comp) if comp else ""
    if fam:
        return fam
    # product_class fallback via run_ic categories
    pc = str(data.get("product_class") or "").strip().lower()
    if pc in ("opamp", "logic", "level", "switch", "lim"):
        return "switch" if pc == "lim" else pc
    return ""


def enable_tests_on_part(
    *,
    dest_part: str,
    test_ids: list[str],
    family: str = "",
    source_part: str = "",
    update_catalog: bool = True,
    update_part_yaml: bool = False,
) -> dict[str, Any]:
    """Append test ids. Same-family only. Default: this campaign catalog, not shared part yaml."""
    from ate.core.registry import all_tests, load_family

    dest_key = re.sub(r"[^a-z0-9]+", "", (dest_part or "").strip().lower())
    if not dest_key:
        raise ValueError("dest_part required")
    ids = [str(x).strip() for x in (test_ids or []) if str(x).strip()]
    if not ids:
        raise ValueError("test_ids required")

    dest_fam = family_for_part(dest_key)
    src_key = re.sub(r"[^a-z0-9]+", "", (source_part or "").strip().lower())
    if src_key:
        src_fam = family_for_part(src_key)
        if not src_fam or not dest_fam or src_fam != dest_fam:
            raise ValueError(
                f"Cross-family copy refused: source={src_key!r}/{src_fam!r} "
                f"dest={dest_key!r}/{dest_fam!r}"
            )
        fam = src_fam
    else:
        fam = (family or dest_fam or "").strip().lower()
        if fam == "lim":
            fam = "switch"
        if not fam:
            raise ValueError(f"Cannot resolve family for part {dest_key!r}")
        if dest_fam and dest_fam != fam:
            raise ValueError(
                f"Cross-family copy refused: family={fam!r} dest={dest_key!r}/{dest_fam!r}"
            )

    load_family(fam)
    known = {t.id for t in all_tests()}
    missing = [i for i in ids if i not in known]
    if missing:
        raise ValueError(f"Ids not in family {fam!r} registry: {missing}")

    path = _part_yaml_path(dest_key)
    if not path.is_file():
        raise ValueError(f"Part yaml missing: {path}")
    data = _safe_load_yaml(path)
    existing = data.get("enabled_tests")
    if not isinstance(existing, list):
        existing = []
    merged = list(existing)
    added: list[str] = []
    for i in ids:
        if i not in merged:
            merged.append(i)
            added.append(i)
    if update_part_yaml:
        data["enabled_tests"] = merged
        path.write_text(
            yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    catalog_path = None
    catalog_added: list[str] = []
    if update_catalog:
        try:
            from ate.core.database import get_context

            ctx = get_context()
            if str(ctx.part_key or "").lower() == dest_key or str(ctx.part or "").lower() == dest_key:
                cpath = ctx.root() / "_manifest" / "test_catalog.yaml"
                catalog_path = str(cpath)
                cdata = _safe_load_yaml(cpath) if cpath.is_file() else {}
                cen = cdata.get("enabled_tests")
                if not isinstance(cen, list) or not cen:
                    from ate.fixture.modes import enabled_tests_for_part

                    seed = enabled_tests_for_part(dest_key, catalog=None)
                    if seed:
                        cen = list(seed)
                    else:
                        cen = [t.id for t in all_tests()]
                for i in ids:
                    if i not in cen:
                        cen.append(i)
                        catalog_added.append(i)
                cdata["enabled_tests"] = cen
                cpath.parent.mkdir(parents=True, exist_ok=True)
                cpath.write_text(
                    yaml.safe_dump(cdata, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
        except Exception:
            pass

    return {
        "ok": True,
        "dest_part": dest_key,
        "family": fam,
        "enabled_tests": merged,
        "added": added,
        "catalog_path": catalog_path,
        "catalog_added": catalog_added,
    }


def copy_enabled_tests(*, source_part: str, dest_part: str) -> dict[str, Any]:
    """Copy source part's enabled_tests onto dest (same family)."""
    from ate.fixture.modes import enabled_tests_for_part

    src_key = re.sub(r"[^a-z0-9]+", "", (source_part or "").strip().lower())
    ids = enabled_tests_for_part(src_key) or []
    if not ids:
        raise ValueError(f"Source part {src_key!r} has no enabled_tests")
    return enable_tests_on_part(
        dest_part=dest_part,
        test_ids=list(ids),
        source_part=src_key,
        update_part_yaml=False,
    )


def _known_test_id(raw: str, known: set[str]) -> str:
    s = str(raw or "").strip().lower()
    compact = re.sub(r"[^a-z0-9_]+", "", s)
    if compact in known:
        return compact
    nosep = re.sub(r"[^a-z0-9]+", "", s)
    if nosep in known:
        return nosep
    alt = _SHEET_ID_ALIASES.get(nosep, "")
    if alt in known:
        return alt
    return ""


def _ids_from_list(raw: Any, known: set[str]) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        nid = _known_test_id(str(item), known)
        if nid and nid not in out:
            out.append(nid)
    return out


def _ids_from_sheet_map(data: dict[str, Any], known: set[str]) -> list[str]:
    tests = data.get("tests") if isinstance(data, dict) else None
    if not isinstance(tests, dict):
        return []
    out: list[str] = []
    for key, entry in tests.items():
        candidates = [str(key)]
        if isinstance(entry, dict):
            if entry.get("folder"):
                candidates.append(str(entry["folder"]))
            if entry.get("id"):
                candidates.append(str(entry["id"]))
        for raw in candidates:
            nid = _known_test_id(raw, known)
            if nid and nid not in out:
                out.append(nid)
    return out


def _campaign_family(ctx: Any) -> str:
    from ate.core.database import family_for_component

    fam = family_for_part(getattr(ctx, "part_key", "") or "")
    if not fam:
        fam = family_for_component(getattr(ctx, "component", "") or "")
    fam = (fam or "").strip().lower()
    if fam == "lim":
        fam = "switch"
    return fam


def list_campaign_tests() -> dict[str, Any]:
    """This operator's Version only. Other people listed, never merged."""
    from ate.core.database import (
        get_context,
        is_campaign_dir,
        is_version_name,
        require_write_operator,
    )
    from ate.core.registry import load_family_tests
    from ate.fixture.modes import enabled_tests_for_part

    ctx = get_context()
    try:
        op = require_write_operator(ctx.operator)
    except ValueError as exc:
        return {
            "ok": False,
            "error": str(exc),
            "available": [],
            "current": [],
            "missing": [],
            "versions": [],
            "skipped_operators": [],
            "copy_between_people": False,
        }

    fam = _campaign_family(ctx)
    if not fam:
        raise ValueError("Cannot resolve campaign category (family)")
    specs = load_family_tests(fam)
    known = {t.id for t in specs}

    catalog = ctx.load_test_catalog()
    catalog_list = catalog.get("enabled_tests") if isinstance(catalog, dict) else None
    filtered = enabled_tests_for_part(ctx.part_key, catalog=catalog)
    if filtered is None:
        current_ids = [t.id for t in specs]
        current_from = "registry_all"
    else:
        current_ids = [i for i in filtered if i in known]
        if isinstance(catalog_list, list) and catalog_list:
            current_from = "catalog"
        else:
            current_from = "part_yaml"

    allow_ids = (
        set(_PART_OWN_IDS.get(str(ctx.part_key or "").lower(), ())) | set(current_ids)
        if str(ctx.part_key or "").lower() in _PART_OWN_IDS
        else known
    )
    available = [
        {
            "id": t.id,
            "label": t.label,
            "on": t.id in set(current_ids),
            "fixture_mode": t.fixture_mode,
        }
        for t in specs
        if t.id in allow_ids
    ]
    if current_ids:
        order = {tid: i for i, tid in enumerate(current_ids)}
        available.sort(
            key=lambda row: (
                0 if row["id"] in order else 1,
                order.get(row["id"], 9999),
                row["id"],
            )
        )

    part_ids = _ids_from_list(
        enabled_tests_for_part(ctx.part_key, catalog=None) or [],
        known,
    )
    this_sheet = _ids_from_sheet_map(ctx.load_sheet_map(), known)

    skipped_operators: list[dict[str, str]] = []
    versions: list[dict[str, Any]] = []
    union: list[str] = []
    pkg_dir = ctx.root().parent.parent
    op_dir = ctx.root().parent
    if pkg_dir.is_dir():
        for child in sorted(pkg_dir.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if is_version_name(child.name):
                skipped_operators.append(
                    {"operator": child.name, "reason": "not_operator_folder"}
                )
                continue
            if child.name.startswith("_"):
                skipped_operators.append(
                    {"operator": child.name, "reason": "skip_folder"}
                )
                continue
            if child.name.lower() != op.lower():
                skipped_operators.append(
                    {"operator": child.name, "reason": "other_operator"}
                )
                continue
            for ver in sorted(child.iterdir(), key=lambda p: p.name.lower()):
                if not is_campaign_dir(ver):
                    continue
                cdata = _safe_load_yaml(ver / "_manifest" / "test_catalog.yaml")
                sm = _safe_load_yaml(ver / "_manifest" / "sheet_map.yaml")
                ids = _ids_from_list(cdata.get("enabled_tests"), known)
                for nid in _ids_from_sheet_map(sm, known):
                    if nid not in ids:
                        ids.append(nid)
                versions.append(
                    {
                        "version": ver.name,
                        "enabled_tests": ids,
                        "path": str(ver),
                    }
                )
                for nid in ids:
                    if nid not in union:
                        union.append(nid)

    gap_src = set(union) | set(part_ids) | set(this_sheet)
    missing = [i for i in sorted(gap_src) if i not in set(current_ids)]

    return {
        "ok": True,
        "operator": op,
        "part": ctx.part_key,
        "part_label": ctx.part,
        "family": fam,
        "version": ctx.version,
        "available": available,
        "current": current_ids,
        "current_from": current_from,
        "part_yaml": part_ids,
        "versions": versions,
        "missing": missing,
        "skipped_operators": skipped_operators,
        "copy_between_people": False,
        "catalog_path": str(ctx.test_catalog_path()),
        "operator_folder": str(op_dir),
    }


def set_campaign_enabled_tests(
    test_ids: list[str],
    *,
    family: str = "",
) -> dict[str, Any]:
    """Replace this Version catalog enabled_tests. Does not write part yaml or other people."""
    from ate.core.database import get_context, require_write_operator
    from ate.core.registry import all_tests, load_family

    ctx = get_context()
    op = require_write_operator(ctx.operator)
    camp_fam = _campaign_family(ctx)
    req = (family or "").strip().lower()
    if req == "lim":
        req = "switch"
    if req in ("opa",):
        req = "opamp"
    if req and camp_fam and req != camp_fam:
        raise ValueError(
            f"Same category only: campaign={camp_fam!r} request={req!r}"
        )
    fam = camp_fam or req
    if not fam:
        raise ValueError("Cannot resolve campaign category (family)")
    load_family(fam)
    known = {t.id for t in all_tests()}
    ids: list[str] = []
    unknown: list[str] = []
    for raw in test_ids or []:
        nid = str(raw or "").strip()
        if not nid:
            continue
        if nid not in known:
            unknown.append(nid)
            continue
        if nid not in ids:
            ids.append(nid)
    if unknown:
        raise ValueError(f"Ids not in family {fam!r} registry: {unknown}")

    cpath = ctx.test_catalog_path()
    cdata = _safe_load_yaml(cpath) if cpath.is_file() else {}
    cdata["enabled_tests"] = ids
    cdata["part_key"] = ctx.part_key
    cdata["owner"] = op
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(
        yaml.safe_dump(cdata, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "operator": op,
        "part": ctx.part_key,
        "family": fam,
        "version": ctx.version,
        "enabled_tests": ids,
        "catalog_path": str(cpath),
        "part_yaml_written": False,
    }


def add_missing_campaign_tests() -> dict[str, Any]:
    """Enable tests found on this person's other Versions / part yaml. Never other people."""
    snap = list_campaign_tests()
    if not snap.get("ok"):
        return snap
    missing = list(snap.get("missing") or [])
    current = list(snap.get("current") or [])
    if not missing:
        return {
            "ok": True,
            "added": [],
            "enabled_tests": current,
            "skipped_operators": snap.get("skipped_operators") or [],
        }
    merged = list(current)
    for nid in missing:
        if nid not in merged:
            merged.append(nid)
    out = set_campaign_enabled_tests(merged, family=str(snap.get("family") or ""))
    out["added"] = missing
    out["skipped_operators"] = snap.get("skipped_operators") or []
    return out
