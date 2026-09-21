"""Golden lab workbooks as references -- one real book per SKU, not one Parameter table.

Sources (available only, no scrape):
  1. #Test_Database/{Component}/{Part}/{Package}/{Operator}/workbook/*.xlsx
  2. inventory reports_root Product Testing Report xlsx

Stubs (provision Parameter/DUT grid) are never the golden.
Copies live under #Test_Database/_ate/goldens/. Git does not store the xlsx.

  python -m ate.core.golden_refs
  python -m ate.core.check_golden_refs
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from ate.core.paths import TEST_DB_ROOT, resolve_portable, store_portable

MYT_INDEX = "index.yaml"
_SKIP_NAME = ("_filled", "_demo", ".bak_", "datalog")
_META = frozenset({"summary", "checklist", "sweep", "sheet1", "status"})


def goldens_root() -> Path:
    return Path(TEST_DB_ROOT) / "_ate" / "goldens"


def index_path() -> Path:
    return goldens_root() / MYT_INDEX


def _fold(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name or "").lower())


def _copy_readable(src: Path) -> Path:
    """OneDrive/Excel may lock the live xlsx. Copy then read."""
    dest = Path(tempfile.mkdtemp(prefix="ate_golden_")) / src.name
    shutil.copy2(src, dest)
    return dest


def _load_wb(path: Path):
    from openpyxl import load_workbook

    try:
        return load_workbook(path, read_only=True, data_only=False)
    except PermissionError:
        return load_workbook(_copy_readable(path), read_only=True, data_only=False)


def inspect_workbook(path: Path) -> dict[str, Any]:
    """One open: stub flag, sheet names, A1 samples."""
    if not path.is_file():
        return {"stub": True, "sheets": [], "a1": {}}
    size = path.stat().st_size
    if size < 200:
        return {"stub": True, "sheets": [], "a1": {}, "bytes": size}
    wb = _load_wb(path)
    try:
        names = list(wb.sheetnames)
        a1 = {n: str(wb[n]["A1"].value or "").strip()[:80] for n in names[:24]}
        stub = False
        if "Summary" in names:
            note = str(wb["Summary"]["B8"].value or "")
            if "Clean golden template" in note:
                stub = True
            elif str(wb["Summary"]["A1"].value or "").strip() == "Device":
                samples = [
                    str(wb[n]["A1"].value or "").strip()
                    for n in names
                    if _fold(n) not in _META
                ][:3]
                if samples and all(v == "Parameter" for v in samples):
                    stub = True
        test_a1 = [
            str(a1.get(n) or "").strip().lower()
            for n in names
            if _fold(n) not in _META
        ]
        if test_a1 and all(
            "(stub)" in v or v in ("parameter", "") for v in test_a1
        ):
            stub = True
        return {"stub": stub, "sheets": names, "a1": a1, "bytes": size}
    finally:
        wb.close()


def is_stub_workbook(path: Path) -> bool:
    """Provision stub: Parameter/DUT grid or 'Clean golden template' note."""
    return bool(inspect_workbook(path).get("stub"))


def _skip_xlsx(path: Path) -> bool:
    n = path.name.lower()
    if path.suffix.lower() != ".xlsx" or path.name.startswith("~"):
        return True
    if any(tok in n for tok in _SKIP_NAME):
        return True
    parts = {p.lower() for p in path.parts}
    if "files" in parts and "datalog" in n:
        return True
    if "raw data" in str(path).lower():
        return True
    if "_retired" in "".join(path.parts).lower():
        return True
    return False


def _parse_campaign_xlsx(path: Path) -> dict[str, str]:
    """#Test_Database/Component/Part/Package/Operator/Version_N/workbook/file.xlsx"""
    parts = list(path.parts)
    try:
        i = parts.index("workbook")
    except ValueError:
        return {}
    if i < 5:
        return {}
    version, operator, package, part, component = parts[i - 1], parts[i - 2], parts[i - 3], parts[i - 4], parts[i - 5]
    if not str(version).lower().startswith("version"):
        return {}
    return {
        "component": str(component),
        "part": str(part).upper(),
        "package": str(package),
        "operator": str(operator),
        "version": str(version),
    }


def _score(path: Path, *, stub: bool, sheets: list[str], a1: dict[str, str], kind: str) -> int:
    if stub:
        return 0
    score = min(path.stat().st_size // 1024, 8000)
    folds = {_fold(s) for s in sheets}
    if "vix" in folds or "vox" in folds:
        score += 2000
    if "slewrate" in folds or "gbw" in folds:
        score += 2000
    a1_blob = " ".join(a1.values()).lower()
    if "test parameter" in a1_blob or "version summary" in a1_blob:
        score += 400
    if kind == "report_drop":
        score += 2000
    return score


_SKIP_DROP_DIRS = frozenset({"files", "raw data", "my tests"})


def sync_report_drop() -> dict[str, Any]:
    """Extract lab xlsx from Test Reports.zip into reports_root. Skip datalogs/PNGs."""
    from ate.core.new_product import reports_root, reports_zip

    dest = reports_root()
    zpath = reports_zip()
    copied = 0
    skipped = 0
    if dest and str(dest):
        dest.mkdir(parents=True, exist_ok=True)
    if not zpath.is_file() or not dest:
        return {"ok": False, "copied": 0, "zip": str(zpath), "dest": str(dest)}
    from zipfile import ZipFile

    with ZipFile(zpath) as zf:
        for name in zf.namelist():
            n = name.replace("\\", "/")
            if n.endswith("/") or not n.lower().endswith(".xlsx"):
                continue
            bits = [p.lower() for p in n.split("/")]
            if any(p in _SKIP_DROP_DIRS for p in bits):
                skipped += 1
                continue
            if "datalog" in n.lower() or "[outdated]" in n.lower():
                skipped += 1
                continue
            rel = n
            prefix = "product testing report/"
            if rel.lower().startswith(prefix):
                rel = rel[len(prefix) :]
            if not rel:
                continue
            out = dest / rel
            if out.is_file() and out.stat().st_size > 0:
                skipped += 1
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(name) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
            copied += 1
    return {"ok": True, "copied": copied, "skipped": skipped, "zip": str(zpath), "dest": str(dest)}


def install_lab_report(
    src: Path,
    *,
    part: str,
    package: str = "SC70-5",
    operator: str = "Ariff",
    category_id: str = "logic",
) -> dict[str, Any]:
    """Copy a senior xlsx into the report drop + this operator's workbook. Probe sheet_map."""
    from ate.core.new_product import campaign_root, category_by_id, ensure_product, reports_root
    from ate.core.provision_operator import _write_sheet_map_from_xlsx

    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(src)
    part_u = str(part or "").strip().upper()
    drop = reports_root() / part_u / src.name
    drop.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != drop.resolve():
        shutil.copy2(src, drop)
    out = ensure_product(
        category_id=category_id,
        part=part_u,
        package=package,
        model=part_u,
        sample_size=4,
        operator=operator,
        open_folder=False,
        apply=False,
    )
    root = Path(str(out.get("root") or ""))
    if not root.is_dir():
        cat = category_by_id(category_id)
        root = campaign_root(
            str(cat["component"]), part_u, package, "Version_1", operator=operator
        )
    dest = root / "workbook" / f"{part_u}_Lab_Report.xlsx"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    sheets = _write_sheet_map_from_xlsx(
        root, dest, part=part_u, package=package, operator=operator
    )
    return {
        "ok": True,
        "drop": str(drop),
        "workbook": str(dest),
        "root": str(root),
        "sheets": sheets,
    }


def collect_available() -> list[dict[str, Any]]:
    """Scan live campaign books + Product Testing Report drop."""
    from ate.core.new_product import load_inventory, part_key_for, reports_root, resolve_inventory_report

    rows: list[dict[str, Any]] = []
    root = Path(TEST_DB_ROOT)
    if root.is_dir():
        for xlsx in root.rglob("*.xlsx"):
            if _skip_xlsx(xlsx):
                continue
            if "workbook" not in xlsx.parts:
                continue
            if "_ate" in xlsx.parts:
                continue
            meta = _parse_campaign_xlsx(xlsx)
            if not meta:
                continue
            if str(meta.get("operator") or "").startswith("_"):
                continue
            if any(str(p).lower().startswith("_retired") for p in xlsx.parts):
                continue
            if xlsx.name.lower().startswith("smoke"):
                continue
            try:
                info = inspect_workbook(xlsx)
            except Exception as exc:
                rows.append({**meta, "path": str(xlsx), "error": str(exc)[:120], "stub": True, "score": 0})
                continue
            stub = bool(info.get("stub"))
            sheets = list(info.get("sheets") or [])
            a1 = dict(info.get("a1") or {})
            rows.append(
                {
                    **meta,
                    "part_key": part_key_for(meta["part"]),
                    "path": str(xlsx),
                    "bytes": int(info.get("bytes") or xlsx.stat().st_size),
                    "stub": stub,
                    "sheets": sheets,
                    "a1": a1,
                    "score": _score(xlsx, stub=stub, sheets=sheets, a1=a1, kind="campaign"),
                    "kind": "campaign",
                }
            )
    for inv in load_inventory():
        src = resolve_inventory_report(inv)
        if src is None or not src.is_file() or _skip_xlsx(src):
            continue
        part = str(inv.get("part") or "").upper()
        package = str(inv.get("package") or "").strip() or "SOT23"
        try:
            info = inspect_workbook(src)
        except Exception as exc:
            rows.append(
                {
                    "part": part,
                    "package": package,
                    "part_key": part_key_for(part),
                    "path": str(src),
                    "error": str(exc)[:120],
                    "stub": True,
                    "score": 0,
                    "kind": "report_drop",
                }
            )
            continue
        stub = bool(info.get("stub"))
        sheets = list(info.get("sheets") or [])
        a1 = dict(info.get("a1") or {})
        rows.append(
            {
                "component": str(inv.get("category") or ""),
                "part": part,
                "package": package,
                "operator": "report_drop",
                "part_key": part_key_for(part),
                "path": str(src),
                "bytes": int(info.get("bytes") or src.stat().st_size),
                "stub": stub,
                "sheets": sheets,
                "a1": a1,
                "score": _score(src, stub=stub, sheets=sheets, a1=a1, kind="report_drop"),
                "kind": "report_drop",
            }
        )
    seen = {str(r.get("path") or "") for r in rows}
    drop_root = reports_root()
    if drop_root.is_dir():
        for xlsx in drop_root.rglob("*.xlsx"):
            if str(xlsx) in seen or _skip_xlsx(xlsx):
                continue
            bits = {p.lower() for p in xlsx.parts}
            if bits & _SKIP_DROP_DIRS:
                continue
            try:
                rel = xlsx.relative_to(drop_root)
                part = str(rel.parts[0]).upper() if len(rel.parts) >= 2 else ""
            except ValueError:
                part = ""
            if not part.startswith("RS") and not part.startswith("LM"):
                continue
            pkg = "SC70-5"
            for inv in load_inventory():
                if str(inv.get("part") or "").upper() == part and str(inv.get("package") or "").strip():
                    pkg = str(inv.get("package")).strip()
                    break
            try:
                info = inspect_workbook(xlsx)
            except Exception:
                continue
            stub = bool(info.get("stub"))
            sheets = list(info.get("sheets") or [])
            a1 = dict(info.get("a1") or {})
            rows.append(
                {
                    "component": "",
                    "part": part,
                    "package": pkg,
                    "operator": "report_drop",
                    "part_key": part_key_for(part),
                    "path": str(xlsx),
                    "bytes": int(info.get("bytes") or xlsx.stat().st_size),
                    "stub": stub,
                    "sheets": sheets,
                    "a1": a1,
                    "score": _score(xlsx, stub=stub, sheets=sheets, a1=a1, kind="report_drop"),
                    "kind": "report_drop",
                }
            )
    return rows


def _best_by_key(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("stub") or int(row.get("score") or 0) <= 0:
            continue
        pk = str(row.get("part_key") or "").lower()
        if not pk:
            continue
        pkg = str(row.get("package") or "").strip() or "_"
        for key in (f"{pk}|{pkg}", pk):
            cur = best.get(key)
            if cur is None or int(row.get("score") or 0) > int(cur.get("score") or 0):
                best[key] = row
    return best


def store_goldens(*, write: bool = True) -> dict[str, Any]:
    """Copy winning senior books into #Test_Database/_ate/goldens."""
    from ate.core.new_product import category_by_id

    rows = collect_available()
    best = _best_by_key(rows)
    dest_root = goldens_root()
    index: dict[str, Any] = {"parts": {}, "n_scanned": len(rows)}
    stored = 0
    if write:
        dest_root.mkdir(parents=True, exist_ok=True)
    for key, row in sorted(best.items()):
        src = Path(str(row.get("path") or ""))
        if not src.is_file():
            continue
        pk = str(row.get("part_key") or "").lower()
        pkg = str(row.get("package") or "SOT23")
        cat = str(row.get("component") or "")
        try:
            component = str(category_by_id(cat).get("component") or cat or "Logic")
        except Exception:
            component = cat or "Logic"
        dest = dest_root / component / str(row.get("part") or pk).upper() / pkg / "golden.xlsx"
        if write:
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dest)
            except PermissionError:
                shutil.copy2(_copy_readable(src), dest)
        stored += 1
        slot = index["parts"].setdefault(pk, {"packages": {}})
        slot["packages"][pkg] = {
            "source": store_portable(src),
            "golden": store_portable(dest),
            "sheets": row.get("sheets") or [],
            "bytes": row.get("bytes"),
            "operator": row.get("operator"),
            "kind": row.get("kind"),
            "score": row.get("score"),
        }
        if "default" not in slot:
            slot["default"] = pkg
    if write:
        index_path().write_text(yaml.safe_dump(index, sort_keys=False, allow_unicode=True), encoding="utf-8")
        (goldens_root() / "last_collect.json").write_text(
            json.dumps({"n_scanned": len(rows), "stored": stored, "keys": list(best)}, indent=2, default=str),
            encoding="utf-8",
        )
    index["stored"] = stored
    index["path"] = str(index_path())
    return index


def resolve_golden(part: str, package: str = "") -> Path | None:
    """Path to the stored golden xlsx for this SKU, if collect has run."""
    idx_file = index_path()
    if not idx_file.is_file():
        return None
    data = yaml.safe_load(idx_file.read_text(encoding="utf-8")) or {}
    parts = data.get("parts") if isinstance(data, dict) else {}
    pk = re.sub(r"[^a-z0-9]+", "", str(part or "").lower())
    slot = parts.get(pk) if isinstance(parts, dict) else None
    if not isinstance(slot, dict):
        return None
    pkgs = slot.get("packages") if isinstance(slot.get("packages"), dict) else {}
    pkg = str(package or "").strip()
    if pkg:
        row = pkgs.get(pkg)
        # Do not copy MSOP golden photos onto UQFN (or any other package).
        if not isinstance(row, dict):
            return None
    else:
        row = pkgs.get(str(slot.get("default") or "")) or (
            next(iter(pkgs.values())) if pkgs else None
        )
    if not isinstance(row, dict):
        return None
    path = Path(str(row.get("golden") or ""))
    hit = resolve_portable(str(path), goldens_root(), db_root=Path(TEST_DB_ROOT))
    if hit is not None and hit.is_file():
        return hit
    if path.is_file():
        return path
    root = goldens_root()
    if root.is_dir():
        needle = pk
        named = [p for p in root.rglob("golden.xlsx") if needle in str(p).replace("\\", "/").lower()]
        if pkg:
            pkg_hit = [p for p in named if pkg.lower() in str(p).lower()]
            if pkg_hit:
                return pkg_hit[0]
        if named:
            return named[0]
    return None


def main() -> int:
    drop = sync_report_drop()
    print(f"report drop copied={drop.get('copied')} dest={drop.get('dest')}")
    got = store_goldens(write=True)
    print(f"golden refs stored={got.get('stored')} index={got.get('path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
