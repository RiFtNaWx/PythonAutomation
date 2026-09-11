"""Move Level/LDO off Level/Stub into part folders and track enabled tests.

Dry-run by default. Pass --apply to move/create.

  python -m ate.core.seed_classified_campaigns
  python -m ate.core.seed_classified_campaigns --apply
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

from ate.core.database import require_write_operator
from ate.core.migrate_operator_folders import _pic_label_map
from ate.core.new_product import ensure_product, load_inventory
from ate.core.paths import TEST_DB_ROOT


def _operator_for(part: str, fallback: str = "Eugene") -> str:
    pic = _pic_label_map().get(str(part).upper(), "")
    if pic and not pic.startswith("_"):
        return pic
    return fallback


def _unique_skus() -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in load_inventory():
        cat = str(row.get("category") or "").strip()
        if cat not in ("level", "power"):
            continue
        part = str(row.get("part") or "").strip().upper()
        package = str(row.get("package") or "").strip() or "SOT23"
        key = (part, package)
        if not part or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def plan(root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    src = root / "Logic" / "RS0204"
    dst = root / "Level" / "RS0204"
    if src.is_dir() and not dst.exists():
        actions.append({"op": "move", "src": str(src), "dest": str(dst)})
    elif src.is_dir() and dst.exists():
        actions.append({"op": "skip_move", "src": str(src), "dest": str(dst)})
    stub = root / "Level" / "Stub"
    if stub.is_dir():
        dest = root / "Level" / "_retired_Stub"
        n = 2
        while dest.exists():
            dest = root / "Level" / f"_retired_Stub_{n}"
            n += 1
        actions.append({"op": "retire_stub", "src": str(stub), "dest": str(dest)})
    for row in _unique_skus():
        part = str(row.get("part") or "").strip().upper()
        package = str(row.get("package") or "").strip() or "SOT23"
        cat = str(row.get("category") or "")
        op = _operator_for(part)
        actions.append(
            {
                "op": "ensure",
                "category": cat,
                "part": part,
                "package": package,
                "model": str(row.get("model") or part),
                "operator": op,
            }
        )
    return actions


def apply_plan(actions: list[dict[str, Any]], *, apply: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for act in actions:
        row = dict(act)
        if not apply:
            row["status"] = "dry_run"
            out.append(row)
            continue
        op = act["op"]
        if op == "move" or op == "retire_stub":
            src = Path(act["src"])
            dest = Path(act["dest"])
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            if op == "move":
                for sm in dest.rglob("sheet_map.yaml"):
                    text = sm.read_text(encoding="utf-8")
                    if "component: Logic" in text:
                        sm.write_text(
                            text.replace("component: Logic", "component: Level", 1),
                            encoding="utf-8",
                        )
            row["status"] = "moved"
        elif op == "ensure":
            ensure_product(
                category_id=str(act["category"]),
                part=str(act["part"]),
                package=str(act["package"]),
                model=str(act.get("model") or ""),
                operator=str(act["operator"]),
                open_folder=False,
                apply=False,
            )
            row["status"] = "ensured"
        else:
            row["status"] = "skipped"
        out.append(row)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(TEST_DB_ROOT)
    require_write_operator("Eugene")
    actions = plan(root)
    results = apply_plan(actions, apply=bool(args.apply))
    moved = sum(1 for r in results if r.get("status") == "moved")
    ensured = sum(1 for r in results if r.get("status") == "ensured")
    mode = "apply" if args.apply else "dry-run"
    print(f"OK seed-classified {mode}: actions={len(results)} moved={moved} ensured={ensured}")
    for row in results:
        print(f"  {row.get('status')}: {row.get('op')} {row.get('part', '')} {row.get('src', row.get('package', ''))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
