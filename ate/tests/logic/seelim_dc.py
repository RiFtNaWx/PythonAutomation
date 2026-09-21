"""SeeLim RS1G97 / RS1G126 -- call original goldens/see_lin files.

Does not import Lim.* / Ariff.*. Does not rewrite the golden.
input() / _prompt become pause_hook Continue so the worker is not blocked.
icc / ioz keep the existing Logic ids and dispatch by part (RS0204 / RS1G125 stay).
"""
from __future__ import annotations

import builtins
import importlib.util
import inspect
import math
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from ate.core.paths import REPO_ROOT
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams
from ate.tests.logic.ariff_dc import _run_ioz as _ariff_ioz
from ate.tests.logic.rs0204 import _run_icc as _rs0204_icc

_LOGIC = "LOGIC"
_SEE_LIM_PARTS = frozenset({"rs1g97", "rs1g126"})
_SIBLINGS = (
    "configurations",
    "limits",
    "psu_setup",
    "dmm_setup",
    "scope_setup",
    "instruments",
    "datalog",
    "utils",
    "screenshot",
    "temp_control",
    "current_tests",
    "threshold_tests",
)
_DOWNLOADS = Path(r"C:/Users/OoiJianHong/Downloads/See Lim Repo")


def _path_is(raw: str, folder: Path) -> bool:
    try:
        return bool(raw) and Path(raw).resolve() == folder
    except OSError:
        return False


def _part_key(params: RunParams) -> str:
    return str(getattr(params, "part", "") or "").strip().lower()


def _golden_dir(part: str) -> Path:
    key = str(part or "").strip().lower()
    folder = key.upper() if key.startswith("rs") else "RS" + key.upper()
    local = REPO_ROOT / "goldens" / "see_lin" / folder
    if local.is_dir() and (local / "current_tests.py").is_file():
        return local
    live = _DOWNLOADS / folder
    if live.is_dir():
        return live
    return local


def resolve_current_tests(part: str):
    """Locator for goldens/see_lin/<PART>/current_tests.py. None if missing."""
    path = _golden_dir(part) / "current_tests.py"
    return path if path.is_file() else None


def _ensure_repo_setup() -> None:
    repo = str(REPO_ROOT)
    if repo not in sys.path:
        sys.path.append(repo)
    import generator_setup  # noqa: F401
    import psu_setup  # noqa: F401


@contextmanager
def _isolated_folder(folder: Path) -> Iterator[None]:
    _ensure_repo_setup()
    saved: dict[str, Any] = {}
    for name in _SIBLINGS:
        if name in sys.modules:
            saved[name] = sys.modules.pop(name)
    folder_res = folder.resolve()
    sys.path.insert(0, str(folder))
    try:
        yield
    finally:
        sys.path[:] = [
            p
            for p in sys.path
            if not _path_is(p, folder_res)
        ]
        for name in list(sys.modules):
            if name.startswith("ate_seelim_"):
                sys.modules.pop(name, None)
        for name in _SIBLINGS:
            sys.modules.pop(name, None)
        sys.modules.update(saved)


@contextmanager
def _continue_input(params: RunParams) -> Iterator[None]:
    hook = getattr(params, "pause_hook", None)
    old = builtins.input

    def _ate_input(prompt: object = "") -> str:
        msg = str(prompt or "").strip() or "SeeLim golden: wire, then Continue"
        if hook is None:
            raise RuntimeError("SeeLim golden called input(); START needs Continue")
        if not hook(msg):
            return "s"
        return ""

    builtins.input = _ate_input
    try:
        yield
    finally:
        builtins.input = old


def _load_fn(path: Path, fn_name: str):
    spec = importlib.util.spec_from_file_location(
        f"ate_seelim_{path.parent.name}_{path.stem}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        raise RuntimeError(f"{fn_name} missing in {path}")
    return fn


class _NullLog:
    def log_test(self, *args, **kwargs) -> None:
        return None

    def save_to_xl(self) -> None:
        return None

    def get_summary(self) -> str:
        return ""


def _call_fn(fn: Any, instr: Any, params: RunParams) -> Any:
    try:
        names = set(inspect.signature(fn).parameters)
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
        kwargs["logger"] = _NullLog()
    if names:
        return fn(**kwargs)
    return fn(instr)


_CANON = {
    "icc": "ICC_uA",
    "ii": "II_uA",
    "ioz": "IOZ_uA",
    "ioff": "IOFF_uA",
    "delta_icc": "DELTA_ICC_uA",
    "dicc": "DELTA_ICC_uA",
}


def _flatten(tid: str, raw: Any) -> dict[str, Any]:
    measurements: list[dict[str, Any]] = []

    def _add(mid: str, val: Any, unit: str, mn: Any = None, mx: Any = None) -> None:
        try:
            fv = float(val)
        except (TypeError, ValueError):
            return
        if not math.isfinite(fv):
            return
        row = {"id": str(mid), "value": fv, "unit": unit}
        measurements.append(row)

    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            mid = item.get("param") or item.get("id") or item.get("kind")
            if not mid:
                continue
            unit = "V" if str(item.get("kind") or mid).upper()[:1] in "VD" else "uA"
            _add(mid, item.get("value"), unit, item.get("min"), item.get("max"))
        summary = f"{tid} n={len(measurements)}"
        return {
            "summary": summary,
            "data": {"rows": raw},
            "measurements": measurements,
        }

    data = raw if isinstance(raw, dict) else {"value": raw}

    sub = data.get("Sub_results") if isinstance(data, dict) else None
    if isinstance(sub, dict):
        for key, val in sub.items():
            cur = val
            if isinstance(val, dict):
                cur = val.get(
                    "worst_uA",
                    val.get("value", val.get("ua", val.get("I"))),
                )
            if isinstance(val, (tuple, list)) and val:
                cur = val[0]
            unit = "V" if str(key).upper().startswith(("V", "VT", "DVT")) else "uA"
            _add(key, cur, unit)
    if isinstance(data, dict):
        for key, val in data.items():
            if key in ("Test", "Sub_results", "summary", "data", "measurements"):
                continue
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                continue
            unit = "V" if str(key).upper().startswith(("V", "VT", "DVT")) else "uA"
            _add(key, val, unit)
    if not measurements and isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                _add(key, val, "")
    summary = str(data.get("Test") or tid) if isinstance(data, dict) else str(tid)
    canon = _CANON.get(str(tid or "").strip().lower())
    if canon and not any(str(m.get("id") or "") == canon for m in measurements):
        worst_ua = None
        if isinstance(sub, dict):
            for val in sub.values():
                cur = val.get("worst_uA") if isinstance(val, dict) else val
                try:
                    ua = abs(float(cur))
                except (TypeError, ValueError):
                    continue
                if worst_ua is None or ua > worst_ua:
                    worst_ua = ua
        if worst_ua is not None:
            measurements.append({"id": canon, "value": float(worst_ua), "unit": "uA"})
    if measurements:
        worst = max(measurements, key=lambda m: abs(float(m.get("value") or 0)))
        summary = f"{summary} n={len(measurements)} {worst['id']}={worst['value']}"
    return {
        "summary": summary,
        "data": data if isinstance(data, dict) else {},
        "measurements": measurements,
    }


def run_see_lim(instr, params: RunParams, filename: str, fn_name: str) -> dict[str, Any]:
    part = _part_key(params)
    folder = _golden_dir(part)
    path = folder / filename
    if not path.is_file():
        raise RuntimeError(f"SeeLim golden missing: {path}")
    with _isolated_folder(folder), _continue_input(params):
        fn = _load_fn(path, fn_name)
        raw = _call_fn(fn, instr, params)
    return _flatten(fn_name.replace("test_", "", 1), raw)


def _run_named(filename: str, fn_name: str, parts: frozenset[str]):
    def _run(instr, params: RunParams) -> dict[str, Any]:
        part = _part_key(params)
        if part not in parts:
            raise RuntimeError(f"{fn_name} is SeeLim-only ({', '.join(sorted(parts))}), not {part}")
        return run_see_lim(instr, params, filename, fn_name)

    return _run


def _register(tid: str, label: str, lab: str, required: frozenset[str], run, *, notes: str) -> None:
    register(
        TestSpec(
            id=tid,
            label=label,
            required_instruments=required,
            fixture_mode=_LOGIC,
            lab_sheet=lab,
            run=run,
            dual_channel=False,
            notes=notes,
        )
    )


def _run_icc(instr, params: RunParams) -> dict[str, Any]:
    if _part_key(params) in _SEE_LIM_PARTS:
        return run_see_lim(instr, params, "current_tests.py", "test_icc")
    return _rs0204_icc(instr, params)


def _run_ioz(instr, params: RunParams) -> dict[str, Any]:
    if _part_key(params) == "rs1g126":
        return run_see_lim(instr, params, "current_tests.py", "test_ioz")
    return _ariff_ioz(instr, params)


_NOTE = "SeeLim original goldens/see_lin -- Continue, not stdin"

_register(
    "icc",
    "Quiescent supply current (ICC)",
    "ICC",
    frozenset({"PSU", "DMM"}),
    _run_icc,
    notes=_NOTE + " / RS0204 Icc when part is rs0204",
)
_register(
    "delta_icc",
    "Delta supply current (dICC)",
    "dICC",
    frozenset({"PSU", "DMM", "AWG"}),
    _run_named("current_tests.py", "test_delta_icc", _SEE_LIM_PARTS),
    notes=_NOTE,
)
_register(
    "ii",
    "Input leakage (II)",
    "II",
    frozenset({"PSU", "DMM"}),
    _run_named("current_tests.py", "test_ii", _SEE_LIM_PARTS),
    notes=_NOTE,
)
_register(
    "ioff",
    "Power-off leakage (IOFF)",
    "IOFF",
    frozenset({"PSU", "DMM"}),
    _run_named("current_tests.py", "test_ioff", frozenset({"rs1g126"})),
    notes=_NOTE,
)
_register(
    "input_threshold",
    "Input threshold (VIH/VIL)",
    "InputThreshold",
    frozenset({"PSU", "DMM"}),
    _run_named("threshold_tests.py", "test_input_threshold", _SEE_LIM_PARTS),
    notes=_NOTE + " -- same physics as vih_vil; do not enable both",
)
_register(
    "ioz",
    "High-Z output leakage (IOZ)",
    "IOZ",
    frozenset({"PSU", "DMM"}),
    _run_ioz,
    notes=_NOTE + " on RS1G126; Ariff Path B on RS1G125",
)
