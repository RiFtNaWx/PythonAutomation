"""Test Database tree — component / part / package / operator / version.

Canonical layout (images + waveforms + manifests; Excel linked by sheet_map):

  #Test_Database/
    {Component}/          e.g. OpAmp
      {Part}/             e.g. RS622
        {Package}/        e.g. TTSOP8
          {Operator}/     e.g. Eugene (person folder; not "All")
            {Version_N}/  e.g. Version_1  (campaign — not calendar year)
              _manifest/
                sheet_map.yaml      # folder <-> Excel sheet <-> paste anchors
                test_catalog.yaml
                test_params.yaml    # per-test sweep / specs for this Version only
              workbook/             # lab report (editable; Excel MCP target)
              sessions/             # per-run JSON manifests
              {TestKey}/            # ORT, VOS, SlewRate, …
                DUT_{1..N}/
                  screenshots/
                  graphs/

Fixture / gain "config" is NOT a path segment — it lives in sheet_map +
ate/fixture/modes.py and drives operator prompts between batches.

Photo naming: {TEST}_{DUT}_{VARIANT}_{YYYY-MM-DD_HHMMSS}.jpg
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from ate.core.paths import CONFIG_DIR, PARTS_DIR, TEST_DB_ROOT, cloud_kind, expand_user_path

MYT = timezone(timedelta(hours=8))

_VERSION_RE = re.compile(r"^Version_(\d+)$", re.IGNORECASE)
_OWNER_ID_RE = re.compile(r"^[a-z][a-z0-9]*$")
# Board / PIC display. Disk folders can stay Lim / ChangThong.
_PERSON_CANON = {
    "lim": "SeeLim",
    "seelim": "SeeLim",
    "ariff": "Ariff",
    "eugene": "Eugene",
    "changthong": "ChangTong",
    "changtong": "ChangTong",
    "soo": "Soo",
    "chuntak": "Chun Tak",
    "chuntat": "Chun Tak",
}


def _person_key(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(raw or "").strip().lower())


def canonical_person_label(raw: str) -> str:
    """One lab name: Lim/SeeLim -> SeeLim, eugene -> Eugene. Not a Users table."""
    s = str(raw or "").strip()
    if not s:
        return ""
    key = _person_key(s)
    if key in _PERSON_CANON:
        return _PERSON_CANON[key]
    for row in load_owners():
        oid = str(row.get("id") or "").lower()
        lab = str(row.get("label") or oid)
        if row.get("alias_of"):
            continue
        if oid == key or _person_key(lab) == key:
            return lab
    return s
UNASSIGNED_OPERATOR = "_unassigned"
WRITE_BLOCKED_OPERATORS = frozenset({
    "", "all", "All", "ALL",
    "kevin", "Kevin", "KEVIN",
    "ate", "ATE", "Ate",
})
OWNERS_PATH = CONFIG_DIR / "owners.yaml"
CLOUD_PEOPLE_PATH: Path | None = None  # tests patch; else TEST_DB_ROOT/_ate/people.yaml
_OWNERS_PREAMBLE = (
    "# Operators are people. Family rail is product class (RUN-IC).\n"
    "# Picking an operator defaults their campaign; other families stay.\n"
    "\n"
)


def is_version_name(name: str) -> bool:
    n = str(name or "")
    return bool(_VERSION_RE.match(n) or n.lower().startswith("version"))


def is_campaign_dir(path: Path) -> bool:
    """True if path looks like a Version campaign root."""
    if not path.is_dir():
        return False
    if is_version_name(path.name):
        return True
    return (path / "_manifest").is_dir() or (path / "workbook").is_dir()


def _looks_like_person(raw: str) -> bool:
    s = str(raw or "").strip()
    if not s or s.lower() == "all" or s.startswith("_"):
        return False
    return bool(re.search(r"[A-Za-z]", s))


def owner_id_from_label(label: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]+", "", str(label or "").strip())
    oid = compact.lower()
    if not oid or not _OWNER_ID_RE.match(oid) or oid == "all":
        raise ValueError("Person name must include letters (not All)")
    return oid


def operator_folder_label(owner_id_or_label: str | None) -> str:
    """Map owners.yaml id/label to a filesystem folder name. Never returns All."""
    raw = str(owner_id_or_label or "").strip()
    if not raw or raw.lower() == "all":
        raise ValueError("Operator=All is view-only; pick a person before writing campaigns")
    for row in load_owners():
        oid = str(row.get("id") or "")
        label = str(row.get("label") or oid)
        if oid.lower() == raw.lower() or label.lower() == raw.lower():
            if oid.lower() == "all":
                raise ValueError("Operator=All is view-only; pick a person before writing campaigns")
            return label
    if raw.startswith("_"):
        return raw
    if _looks_like_person(raw):
        return raw
    return UNASSIGNED_OPERATOR


def is_observer_operator(operator: str | None) -> bool:
    """All / Kevin / role=observer -- view-only, no START."""
    raw = str(operator or "").strip()
    if not raw or raw.lower() in ("all", "kevin", "ate"):
        return True
    for row in load_owners():
        oid = str(row.get("id") or "").lower()
        lab = str(row.get("label") or "").lower()
        if oid != raw.lower() and lab != raw.lower():
            continue
        role = str(row.get("role") or "").strip().lower()
        return oid in ("all", "kevin", "ate") or lab in ("kevin", "ate") or role == "observer"
    return False


def require_write_operator(operator: str | None) -> str:
    """Normalize operator folder for writes; reject All / observer."""
    raw = str(operator or "").strip()
    if raw in WRITE_BLOCKED_OPERATORS or raw.lower() in ("all", "kevin", "ate"):
        raise ValueError("Observer/All/ATE is view-only; pick a person before writing campaigns")
    if is_observer_operator(raw):
        raise ValueError("Observer/All is view-only; pick a person before writing campaigns")
    return operator_folder_label(raw)


def prefer_live_operator(
    package_dir: Path,
    version: str,
    part: str,
    parsed: str,
) -> str:
    """Skip leftover _unassigned when a person campaign exists beside it."""
    parsed = (parsed or "").strip() or UNASSIGNED_OPERATOR
    if parsed != UNASSIGNED_OPERATOR and not parsed.startswith("_"):
        return parsed
    try:
        from ate.core.migrate_operator_folders import _pic_label_map

        pic = _pic_label_map().get(str(part).upper(), "")
    except Exception:
        pic = ""
    if pic and pic != UNASSIGNED_OPERATOR and (package_dir / pic / version).is_dir():
        return pic
    if package_dir.is_dir():
        for child in sorted(package_dir.iterdir()):
            if not child.is_dir():
                continue
            if child.name.startswith("_") or child.name == UNASSIGNED_OPERATOR:
                continue
            if is_version_name(child.name):
                continue
            if (child / version).is_dir():
                return child.name
    return parsed


@dataclass
class DbContext:
    """Active characterization campaign under #Test_Database."""

    component: str = "OpAmp"
    part: str = "RS622"
    package: str = "TTSOP8"
    operator: str = "Eugene"  # person folder under Package/
    version: str = "Version_1"
    model: str = "RS622XK"  # marketing / datasheet model name
    sample_size: int = 4
    part_key: str = "rs622"  # ate/config/parts/<key>.yaml
    year: str = ""  # optional metadata only (not a folder axis)
    notes: str = ""

    def root(self) -> Path:
        op = str(self.operator or UNASSIGNED_OPERATOR).strip() or UNASSIGNED_OPERATOR
        return TEST_DB_ROOT / self.component / self.part / self.package / op / self.version

    def manifest_dir(self) -> Path:
        return self.root() / "_manifest"

    def sessions_dir(self) -> Path:
        return self.root() / "sessions"

    def workbook_dir(self) -> Path:
        return self.root() / "workbook"

    def sheet_map_path(self) -> Path:
        return self.manifest_dir() / "sheet_map.yaml"

    def test_catalog_path(self) -> Path:
        return self.manifest_dir() / "test_catalog.yaml"

    def run_prefs_path(self) -> Path:
        return self.manifest_dir() / "run_prefs.yaml"

    def test_params_path(self) -> Path:
        return self.manifest_dir() / "test_params.yaml"

    def lab_report_path(self) -> Path:
        # bind_golden_auto: Fill/plot targets Version golden_auto only (never ultimate_manual).
        try:
            from ate.tests.logic.excel_lock import bind_golden_auto

            bound = bind_golden_auto(self)
            if bound:
                return Path(bound)
        except Exception:
            pass
        # Prefer sheet_map workbook path; else first xlsx in workbook/; else part yaml.
        sm = self.load_sheet_map()
        rel = ((sm.get("workbook") or {}) if isinstance(sm, dict) else {}).get("path")
        if rel:
            candidate = (self.manifest_dir() / str(rel)).resolve()
            if candidate.is_file():
                return candidate
        wb = self.workbook_dir()
        if wb.is_dir():
            xlsx = sorted(wb.glob("*.xlsx"))
            if xlsx:
                return xlsx[0]
        return wb / f"{self.model}_Lab_Report_{self.package}.xlsx"

    def test_folder(self, test_key: str) -> Path:
        return self.root() / test_key

    def dut_folder(self, test_key: str, dut_index: int) -> Path:
        return self.test_folder(test_key) / f"DUT_{int(dut_index)}"

    def screenshot_dir(self, test_key: str, dut_index: int | None = None) -> Path:
        if dut_index is None:
            return self.test_folder(test_key) / "screenshots"
        return self.dut_folder(test_key, dut_index) / "screenshots"

    def graph_dir(self, test_key: str, dut_index: int | None = None) -> Path:
        if dut_index is None:
            return self.test_folder(test_key) / "graphs"
        return self.dut_folder(test_key, dut_index) / "graphs"

    def _default_photo_test_key(self) -> str:
        """First real test folder / sheet_map folder; ORT only as OpAmp fallback."""
        skip = {"_manifest", "workbook", "sessions"}
        sm = self.load_sheet_map()
        tests = (sm.get("tests") or {}) if isinstance(sm, dict) else {}
        for key, entry in tests.items() if isinstance(tests, dict) else []:
            folder = ""
            if isinstance(entry, dict):
                folder = str(entry.get("folder") or "")
            name = folder or str(key)
            if name and (self.root() / name).is_dir():
                return name
        root = self.root()
        if root.is_dir():
            for child in sorted(root.iterdir()):
                if child.is_dir() and child.name not in skip and not child.name.startswith("_"):
                    return child.name
        fam = family_for_component(self.component)
        if fam == "opamp":
            return "ORT"
        return "Setup"

    def photo_preview(self, test_key: str | None = None, dut_index: int = 1) -> str:
        key = test_key or self._default_photo_test_key()
        return str(self.screenshot_dir(key, dut_index))

    def identity(self) -> dict[str, Any]:
        tags: list[str] = []
        boards: list[str] = []
        labels: list[dict[str, str]] = []
        try:
            from ate.core.tags import load_tags

            t = load_tags(self)
            tags = list(t.get("tags") or [])
            boards = list(t.get("boards") or [])
            labels = list(t.get("labels") or [])
        except Exception:
            pass
        walk_order = "channel"
        prefs: dict[str, Any] = {}
        try:
            prefs = load_run_prefs(self)
            walk_order = str(prefs.get("walk_order") or "channel")
        except Exception:
            pass
        probe_channels: list[str] = ["CHA"]
        try:
            from ate.core.specs import probe_channels_for_part

            probe_channels = probe_channels_for_part(
                self.part_key or self.part,
                family=family_for_component(self.component),
            )
        except Exception:
            pass
        if prefs.get("probe_channels"):
            probe_channels = list(prefs["probe_channels"])
        sample_size = int(self.sample_size or 4)
        if prefs.get("sample_size"):
            sample_size = int(prefs["sample_size"])
        return {
            "component": self.component,
            "part": self.part,
            "package": self.package,
            "operator": self.operator,
            "version": self.version,
            "model": self.model,
            "sample_size": sample_size,
            "part_key": self.part_key,
            "year": self.year,
            "tags": tags,
            "boards": boards,
            "labels": labels,
            "walk_order": walk_order,
            "probe_channels": probe_channels,
            "root": str(self.root()),
            "lab_report": str(self.lab_report_path()),
            "sheet_map": str(self.sheet_map_path()),
            "sessions": str(self.sessions_dir()),
            "photo_example": self.photo_preview(),
            "test_database_root": str(TEST_DB_ROOT),
            "cloud_kind": cloud_kind(TEST_DB_ROOT),
        }

    def load_sheet_map(self) -> dict[str, Any]:
        path = self.sheet_map_path()
        if not path.is_file():
            return {}
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}

    def load_test_catalog(self) -> dict[str, Any]:
        path = self.test_catalog_path()
        if not path.is_file():
            return {}
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}

    def test_entry(self, test_key: str) -> dict[str, Any]:
        sm = self.load_sheet_map()
        tests = sm.get("tests") or {}
        if not isinstance(tests, dict):
            return {}
        # Accept folder key or excel sheet name.
        if test_key in tests:
            return dict(tests[test_key])
        for _k, entry in tests.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("folder") == test_key or entry.get("excel_sheet") == test_key:
                return dict(entry)
        return {}

    def ensure_tree(self, test_keys: Optional[list[str]] = None) -> list[str]:
        """Create sessions/_manifest and DUT screenshot/graph folders."""
        created: list[str] = []
        root = self.root()
        for rel in ("_manifest", "sessions", "workbook"):
            p = root / rel
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                created.append(str(p))

        keys = list(test_keys or [])
        if not keys:
            sm = self.load_sheet_map()
            tests = sm.get("tests") or {}
            if isinstance(tests, dict):
                for _k, entry in tests.items():
                    if isinstance(entry, dict) and entry.get("folder"):
                        keys.append(str(entry["folder"]))
                    elif isinstance(_k, str):
                        keys.append(_k)
        if not keys:
            try:
                from ate.fixture.modes import enabled_tests_for_part

                keys = list(enabled_tests_for_part(self.part_key) or [])
            except Exception:
                keys = []
        if not keys:
            # Never grow OpAmp GBW/ORT on Level/Power/Logic stubs.
            keys = ["Setup"]

        n = max(1, min(16, int(self.sample_size or 4)))
        for key in keys:
            for dut in range(1, n + 1):
                for sub in ("screenshots", "graphs"):
                    p = self.dut_folder(key, dut) / sub
                    if not p.exists():
                        p.mkdir(parents=True, exist_ok=True)
                        created.append(str(p))
            shared = self.test_folder(key) / "screenshots"
            if not shared.exists():
                shared.mkdir(parents=True, exist_ok=True)
                created.append(str(shared))
        invalidate_tree_cache()
        return created


@dataclass
class RunSession:
    """One ATE run archived under sessions/."""

    session_id: str
    started_at: str
    context: dict[str, Any]
    params: dict[str, Any] = field(default_factory=dict)
    instrument_map: dict[str, str] = field(default_factory=dict)
    fixture_plan: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    finished_at: str = ""
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_lock = threading.Lock()
_active: Optional[DbContext] = None
_current_session: Optional[RunSession] = None


def _read_bench_defaults() -> dict[str, Any]:
    path = CONFIG_DIR / "bench.yaml"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def _model_from_part_yaml(part_key: str) -> tuple[str, str, int]:
    path = PARTS_DIR / f"{part_key}.yaml"
    model, package, sample = part_key.upper(), "TTSOP8", 4
    if path.is_file():
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if isinstance(data, dict):
            model = str(data.get("part") or model)
            package = str(data.get("package") or package)
            sample = int(data.get("sample_size") or sample)
    return model, package, sample


def default_context() -> DbContext:
    bench = _read_bench_defaults()
    part_key = str(bench.get("default_part") or "rs622")
    model, package, sample = _model_from_part_yaml(part_key)
    year = str(bench.get("year") or datetime.now(MYT).year)

    # Prefer parsing test_database path from bench.yaml
    td = bench.get("test_database")
    if td:
        p = expand_user_path(str(td))
        # New: …/#Test_Database/OpAmp/RS622/TTSOP8/Eugene/Version_1
        # Legacy: …/#Test_Database/OpAmp/RS622/TTSOP8/Version_1
        try:
            parts = p.parts
            idx = next(i for i, x in enumerate(parts) if x == "#Test_Database" or x == "Test_Database")
            component = parts[idx + 1]
            part = parts[idx + 2]
            package = parts[idx + 3]
            seg4 = parts[idx + 4]
            if is_version_name(seg4):
                operator = UNASSIGNED_OPERATOR
                version = seg4
            else:
                operator = seg4
                version = parts[idx + 5]
            package_dir = Path(*parts[: idx + 4])
            operator = prefer_live_operator(package_dir, version, part, operator)
            return DbContext(
                component=component,
                part=part,
                package=package,
                operator=operator,
                version=version,
                model=model,
                sample_size=sample,
                part_key=part_key,
                year=year,
            )
        except (StopIteration, IndexError):
            pass

    return DbContext(
        component="OpAmp",
        part="RS622",
        package=package,
        operator="Eugene",
        version="Version_1",
        model=model,
        sample_size=sample,
        part_key=part_key,
        year=year,
    )


def family_for_component(component: str) -> str:
    """Map #Test_Database component folder to ATE family key (product class)."""
    c = (component or "").strip().lower().replace(" ", "").replace("_", "")
    if c in ("logic", "logictranslator", "logicseries"):
        return "logic"
    if c in ("level", "levelshifters", "levelshifter", "leveltranslator"):
        return "level"
    if c in (
        "opamp",
        "operationalamplifier",
        "lownoiseopamp",
        "generalopamp",
        "precisionopamp",
    ):
        return "opamp"
    if c in ("switch", "analogswitch", "analogsw"):
        return "switch"
    if c in ("lim",):
        return "switch"
    if c in ("power", "ldo", "linearregulator"):
        return "power"
    try:
        from ate.core.new_product import load_categories

        for row in load_categories():
            comp = str(row.get("component") or "").strip().lower().replace(" ", "").replace("_", "")
            if comp != c:
                continue
            fam = str(row.get("family") or "").strip()
            if row.get("live") and fam:
                return fam
            return ""
    except Exception:
        pass
    try:
        from ate.core.registry import FAMILY_ALIASES, known_families

        if c in FAMILY_ALIASES:
            return FAMILY_ALIASES[c]
        for fam in known_families():
            key = str(fam).lower().replace(" ", "").replace("_", "")
            if key == c:
                return FAMILY_ALIASES.get(fam, fam)
    except Exception:
        pass
    # Unknown / stub RUN-IC class: empty suite, never steal OpAmp.
    return ""


def cloud_people_file() -> Path:
    if CLOUD_PEOPLE_PATH is not None:
        return Path(CLOUD_PEOPLE_PATH)
    return Path(TEST_DB_ROOT) / "_ate" / "people.yaml"


def _read_owner_file(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return []
    rows = data.get("owners") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and row.get("id")]


def _merge_owner_rows(
    primary: list[dict[str, Any]], extra: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for src in (primary, extra):
        for row in src:
            oid = str(row.get("id") or "").lower()
            if not oid:
                continue
            if oid not in by_id:
                by_id[oid] = dict(row)
                order.append(oid)
                continue
            cur = by_id[oid]
            for key, val in row.items():
                if key == "parts" and "parts" in cur:
                    continue
                if key not in cur or cur[key] in (None, "", []):
                    cur[key] = val
    return [by_id[i] for i in order]


def load_owners() -> list[dict[str, Any]]:
    git = _read_owner_file(OWNERS_PATH)
    cloud = _read_owner_file(cloud_people_file())
    return _merge_owner_rows(git, cloud)


def save_owners(rows: list[dict[str, Any]]) -> None:
    """Write owners.yaml and #Test_Database/_ate/people.yaml. Does not delete folders."""
    payload = {"owners": list(rows)}
    body = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    OWNERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    OWNERS_PATH.write_text(_OWNERS_PREAMBLE + body, encoding="utf-8")
    try:
        cloud = cloud_people_file()
        cloud.parent.mkdir(parents=True, exist_ok=True)
        cloud.write_text(_OWNERS_PREAMBLE + body, encoding="utf-8")
    except OSError:
        pass


def upsert_owner(
    *,
    label: str,
    owner_id: str = "",
    default_family: str = "",
    default_part: str = "",
    default_component: str = "",
    default_package: str = "",
    task: str = "",
    parts: list[str] | None = None,
    update_defaults: bool = False,
) -> dict[str, Any]:
    """Append or update a person in owners.yaml. Never id=all. Never deletes folders."""
    name = str(label or "").strip()
    if not name or name.lower() in ("all", "kevin") or name.startswith("_"):
        raise ValueError("Person folder must be a real name (not All/observer)")
    oid = str(owner_id or "").strip().lower() or owner_id_from_label(name)
    if oid in ("all", "kevin") or not _OWNER_ID_RE.match(oid):
        raise ValueError("Person id must be lowercase ascii (not All/observer)")
    fam = str(default_family or "").strip().lower()
    part_key = str(default_part or "").strip().lower()
    component = str(default_component or "").strip()
    package = str(default_package or "").strip()
    job = str(task or "").strip()
    extra_parts = [str(p).strip().lower() for p in (parts or []) if str(p).strip()]
    if part_key and part_key not in extra_parts:
        extra_parts.append(part_key)
    rows = load_owners()
    found: dict[str, Any] | None = None
    for row in rows:
        rid = str(row.get("id") or "").lower()
        rlab = str(row.get("label") or "")
        if rid == oid or rlab.lower() == name.lower():
            found = row
            break
    if found is not None:
        if str(found.get("id") or "").lower() in ("all", "kevin"):
            raise ValueError("Observer/All is view-only")
        if str(found.get("role") or "").strip().lower() == "observer":
            raise ValueError("Observer/All is view-only")
        if update_defaults:
            if fam:
                found["default_family"] = fam
            if part_key:
                found["default_part"] = part_key
            if component:
                found["default_component"] = component
            if package:
                found["default_package"] = package
            if job:
                found["task"] = job
            found["label"] = name
            cur_parts = [str(p).strip().lower() for p in (found.get("parts") or []) if str(p).strip()]
            for p in extra_parts:
                if p and p not in cur_parts:
                    cur_parts.append(p)
            found["parts"] = cur_parts
            save_owners(rows)
            return {"owner": found, "action": "updated", "owners": rows}
        return {"owner": found, "action": "exists", "owners": rows}
    row = {
        "id": oid,
        "label": name,
        "default_family": fam or "opamp",
        "default_part": part_key or "rs622",
        "default_component": component or "OpAmp",
        "default_package": package or "TTSOP8",
        "parts": extra_parts,
    }
    if job:
        row["task"] = job
    rows.append(row)
    save_owners(rows)
    return {"owner": row, "action": "created", "owners": rows}


def forget_confirm_phrase(label: str) -> str:
    """Type-to-confirm shield. Not a login password."""
    return f"FORGET {str(label or '').strip()}"


def operator_folder_paths(label: str, *, root: Path | None = None) -> list[Path]:
    """Package/{Operator} trees only. Never _ate or another person's folder."""
    name = str(label or "").strip()
    base = Path(root) if root is not None else Path(TEST_DB_ROOT)
    if not name or not base.is_dir():
        return []
    want = name.casefold()
    hits: list[Path] = []
    try:
        comps = [
            p
            for p in base.iterdir()
            if p.is_dir() and not p.name.startswith(".") and not p.name.startswith("_")
        ]
    except OSError:
        return []
    for comp in comps:
        try:
            parts = [p for p in comp.iterdir() if p.is_dir() and not p.name.startswith(".")]
        except OSError:
            continue
        for part in parts:
            try:
                pkgs = [p for p in part.iterdir() if p.is_dir() and not p.name.startswith(".")]
            except OSError:
                continue
            for pkg in pkgs:
                try:
                    children = list(pkg.iterdir())
                except OSError:
                    continue
                for child in children:
                    if not child.is_dir() or child.name.startswith(".") or child.name.startswith("_"):
                        continue
                    if child.name.casefold() == want:
                        hits.append(child)
    return hits


def _force_rmtree(path: Path) -> None:
    """OneDrive often locks graphs/; chmod then retry. Leftover path raises."""
    def _onerror(func, p, _exc):
        try:
            os.chmod(p, stat.S_IWRITE)
        except OSError:
            pass
        try:
            func(p)
        except OSError:
            pass

    shutil.rmtree(path, onerror=_onerror)
    if path.exists():
        for p in sorted(path.rglob("*"), reverse=True):
            try:
                if p.is_file() or p.is_symlink():
                    try:
                        p.chmod(stat.S_IWRITE)
                    except OSError:
                        pass
                    p.unlink()
                elif p.is_dir():
                    p.rmdir()
            except OSError:
                pass
        try:
            path.rmdir()
        except OSError:
            pass
    if path.exists():
        raise OSError(f"Access is denied: {path}")


def wipe_operator_folders(label: str, *, root: Path | None = None) -> dict[str, Any]:
    """Delete this person's operator folders only. History gone."""
    name = str(label or "").strip()
    if not name or name.casefold() in ("all", "kevin") or name.startswith("_"):
        raise ValueError("Cannot wipe All/observer/_ folders")
    deleted: list[str] = []
    errors: list[str] = []
    for path in operator_folder_paths(name, root=root):
        try:
            _force_rmtree(path)
            deleted.append(str(path))
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    invalidate_tree_cache()
    return {"label": name, "deleted": deleted, "errors": errors, "count": len(deleted)}


def remove_owner(
    owner_id_or_label: str,
    *,
    confirm_text: str = "",
    delete_folders: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """Drop a person from owners.yaml. Folders stay unless delete_folders + phrase."""
    raw = str(owner_id_or_label or "").strip()
    if not raw or raw.lower() in ("all", "kevin"):
        raise ValueError("Cannot remove All/observer")
    rows = load_owners()
    keep: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for row in rows:
        rid = str(row.get("id") or "").lower()
        rlab = str(row.get("label") or "")
        if rid == "all":
            keep.append(row)
            continue
        if rid == raw.lower() or rlab.lower() == raw.lower():
            removed = row
            continue
        keep.append(row)
    if removed is None:
        raise ValueError(f"No person {raw!r} in owners.yaml")
    if str(removed.get("id") or "").lower() in ("all", "kevin"):
        raise ValueError("Cannot remove All/observer")
    if str(removed.get("role") or "").strip().lower() == "observer":
        raise ValueError("Cannot remove All/observer")
    label = str(removed.get("label") or raw).strip()
    want = forget_confirm_phrase(label)
    if str(confirm_text or "") != want:
        raise ValueError(f"Type {want} to remove this person")
    wipe: dict[str, Any] = {}
    if delete_folders:
        wipe = wipe_operator_folders(label, root=root)
    save_owners(keep)
    return {
        "removed": removed,
        "owners": keep,
        "folders_deleted": list(wipe.get("deleted") or []),
        "folder_count": int(wipe.get("count") or 0),
        "folder_errors": list(wipe.get("errors") or []),
    }


def _find_owner_row(rows: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    name = str(label or "").strip()
    if not name:
        return None
    oid = owner_id_from_label(name)
    for row in rows:
        rid = str(row.get("id") or "").lower()
        rlab = str(row.get("label") or "")
        if rid == oid or rlab.lower() == name.lower():
            return row
    return None


def replace_owner_parts(
    *,
    label: str,
    parts: list[str],
    default_family: str = "",
    default_part: str = "",
    default_component: str = "",
    default_package: str = "",
    task: str = "",
) -> dict[str, Any]:
    """Set owners.yaml parts: to exactly this list. Never deletes folders."""
    keys = []
    seen: set[str] = set()
    for p in parts or []:
        k = str(p or "").strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        keys.append(k)
    first = keys[0] if keys else ""
    created = upsert_owner(
        label=label,
        default_family=default_family,
        default_part=default_part or first,
        default_component=default_component,
        default_package=default_package,
        task=task or (first.upper() if first else ""),
        parts=keys,
        update_defaults=True,
    )
    rows = load_owners()
    found = _find_owner_row(rows, label)
    if found is None:
        raise ValueError(f"No person {label!r} in owners.yaml")
    found["parts"] = list(keys)
    if first:
        found["default_part"] = first
        if not str(found.get("task") or "").strip():
            found["task"] = first.upper()
    save_owners(rows)
    return {"owner": found, "action": created.get("action") or "updated", "owners": rows}


def unassign_owner_parts(label: str, part_keys: list[str]) -> dict[str, Any]:
    """Drop part keys from owners.yaml parts: only. Never deletes Version folders."""
    name = str(label or "").strip()
    if not name or name.lower() in ("all", "kevin") or name.startswith("_"):
        raise ValueError("Person folder must be a real name (not All/observer)")
    drop = {str(p or "").strip().lower() for p in (part_keys or []) if str(p or "").strip()}
    if not drop:
        rows = load_owners()
        found = _find_owner_row(rows, name)
        if found is None:
            raise ValueError(f"No person {name!r} in owners.yaml")
        return {"owner": found, "action": "unchanged", "owners": rows, "unassigned": []}
    rows = load_owners()
    found = _find_owner_row(rows, name)
    if found is None:
        raise ValueError(f"No person {name!r} in owners.yaml")
    if str(found.get("id") or "").lower() in ("all", "kevin"):
        raise ValueError("Observer/All is view-only")
    if str(found.get("role") or "").strip().lower() == "observer":
        raise ValueError("Observer/All is view-only")
    cur = [str(p).strip().lower() for p in (found.get("parts") or []) if str(p).strip()]
    kept = [p for p in cur if p not in drop]
    removed = [p for p in cur if p in drop]
    found["parts"] = kept
    save_owners(rows)
    return {"owner": found, "action": "unassigned", "owners": rows, "unassigned": removed}


def remember_operator(
    operator: str,
    *,
    component: str = "",
    part: str = "",
    package: str = "",
    family: str = "",
    update_defaults: bool = False,
) -> str:
    """Create owners.yaml row for a new person, then return folder label."""
    raw = str(operator or "").strip()
    if not raw or raw.lower() in ("all", "kevin", "ate") or raw == UNASSIGNED_OPERATOR or raw.startswith("_"):
        return require_write_operator(raw)
    fam = str(family or "").strip() or family_for_component(component)
    upsert_owner(
        label=raw,
        default_family=fam,
        default_part=str(part or "").strip().lower(),
        default_component=str(component or "").strip(),
        default_package=str(package or "").strip(),
        task=str(part or "").strip().upper(),
        update_defaults=update_defaults,
    )
    return require_write_operator(raw)


def get_context() -> DbContext:
    global _active
    with _lock:
        if _active is None:
            _active = default_context()
        return _active


def set_context(
    *,
    component: Optional[str] = None,
    part: Optional[str] = None,
    package: Optional[str] = None,
    operator: Optional[str] = None,
    version: Optional[str] = None,
    model: Optional[str] = None,
    part_key: Optional[str] = None,
    year: Optional[str] = None,
    sample_size: Optional[int] = None,
) -> DbContext:
    global _active
    with _lock:
        cur = _active or default_context()
        next_part = part or cur.part
        # Derive part_key from part name when yaml exists (rs29511 / rs1g08 / rs622)
        if part_key:
            pk = part_key
        else:
            candidate = str(next_part or "").strip().lower()
            if candidate and (PARTS_DIR / f"{candidate}.yaml").is_file():
                pk = candidate
            else:
                pk = cur.part_key
        m, pkg, sample = _model_from_part_yaml(pk)
        next_op = operator if operator is not None else cur.operator
        next_op = require_write_operator(next_op)
        ui_model = str(model or "").strip()
        part_u = str(next_part or "").strip().upper()
        stale_ui = bool(
            ui_model
            and part_u
            and part_u not in ui_model.upper()
            and ui_model.upper() not in part_u
        )
        ctx = DbContext(
            component=component or cur.component,
            part=next_part,
            package=package or (pkg if pk != cur.part_key else cur.package) or pkg,
            operator=next_op,
            version=version or cur.version,
            model=(ui_model if ui_model and not stale_ui else "") or m or cur.model,
            sample_size=int(
                sample_size
                if sample_size is not None
                else (sample if pk != cur.part_key else cur.sample_size or sample)
            ),
            part_key=pk,
            year=year if year is not None else cur.year,
        )
        # Sync identity fields from sheet_map if present.
        sm = ctx.load_sheet_map()
        if sm:
            ctx.component = str(sm.get("component") or ctx.component)
            ctx.part = str(sm.get("part") or ctx.part)
            ctx.package = str(sm.get("package") or ctx.package)
            if sm.get("operator"):
                ctx.operator = require_write_operator(str(sm.get("operator")))
            ctx.version = str(sm.get("version") or ctx.version)
            if sm.get("sample_size"):
                ctx.sample_size = int(sm["sample_size"])
        try:
            prefs = load_run_prefs(ctx)
            if prefs.get("sample_size"):
                ctx.sample_size = int(prefs["sample_size"])
        except Exception:
            pass
        ctx.ensure_tree()
        _active = ctx
        return ctx


_TREE_TTL_S = 8.0
_TREE_CACHE: dict[str, Any] = {"t": 0.0, "root": "", "data": None}


def invalidate_tree_cache() -> None:
    _TREE_CACHE["t"] = 0.0
    _TREE_CACHE["root"] = ""
    _TREE_CACHE["data"] = None


def list_tree(root: Optional[Path] = None, *, force: bool = False) -> dict[str, Any]:
    """Scan #Test_Database into component → part → package → operator → versions."""
    base = Path(root) if root else TEST_DB_ROOT
    key = str(base)
    now = time.monotonic()
    if (
        root is None
        and not force
        and _TREE_CACHE["data"] is not None
        and _TREE_CACHE["root"] == key
        and (now - float(_TREE_CACHE["t"])) < _TREE_TTL_S
    ):
        return _TREE_CACHE["data"]
    tree: dict[str, Any] = {"root": str(base), "components": {}}
    if not base.is_dir():
        if root is None:
            _TREE_CACHE.update(t=now, root=key, data=tree)
        return tree
    def _live_dirs(parent: Path, *, keep: frozenset[str] | None = None):
        keep = keep or frozenset()
        return sorted(
            p
            for p in parent.iterdir()
            if p.is_dir()
            and not p.name.startswith(".")
            and (not p.name.startswith("_") or p.name in keep)
        )

    for comp in _live_dirs(base):
        parts: dict[str, Any] = {}
        for part in _live_dirs(comp):
            if part.name.lower() == "stub":
                continue
            packages: dict[str, Any] = {}
            for pkg in _live_dirs(part):
                operators: dict[str, Any] = {}
                for child in _live_dirs(pkg, keep=frozenset({UNASSIGNED_OPERATOR})):
                    # Legacy: Package/Version_N
                    if is_campaign_dir(child) and is_version_name(child.name):
                        op_key = UNASSIGNED_OPERATOR
                        ops = operators.setdefault(op_key, {"versions": []})
                        if child.name not in ops["versions"]:
                            ops["versions"].append(child.name)
                        continue
                    # New: Package/Operator/Version_N
                    versions: list[str] = []
                    for ver in sorted(p for p in child.iterdir() if p.is_dir()):
                        if is_campaign_dir(ver):
                            versions.append(ver.name)
                    if versions or is_campaign_dir(child):
                        operators[child.name] = {"versions": versions}
                packages[pkg.name] = {"operators": operators}
            parts[part.name] = {"packages": packages}
        tree["components"][comp.name] = {"parts": parts}
    if root is None:
        _TREE_CACHE.update(t=now, root=key, data=tree)
    return tree


def find_campaign_root(
    component: str,
    part: str,
    package: str,
    version: str = "Version_1",
    *,
    operator: Optional[str] = None,
    base: Optional[Path] = None,
) -> Optional[Path]:
    """Prefer Package/Operator/Version; fall back to legacy Package/Version."""
    root = Path(base) if base else TEST_DB_ROOT
    pkg = root / component / part / package
    if operator:
        try:
            op = require_write_operator(operator)
        except ValueError:
            op = str(operator)
        cand = pkg / op / version
        if cand.is_dir():
            return cand
    # Any operator folder that owns this version
    if pkg.is_dir():
        for child in sorted(pkg.iterdir()):
            if not child.is_dir() or is_version_name(child.name):
                continue
            cand = child / version
            if cand.is_dir():
                return cand
        legacy = pkg / version
        if legacy.is_dir():
            return legacy
    return None



def list_test_folders(ctx: Optional[DbContext] = None) -> list[dict[str, Any]]:
    ctx = ctx or get_context()
    sm = ctx.load_sheet_map()
    tests = sm.get("tests") or {}
    rows: list[dict[str, Any]] = []
    if isinstance(tests, dict):
        for key, entry in tests.items():
            if not isinstance(entry, dict):
                continue
            folder = str(entry.get("folder") or key)
            rows.append(
                {
                    "key": key,
                    "folder": folder,
                    "excel_sheet": entry.get("excel_sheet"),
                    "fixture_mode": entry.get("fixture_mode"),
                    "automated": bool(entry.get("automated", False)),
                    "dut_iterations": int(entry.get("dut_iterations") or ctx.sample_size),
                    "path": str(ctx.test_folder(folder)),
                    "photo_path": ctx.photo_preview(folder, 1),
                }
            )
    return rows


def artifact_name(
    test_key: str,
    dut_index: int,
    variant: str,
    *,
    timestamp: Optional[str] = None,
    ext: str = "jpg",
) -> str:
    ts = timestamp or datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")
    return f"{test_key}_{int(dut_index)}_{variant}_{ts}.{ext.lstrip('.')}"


def _norm_walk_order(raw: Any) -> str:
    return "dut" if str(raw or "channel").strip().lower().startswith("dut") else "channel"


def _norm_sample_size(raw: Any, default: int = 4) -> int:
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = default
    return max(1, min(16, n))


def _norm_probe_channels(raw: Any) -> list[str]:
    from ate.core.specs import normalize_probe_channels

    return normalize_probe_channels(raw)


def load_run_prefs(ctx: Optional["DbContext"] = None) -> dict[str, Any]:
    """Campaign walk-order / DUT count / probe ticks. Not a #Test_Database folder axis."""
    ctx = ctx or get_context()
    path = ctx.run_prefs_path()
    data: Any = {}
    if path.is_file():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    out: dict[str, Any] = {"walk_order": _norm_walk_order(data.get("walk_order"))}
    if data.get("sample_size") is not None:
        out["sample_size"] = _norm_sample_size(data.get("sample_size"))
    chans = _norm_probe_channels(data.get("probe_channels") or data.get("channels"))
    if chans:
        out["probe_channels"] = chans
    return out


def save_run_prefs(
    walk_order: str = "",
    *,
    sample_size: Any = None,
    probe_channels: Any = None,
    ctx: Optional["DbContext"] = None,
) -> dict[str, Any]:
    ctx = ctx or get_context()
    ctx.manifest_dir().mkdir(parents=True, exist_ok=True)
    cur = load_run_prefs(ctx)
    if str(walk_order or "").strip():
        cur["walk_order"] = _norm_walk_order(walk_order)
    if sample_size is not None and str(sample_size).strip() != "":
        cur["sample_size"] = _norm_sample_size(sample_size)
    if probe_channels is not None:
        chans = _norm_probe_channels(probe_channels)
        if chans:
            cur["probe_channels"] = chans
    ctx.run_prefs_path().write_text(
        yaml.safe_dump(cur, sort_keys=False),
        encoding="utf-8",
    )
    if cur.get("sample_size"):
        ctx.sample_size = int(cur["sample_size"])
        try:
            ctx.ensure_tree()
        except Exception:
            pass
    return cur


_TEST_PARAM_FLOATS = (
    "vcc",
    "vccb",
    "vcc_start",
    "vcc_stop",
    "vcc_step",
    "freq_hz",
    "freq_start",
    "freq_stop",
    "freq_step",
    "amp_vpp",
    "settle_s",
    "timeout_s",
    "dwell_s",
    "vin_step",
    "stable_eps_A",
    "icc_vcc_step",
    "icc_vcc_start",
    "icc_vcc_stop",
)
_TEST_PARAM_INTS = ("n_repeats", "logic_inputs", "sample_size")
_TEST_PARAM_STRS = ("icc_vcc_mode", "vcc_mode")


def _clean_float_list(raw: Any, *, cap: int = 41) -> list[float]:
    if isinstance(raw, str):
        raw = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    if not isinstance(raw, list):
        return []
    out: list[float] = []
    for item in raw:
        try:
            out.append(float(item))
        except (TypeError, ValueError):
            continue
        if len(out) >= cap:
            break
    return out


def _clean_rails(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    mode = str(raw.get("mode") or "").strip().lower()
    out: dict[str, Any] = {}
    if mode in ("single", "dual"):
        out["mode"] = mode
    psu_raw = raw.get("psu")
    psu: list[dict[str, Any]] = []
    if isinstance(psu_raw, list):
        for row in psu_raw[:6]:
            if not isinstance(row, dict):
                continue
            try:
                ch = int(row.get("ch"))
            except (TypeError, ValueError):
                continue
            if ch < 1 or ch > 3:
                continue
            entry: dict[str, Any] = {"ch": ch}
            if row.get("name") not in (None, ""):
                entry["name"] = str(row["name"]).strip()[:32]
            if row.get("volts") not in (None, ""):
                try:
                    entry["volts"] = float(row["volts"])
                except (TypeError, ValueError):
                    pass
            if row.get("digits") not in (None, ""):
                try:
                    entry["digits"] = max(0, min(6, int(row["digits"])))
                except (TypeError, ValueError):
                    pass
            psu.append(entry)
    if psu:
        out["psu"] = psu
    return out


def _clean_spec_rows(raw: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for row in raw:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        item: dict[str, Any] = {"id": str(row["id"]).strip()}
        for key in ("min", "max", "typ"):
            if row.get(key) in (None, ""):
                continue
            try:
                item[key] = float(row[key])
            except (TypeError, ValueError):
                pass
        if row.get("unit"):
            item["unit"] = str(row["unit"]).strip()
        out.append(item)
    return out


def _clean_test_param_block(raw: Any) -> dict[str, Any]:
    src = raw if isinstance(raw, dict) else {}
    out: dict[str, Any] = {}
    for key in _TEST_PARAM_FLOATS:
        if src.get(key) in (None, ""):
            continue
        try:
            out[key] = float(src[key])
        except (TypeError, ValueError):
            pass
    for key in _TEST_PARAM_INTS:
        if src.get(key) in (None, ""):
            continue
        try:
            out[key] = int(src[key])
        except (TypeError, ValueError):
            pass
    if "logic_inputs" in out:
        n = int(out["logic_inputs"])
        # ponytail: DG822 has 2 AWG CH; n>2 needs pause_hook rewire / mux (ceiling 8).
        out["logic_inputs"] = max(1, min(8, n))
    vcc_list = _clean_float_list(src.get("vcc_list"))
    if vcc_list:
        out["vcc_list"] = vcc_list
    icc_list = _clean_float_list(src.get("icc_vcc_list"), cap=80)
    if icc_list:
        out["icc_vcc_list"] = icc_list
    for key in _TEST_PARAM_STRS:
        raw = str(src.get(key) or "").strip().lower()
        if not raw:
            continue
        if raw in ("custom", "points"):
            raw = "list"
        if raw in ("sweep", "0.1", "step0.1"):
            raw = "step"
        if raw in ("named", "step", "list", "grid"):
            out[key] = raw
    levels = _clean_float_list(src.get("levels"), cap=8)
    if levels:
        out["levels"] = levels
    rails = _clean_rails(src.get("rails"))
    if not rails and (
        src.get("rails_mode") not in (None, "") or src.get("rails_psu") not in (None, "")
    ):
        # UI flat fields -> rails dict
        mode = str(src.get("rails_mode") or "").strip().lower()
        flat: dict[str, Any] = {}
        if mode in ("single", "dual"):
            flat["mode"] = mode
        psu_txt = str(src.get("rails_psu") or "").strip()
        if psu_txt:
            # "1:VCC:3.300,2:VSS:-3.300" or "1:3.300"
            rows = []
            for part in psu_txt.replace(";", ",").split(","):
                part = part.strip()
                if not part:
                    continue
                bits = [b.strip() for b in part.split(":")]
                try:
                    ch = int(bits[0])
                except (TypeError, ValueError, IndexError):
                    continue
                entry: dict[str, Any] = {"ch": ch}
                if len(bits) == 2:
                    try:
                        entry["volts"] = float(bits[1])
                    except (TypeError, ValueError):
                        entry["name"] = bits[1][:32]
                elif len(bits) >= 3:
                    entry["name"] = bits[1][:32]
                    try:
                        entry["volts"] = float(bits[2])
                    except (TypeError, ValueError):
                        pass
                    if len(bits) >= 4:
                        try:
                            entry["digits"] = int(bits[3])
                        except (TypeError, ValueError):
                            pass
                rows.append(entry)
            if rows:
                flat["psu"] = rows
        rails = _clean_rails(flat)
    if rails:
        out["rails"] = rails
    specs = _clean_spec_rows(src.get("specs"))
    if specs:
        out["specs"] = specs
    for key in ("vcc_grid", "vcc_plan"):
        blob = src.get(key)
        if isinstance(blob, dict):
            out[key] = dict(blob)
    return out


def load_test_params(ctx: Optional["DbContext"] = None) -> dict[str, Any]:
    """This Version only. Not shared parts yaml."""
    ctx = ctx or get_context()
    path = ctx.test_params_path()
    data: Any = {}
    if path.is_file():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    raw = data.get("tests") if isinstance(data.get("tests"), dict) else {}
    tests: dict[str, Any] = {}
    for key, block in raw.items():
        tid = str(key or "").strip().lower()
        if not tid or not tid.replace("_", "").isalnum():
            continue
        cleaned = _clean_test_param_block(block)
        if cleaned:
            tests[tid] = cleaned
    return {"tests": tests}


def save_test_params(
    test_id: str,
    params: dict[str, Any] | None = None,
    *,
    ctx: Optional["DbContext"] = None,
) -> dict[str, Any]:
    ctx = ctx or get_context()
    require_write_operator(ctx.operator)
    ctx.manifest_dir().mkdir(parents=True, exist_ok=True)
    cur = load_test_params(ctx)
    tests = dict(cur.get("tests") or {})
    tid = str(test_id or "").strip().lower()
    if not tid or not tid.replace("_", "").isalnum():
        raise ValueError("test_id required")
    prev = dict(tests.get(tid) or {})
    prev.update(_clean_test_param_block(params or {}))
    if not prev:
        tests.pop(tid, None)
    else:
        tests[tid] = prev
    out = {"tests": tests}
    ctx.test_params_path().write_text(
        yaml.safe_dump(out, sort_keys=False),
        encoding="utf-8",
    )
    return out


def begin_session(
    params: dict[str, Any],
    *,
    instrument_map: Optional[dict[str, str]] = None,
    fixture_plan: Optional[list[dict[str, Any]]] = None,
) -> RunSession:
    global _current_session
    ctx = get_context()
    ctx.ensure_tree()
    ts = datetime.now(MYT).strftime("%Y-%m-%d_%H%M%S")
    ident = ctx.identity()
    p = dict(params or {})
    if not p.get("tags"):
        p["tags"] = list(ident.get("tags") or [])
    if not p.get("boards"):
        p["boards"] = list(ident.get("boards") or [])
    if not p.get("labels"):
        p["labels"] = list(ident.get("labels") or [])
    if not p.get("walk_order"):
        p["walk_order"] = ident.get("walk_order") or "channel"
    label = str(p.get("run_label") or "").strip()
    slug = re.sub(r"[^\w\-]+", "_", label)[:48].strip("_") if label else ""
    sid = f"session_{slug}_{ts}" if slug else f"session_{ts}"
    session = RunSession(
        session_id=sid,
        started_at=datetime.now(MYT).isoformat(timespec="seconds"),
        context=ident,
        params=p,
        instrument_map=dict(instrument_map or {}),
        fixture_plan=list(fixture_plan or []),
    )
    with _lock:
        _current_session = session
    _write_session(session)
    try:
        from ate.core.datalog import sync_report_from_session

        sync_report_from_session(session.to_dict())
    except Exception:
        pass
    return session


def record_step(
    test_id: str,
    *,
    success: bool,
    summary: str = "",
    error: str = "",
    fixture_mode: str = "",
    artifacts: Optional[list[dict[str, Any]]] = None,
    measurements: Optional[list[dict[str, Any]]] = None,
    dut: int | None = None,
    channel: str | None = None,
    data: Optional[dict[str, Any]] = None,
) -> None:
    stamped: list[dict[str, Any]] | None = None
    ok = bool(success)
    if measurements:
        from ate.core.specs import any_fail, enrich_measurement, load_part_specs

        pk = str(get_context().part_key or "")
        specs = load_part_specs(pk)
        stamped = [
            enrich_measurement(dict(m), specs=specs, test_id=test_id)
            for m in measurements
            if isinstance(m, dict)
        ]
        if any_fail(stamped):
            ok = False
    with _lock:
        session = _current_session
        if session is None:
            return
        row: dict[str, Any] = {
            "test_id": test_id,
            "success": ok,
            "summary": summary,
            "error": error,
            "fixture_mode": fixture_mode,
            "at": datetime.now(MYT).isoformat(timespec="seconds"),
        }
        if dut is not None:
            row["dut"] = int(dut)
        if channel:
            row["channel"] = str(channel).strip().upper()
        if stamped:
            row["measurements"] = stamped
        if data:
            inner = data.get("data") if isinstance(data.get("data"), dict) else data
            rows = inner.get("rows") if isinstance(inner, dict) else None
            if isinstance(rows, list) and rows:
                payload: dict[str, Any] = {"rows": rows}
                if isinstance(inner, dict) and inner.get("vcc_sweep"):
                    payload["vcc_sweep"] = inner["vcc_sweep"]
                row["data"] = payload
        session.steps.append(row)
        if artifacts:
            session.artifacts.extend(artifacts)
        snap = session
    _write_session(snap)
    try:
        from ate.core.datalog import sync_report_from_session

        sync_report_from_session(snap.to_dict())
    except Exception:
        pass


def end_session(status: str = "completed") -> Optional[Path]:
    global _current_session
    with _lock:
        session = _current_session
        if session is None:
            return None
        session.finished_at = datetime.now(MYT).isoformat(timespec="seconds")
        session.status = status
        _current_session = None
        snap = session
    path = _write_session(snap)
    try:
        from ate.core.datalog import archive_report, sync_report_from_session

        sync_report_from_session(snap.to_dict())
        archive_report(snap.to_dict())
    except Exception:
        pass
    imap = snap.instrument_map or {}
    sim = any(str(v).upper().startswith("SIM::") for v in imap.values())
    if not sim:
        try:
            from ate.reporting.session_paste import paste_session_photos

            paste_session_photos(snap.to_dict())
        except Exception:
            pass
    try:
        from ate.reporting.session_values import fill_workbook_from_report

        fill_workbook_from_report(ctx=get_context(), demo=sim, copy_golden=True)
    except Exception:
        pass
    try:
        from ate.reporting.golden_workbook import check_golden_workbook

        check_golden_workbook(fix=False)
    except Exception:
        pass
    return path


def current_session() -> Optional[dict[str, Any]]:
    with _lock:
        return None if _current_session is None else _current_session.to_dict()


def _write_session(session: RunSession) -> Path:
    ctx = get_context()
    dest_dir = ctx.sessions_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{session.session_id}.json"
    path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
    return path


def how_to_use() -> dict[str, Any]:
    """Operator-facing orientation: where we are, where photos go, how Excel links."""
    ctx = get_context()
    return {
        "heading": "ATE <-> #Test_Database orchestration",
        "tree": (
            f"{ctx.component} / {ctx.part} / {ctx.package} / {ctx.operator} / {ctx.version} "
            f"(model {ctx.model}, sample_size={ctx.sample_size})"
        ),
        "root": str(ctx.root()),
        "axes": {
            "component": "Family under #Test_Database (OpAmp, Logic, AnalogSwitch, …)",
            "part": "Device under test folder name (RS622)",
            "package": "Package variant (TTSOP8)",
            "operator": "Person folder (Eugene / Ariff / …). All is view-only.",
            "version": "Characterization campaign Version_N (not calendar year)",
            "year": "Optional metadata on the run session only",
            "config": "Fixture / gain mode (BUFFER, G11, G_NEG100 general; G201/G1001 = VOS research only)",
            "model": "Datasheet / lab-report model name (RS622XK)",
        },
        "photos": {
            "pattern": "{TEST}_{DUT}_{VARIANT}_{YYYY-MM-DD_HHMMSS}.jpg",
            "location": str(ctx.root() / "{TestKey}" / "DUT_N" / "screenshots"),
            "example": ctx.photo_preview("ORT", 1),
            "excel_link": str(ctx.sheet_map_path()),
        },
        "excel": {
            "lab_report": str(ctx.lab_report_path()),
            "mcp": "user-excel (excel_describe_sheets / excel_read_sheet / …)",
            "note": "sheet_map.yaml maps each test folder → Excel sheet + paste anchors",
        },
        "sessions": {
            "folder": str(ctx.sessions_dir()),
            "note": "Each START writes session_YYYY-MM-DD_HHMMSS.json with full identity + results",
        },
        "orchestration": [
            "1. Select Component / Part / Package / Version in Setup",
            "2. Discover → Open Session (instruments)",
            "3. Select tests — runner batches by fixture mode",
            "4. Operator Continue only when board/config must change",
            "5. Photos land under DUT_N/screenshots with parseable names",
            "6. ORT (and later other tests) paste into lab report via sheet_map anchors",
            "7. Session JSON records who/what/where for every run",
            "8. Results -> Run ledger lists those JSON files for every operator on this SKU",
            "9. Central tree is #Test_Database (SharePoint/OneDrive sync that folder; A13 MCP stays parked)",
        ],
    }
