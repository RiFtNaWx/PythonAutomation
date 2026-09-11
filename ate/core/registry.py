"""Test registry — pattern from LabAutomation_14.7 Lim REGISTERED_TESTS."""

from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Callable, Optional



from ate.fixture.modes import fixture_mode_rank, within_mode_test_rank





@dataclass

class TestSpec:

    """One pluggable OPA/ATE test."""



    id: str

    label: str

    required_instruments: frozenset[str]

    fixture_mode: str

    lab_sheet: str  # sheet name in RS622XK_Lab_Report_TTSOP.xlsx

    run: Callable[..., Any]

    enabled: bool = True

    notes: str = ""

    scope_preset: dict[str, Any] = field(default_factory=dict)
    fixed_steps: list[dict[str, Any]] = field(default_factory=list)
    dual_channel: bool = True  # pause for CHA/CHB probe switch per DUT
    short_tag: str = ""  # optional UI short name; else derived from id





_REGISTRY: dict[str, TestSpec] = {}

_ACTIVE_FAMILY: str = ""

# Family key -> package that registers tests on import (A01 plugin table)
FAMILY_PACKAGES: dict[str, str] = {
    "opamp": "ate.tests.opa",
    "logic": "ate.tests.logic",
    "level": "ate.tests.level",
    "switch": "ate.tests.lim",  # analog switch (RS2323); package name is historical
    "power": "ate.tests.power",
}

BUILTIN_FAMILY_PACKAGES: dict[str, str] = dict(FAMILY_PACKAGES)
DEFAULT_FAMILY = "opamp"
# Person names are not families. Old "lim" key = analog switch.
FAMILY_ALIASES: dict[str, str] = {"lim": "switch"}
# Level Shifters keep the Level rail/folder; tests are the dual-rail logic suite (RS0204).
SUITE_ALIASES: dict[str, str] = {"level": "logic"}


def _extra_families_path():
    from pathlib import Path as _P
    return _P(__file__).resolve().parents[1] / "config" / "extra_families.yaml"


def _load_extra_families() -> dict[str, str]:
    try:
        import yaml
    except Exception:
        return {}
    path = _extra_families_path()
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    block = raw.get("families", raw)
    if not isinstance(block, dict):
        return {}
    out: dict[str, str] = {}
    for key, val in block.items():
        fam = str(key or "").strip().lower()
        if not fam or fam in ("opamp", "opa", "logic", "level", "lim", "switch", "power"):
            continue
        if isinstance(val, dict):
            pkg = str(val.get("package") or f"ate.tests.{fam}").strip()
        else:
            pkg = str(val or f"ate.tests.{fam}").strip()
        if pkg:
            out[fam] = pkg
    return out


def _discover_test_packages() -> dict[str, str]:
    import pkgutil
    skip = {"opa", "logic", "level", "lim", "switch", "power"}
    found: dict[str, str] = {}
    try:
        import ate.tests
    except Exception:
        return found
    for info in pkgutil.iter_modules(getattr(ate.tests, "__path__", [])):
        if not info.ispkg:
            continue
        name = info.name
        if name.startswith("_") or name in skip:
            continue
        found[name] = f"ate.tests.{name}"
    return found


def refresh_family_table() -> dict[str, str]:
    """Rebuild FAMILY_PACKAGES from builtins + ate.tests.* + extra_families.yaml."""
    merged = dict(BUILTIN_FAMILY_PACKAGES)
    merged.update(_discover_test_packages())
    merged.update(_load_extra_families())
    FAMILY_PACKAGES.clear()
    FAMILY_PACKAGES.update(merged)
    return dict(FAMILY_PACKAGES)


def known_families() -> list[str]:
    refresh_family_table()
    return sorted(FAMILY_PACKAGES)


def family_labels() -> dict[str, str]:
    """Rail display names. extra_families.yaml `label:` overrides the key."""
    refresh_family_table()
    labels = {
        "opamp": "OpAmp",
        "logic": "Logic",
        "level": "Level",
        "switch": "Analog SW",
        "lim": "Analog SW",
        "power": "Power",
    }
    extras = _load_extra_family_labels()
    for fam in FAMILY_PACKAGES:
        if fam in extras:
            labels[fam] = extras[fam]
        elif fam not in labels:
            labels[fam] = fam.replace("_", " ")
    return labels


def _load_extra_family_labels() -> dict[str, str]:
    try:
        import yaml
    except Exception:
        return {}
    path = _extra_families_path()
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    block = raw.get("families", raw)
    if not isinstance(block, dict):
        return {}
    out: dict[str, str] = {}
    for key, val in block.items():
        fam = str(key or "").strip().lower()
        if not fam or not isinstance(val, dict):
            continue
        lab = str(val.get("label") or "").strip()
        if lab:
            out[fam] = lab
    return out


def clear() -> None:
    """Drop all registered tests (call before loading another family)."""
    _REGISTRY.clear()


def active_family() -> str:
    return _ACTIVE_FAMILY


def load_family(family: str | None = None) -> str:
    """Clear registry and import the family's test package.

    Empty string is an explicit stub (Power / Comparator): clear tests, do not
    fall back to OpAmp. None still means DEFAULT_FAMILY.
    """
    global _ACTIVE_FAMILY
    refresh_family_table()
    if family is not None and str(family).strip() == "":
        clear()
        _ACTIVE_FAMILY = ""
        return ""
    key = (family or DEFAULT_FAMILY).strip().lower()
    key = FAMILY_ALIASES.get(key, key)
    suite_key = SUITE_ALIASES.get(key, key)
    pkg = FAMILY_PACKAGES.get(suite_key) or FAMILY_PACKAGES.get(key)
    if pkg is None:
        known = ", ".join(sorted(FAMILY_PACKAGES))
        raise ValueError(f"Unknown family {family!r}; known: {known}")
    clear()
    import importlib
    import sys

    mod = importlib.import_module(pkg)
    # Reload package so runtime-added modules (ingest / F23 wrap) appear in __all__.
    mod = importlib.reload(mod)
    subs = getattr(mod, "__all__", None) or []
    if subs:
        for name in subs:
            subname = f"{pkg}.{name}"
            if subname in sys.modules:
                importlib.reload(sys.modules[subname])
            else:
                importlib.import_module(subname)
    else:
        importlib.reload(mod)
    _ACTIVE_FAMILY = key
    return key



def register(spec: TestSpec) -> TestSpec:

    _REGISTRY[spec.id] = spec

    return spec





def get(test_id: str) -> Optional[TestSpec]:

    return _REGISTRY.get(test_id)





def all_tests() -> list[TestSpec]:

    """Return tests in fixture-canonical order (same board grouped)."""

    specs = list(_REGISTRY.values())

    specs.sort(

        key=lambda s: (

            fixture_mode_rank(s.fixture_mode),

            within_mode_test_rank(s.fixture_mode, s.id),

            s.id,

        )

    )

    return specs





def filter_runnable(available: set[str]) -> list[TestSpec]:

    """Skip tests whose required instruments are missing (Lim filter_runnable)."""

    runnable: list[TestSpec] = []

    for spec in all_tests():

        if not spec.enabled:

            continue

        missing = sorted(spec.required_instruments - available)

        if missing:

            print(f"  SKIPPING {spec.label}: missing {', '.join(missing)}")

            continue

        runnable.append(spec)

    return runnable





def group_by_fixture(test_ids: list[str]) -> list[tuple[str, list[TestSpec]]]:

    """Batch selected tests by fixture mode so same board runs together.



    Reorders into FIXTURE_RUN_ORDER (BUFFER → G11 → G_NEG100 → …; VOS research last)

    and within each mode uses the part catalog test list. Operator prompt

    fires once per batch (i.e. only when the physical config must change).

    """

    specs = [get(tid) for tid in test_ids]

    specs = [s for s in specs if s is not None]

    if not specs:

        return []



    specs.sort(

        key=lambda s: (

            fixture_mode_rank(s.fixture_mode),

            within_mode_test_rank(s.fixture_mode, s.id),

            s.id,

        )

    )



    batches: list[tuple[str, list[TestSpec]]] = []

    current_mode = specs[0].fixture_mode

    current: list[TestSpec] = [specs[0]]

    for spec in specs[1:]:

        if spec.fixture_mode == current_mode:

            current.append(spec)

        else:

            batches.append((current_mode, current))

            current_mode = spec.fixture_mode

            current = [spec]

    batches.append((current_mode, current))

    return batches


