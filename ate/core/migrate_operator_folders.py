"""One-shot migrate Package/Version_* -> Package/{Operator}/Version_*.

Dry-run by default. Pass --apply to move folders (no copy, no xlsx duplicate).

PIC comes from ate/config/inventory.yaml `pic` mapped through owners.yaml labels.
Unknown parts -> _unassigned.

Run:
  python -m ate.core.migrate_operator_folders
  python -m ate.core.migrate_operator_folders --apply
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

from ate.core.database import (
    UNASSIGNED_OPERATOR,
    is_campaign_dir,
    is_version_name,
    load_owners,
    operator_folder_label,
)
from ate.core.new_product import load_inventory
from ate.core.paths import TEST_DB_ROOT


def _pic_label_map() -> dict[str, str]:
    """part upper -> operator folder label."""
    owners_by_id = {str(o.get("id") or "").lower(): str(o.get("label") or o.get("id")) for o in load_owners()}
    out: dict[str, str] = {}
    for row in load_inventory():
        part = str(row.get("part") or "").strip().upper()
        pic = str(row.get("pic") or "").strip().lower()
        if not part:
            continue
        # Empty PIC must not clobber an assigned SKU of the same part.
        if not pic or pic == "all":
            out.setdefault(part, UNASSIGNED_OPERATOR)
            continue
        if pic in owners_by_id:
            out[part] = owners_by_id[pic]
        else:
            try:
                out[part] = operator_folder_label(pic)
            except ValueError:
                out[part] = UNASSIGNED_OPERATOR
    return out


def plan_moves(root: Path | None = None) -> list[dict[str, Any]]:
    base = Path(root) if root else TEST_DB_ROOT
    pic_map = _pic_label_map()
    moves: list[dict[str, Any]] = []
    if not base.is_dir():
        return moves
    for comp in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
        for part in sorted(p for p in comp.iterdir() if p.is_dir()):
            for pkg in sorted(p for p in part.iterdir() if p.is_dir()):
                for child in sorted(p for p in pkg.iterdir() if p.is_dir()):
                    if not (is_campaign_dir(child) and is_version_name(child.name)):
                        continue
                    op = pic_map.get(part.name.upper(), UNASSIGNED_OPERATOR)
                    dest = pkg / op / child.name
                    moves.append(
                        {
                            "src": str(child),
                            "dest": str(dest),
                            "component": comp.name,
                            "part": part.name,
                            "package": pkg.name,
                            "operator": op,
                            "version": child.name,
                            "exists_dest": dest.exists(),
                        }
                    )
    return moves


def apply_moves(moves: list[dict[str, Any]], *, apply: bool) -> list[dict[str, Any]]:
    done: list[dict[str, Any]] = []
    for m in moves:
        src = Path(m["src"])
        dest = Path(m["dest"])
        row = dict(m)
        if dest.exists():
            row["status"] = "skip_dest_exists"
            done.append(row)
            continue
        if not apply:
            row["status"] = "dry_run"
            done.append(row)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        row["status"] = "moved"
        done.append(row)
    return done


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Migrate Version folders under operator person folders")
    ap.add_argument("--apply", action="store_true", help="Actually move folders (default dry-run)")
    ap.add_argument("--root", default="", help="Override #Test_Database root")
    args = ap.parse_args(argv)
    root = Path(args.root) if args.root else None
    moves = plan_moves(root)
    results = apply_moves(moves, apply=bool(args.apply))
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"{mode}: {len(results)} legacy Version folder(s)")
    for r in results:
        print(f"  [{r['status']}] {r['src']} -> {r['dest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
