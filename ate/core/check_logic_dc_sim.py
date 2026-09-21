"""Visa-free Path B Logic DC catalog SIM. 11 CONFIRMED. Not a bench green.

Run: python -m ate.core.check_logic_dc_sim

Does not import ate.tests.logic.__init__ (that pulls runner + OneDrive).
Do not import check_logic_dc (that module imports this). Overlay one VCC.
stable_eps_A null = NON_TIGHT. G07 VOH SKIP. RS164 sequential 2^n SKIP.
Timeout SIM is a source fail-bar (behavioral walk lives in check_logic_dc).
Scale-wave G00/G02/G04/G86/2G08/2G32 stay UNCONFIRMED HOLD.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

from ate.core.paths import PARTS_DIR
from ate.fixture.modes import enabled_tests_for_part

# Must match check_logic_dc._CONFIRMED_SIM_PARTS / _ARCHIVE_SIM_PARTS / _NEXT_WAVE_SKUS.
_ACTIVE_LOGIC = (
    "rs1gt34",
    "rs1g97",
    "rs1g126",
    "rs1g08",
    "rs1g07",
    "rs1g14",
    "rs1g32",
    "rs1gt08",
    "rs1gt32",
    "rs1g125",
    "rs164",
)
_ARCHIVE_LOGIC = ("rs1g74", "rs1g123")
_NEXT_WAVE_LOGIC = ("rs1g00", "rs1g02", "rs1g04", "rs1g86", "rs2g08", "rs2g32")

_PATH_B_DC = frozenset(
    {
        "input_threshold",
        "vth",
        "icc",
        "delta_icc",
        "ii",
        "voh",
        "vol",
        "ioz",
        "ioff",
    }
)

_LOGIC_DIR = Path(__file__).resolve().parents[1] / "tests" / "logic"
_LOGIC_DC_PY = _LOGIC_DIR / "logic_dc.py"
_PM_PY = _LOGIC_DIR / "product_model.py"


def _load_pm() -> Any:
    """Load product_model without running ate.tests.logic.__init__."""
    name = "ate.tests.logic.product_model"
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "load_product_model", None):
        return existing
    logic = sys.modules.get("ate.tests.logic")
    if logic is not None and getattr(logic, "__file__", None):
        from ate.tests.logic import product_model as pm

        return pm
    pkg_name = "ate.tests.logic"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(_LOGIC_DIR)]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg
    spec = importlib.util.spec_from_file_location(name, _PM_PY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {_PM_PY}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _enabled(part: str) -> set[str]:
    return {str(x).strip().lower() for x in (enabled_tests_for_part(part) or [])}


def _sets_ok() -> list[str]:
    errors: list[str] = []
    if len(_ACTIVE_LOGIC) != 11:
        errors.append(f"_ACTIVE_LOGIC must be 11 CONFIRMED, got {len(_ACTIVE_LOGIC)}")
    if frozenset(_ARCHIVE_LOGIC) != frozenset(("rs1g74", "rs1g123")):
        errors.append("archive must stay RS1G74 / RS1G123")
    if frozenset(_NEXT_WAVE_LOGIC) != frozenset(
        ("rs1g00", "rs1g02", "rs1g04", "rs1g86", "rs2g08", "rs2g32")
    ):
        errors.append("scale-wave must stay G00/G02/G04/G86/2G08/2G32")
    if set(_NEXT_WAVE_LOGIC) & set(_ACTIVE_LOGIC):
        errors.append("scale-wave UNCONFIRMED must not join CONFIRMED SIM set")
    if set(_ARCHIVE_LOGIC) & set(_ACTIVE_LOGIC):
        errors.append("PARKED archive must stay out of CONFIRMED SIM")
    extra2g = [
        p.name
        for p in sorted(PARTS_DIR.glob("rs2g*.yaml"))
        if p.stem.lower() not in ("rs2g08", "rs2g32")
    ]
    if extra2g:
        errors.append(f"must not invent extra 2G part YAML, got {extra2g}")
    return errors


def _overlay_one_vcc(pm: Any) -> list[str]:
    errors: list[str] = []
    base = pm.load_product_model("rs1gt34")
    if base is None:
        return ["rs1gt34 product_model missing (overlay one VCC)"]
    before = list(base.vcc_list or [])
    over = pm.load_product_model("rs1gt34", overlay={"vcc_list": [3.3]})
    if over is None or list(over.vcc_list or []) != [3.3]:
        errors.append(
            f"overlay one VCC must replace vcc_list with [3.3], got "
            f"{None if over is None else over.vcc_list}"
        )
    again = pm.load_product_model("rs1gt34")
    if again is None or list(again.vcc_list or []) != before:
        errors.append("overlay one VCC must not mutate part yaml vcc_list")
    return errors


def _confirmed_catalog(pm: Any) -> list[str]:
    errors: list[str] = []
    for part in _ACTIVE_LOGIC:
        if not pm.has_product_model(part):
            errors.append(f"{part} CONFIRMED product_model missing")
            continue
        m = pm.load_product_model(part)
        if m is None:
            errors.append(f"{part} product_model failed to load")
            continue
        if part == "rs164":
            if not pm.is_sequential(m):
                errors.append("rs164 SIM: sequential_shift_register required")
            plan = pm.sim_icc_plan(m)
            if int(plan.get("n") or 0) != 0:
                errors.append(
                    f"rs164 sequential 2^n SKIP: sim_icc_plan n must be 0, got {plan.get('n')}"
                )
            en = _enabled(part)
            banned = sorted(en & _PATH_B_DC)
            if banned:
                errors.append(f"rs164 Path B ids must stay OFF, got {banned}")
            continue
        if not pm.is_datasheet_signed(m.status):
            errors.append(f"{part} status must be CONFIRMED for SIM catalog, got {m.status!r}")
        rec = m.recipe if isinstance(m.recipe, dict) else {}
        if rec.get("stable_eps_A") is not None:
            errors.append(f"{part} recipe.stable_eps_A must stay null (NON_TIGHT)")
        en = _enabled(part)
        if part == "rs1g07":
            if "voh" in en:
                errors.append("rs1g07 SIM: voh must stay SKIP/N_A")
            if not pm.is_open_drain(m):
                errors.append("rs1g07 SIM: open_drain required (VOH N_A)")
        if m.has_oe():
            if "ioz" not in en:
                errors.append(f"{part} SIM: has_oe must enable ioz")
        elif "ioz" in en:
            errors.append(f"{part} SIM: ioz must stay OFF")
    return errors


def _timeout_source_bar() -> list[str]:
    errors: list[str] = []
    if not _LOGIC_DC_PY.is_file():
        return ["ate/tests/logic/logic_dc.py missing"]
    text = _LOGIC_DC_PY.read_text(encoding="utf-8")
    if "settle timeout" not in text:
        errors.append("Timeout SIM raises: logic_dc must name settle timeout")
    if "raise RuntimeError" not in text:
        errors.append("Timeout SIM raises: logic_dc must raise RuntimeError")
    if "return sum(window) / len(window) if window else" in text:
        errors.append("Timeout SIM raises: must not soft-return last reading")
    return errors


def _next_wave_hold(pm: Any) -> list[str]:
    errors: list[str] = []
    for part in _NEXT_WAVE_LOGIC:
        if not pm.has_product_model(part):
            errors.append(f"{part} UNCONFIRMED product_model missing (numbers HOLD)")
            continue
        m = pm.load_product_model(part)
        if m is None:
            errors.append(f"{part} product_model failed to load")
            continue
        if pm.is_datasheet_signed(m.status):
            errors.append(
                f"{part} must stay UNCONFIRMED (JH DM unlock != Datasheet CONFIRM)"
            )
        if not pm.is_unconfirmed_status(m.status):
            errors.append(f"{part} status must be UNCONFIRMED, got {m.status!r}")
        if part in ("rs2g08", "rs2g32") and not pm.dual_channel_continue(m):
            errors.append(f"{part} dual_channel_continue path must be ready (CHA then CHB)")
        if part not in ("rs2g08", "rs2g32") and pm.dual_channel_continue(m):
            errors.append(f"{part} must not set dual_channel_continue (1Gxx)")
    return errors


def check_logic_dc_sim() -> list[str]:
    """Visa-free catalog. Skip OpAmp/LDO/Switch/Level. Not a reproduce."""
    pm = _load_pm()
    errors: list[str] = []
    errors += _sets_ok()
    errors += _overlay_one_vcc(pm)
    errors += _confirmed_catalog(pm)
    errors += _timeout_source_bar()
    errors += _next_wave_hold(pm)
    return errors


def main() -> int:
    print("logic-dc SIM: catalog start", flush=True)
    errors = check_logic_dc_sim()
    if errors:
        print("FAIL logic-dc SIM:", flush=True)
        for line in errors:
            print(f"  - {line}", flush=True)
        return 1
    print(
        "OK logic-dc SIM: 11 CONFIRMED catalog "
        "(overlay one VCC; stable_eps_A null=NON_TIGHT; "
        "G07 VOH SKIP; RS164 sequential SKIP; timeout source-bar; "
        "scale-wave UNCONFIRMED HOLD; not a bench green)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
