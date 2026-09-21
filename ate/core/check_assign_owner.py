"""Self-check: assign_owner_products upserts parts + ensure this operator only.

Run: python -m ate.core.check_assign_owner

Proves: matched SKUs get Version_1 under that person; unmatched reported (no
scrape); Jane sibling does not clobber Ariff; All/Kevin refuse; unassign drops
yaml parts: only (folders stay).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import yaml

import ate.core.database as dbmod
from ate.core.new_product import assign_owner_products, resolve_sku


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ate_assign_owner_"))
    old_owners = dbmod.OWNERS_PATH
    old_cloud = dbmod.CLOUD_PEOPLE_PATH
    try:
        tmp_owners = tmp / "owners.yaml"
        tmp_owners.write_text(
            yaml.safe_dump(
                {
                    "owners": [
                        {
                            "id": "all",
                            "label": "All",
                            "default_family": "opamp",
                            "default_part": "rs622",
                            "default_component": "OpAmp",
                            "default_package": "TTSOP8",
                            "parts": [],
                        },
                        {
                            "id": "ariff",
                            "label": "Ariff",
                            "default_family": "logic",
                            "default_part": "rs1g08",
                            "default_component": "Logic",
                            "default_package": "SC70-5",
                            "parts": ["rs1g08"],
                        },
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        dbmod.OWNERS_PATH = tmp_owners
        dbmod.CLOUD_PEOPLE_PATH = tmp / "_ate" / "people.yaml"

        if resolve_sku("ZZZZ_NOT_A_PART") is not None:
            raise AssertionError("unknown code must not resolve")
        if resolve_sku("RS1G08") is None and resolve_sku("rs1g08") is None:
            raise AssertionError("RS1G08 must resolve from inventory or parts yaml")

        try:
            assign_owner_products(label="All", parts=["RS1G08"], base=tmp)
            raise AssertionError("All must refuse assign")
        except ValueError:
            pass
        try:
            assign_owner_products(label="kevin", parts=["RS1G08"], base=tmp)
            raise AssertionError("kevin must refuse assign")
        except ValueError:
            pass

        ariff = assign_owner_products(
            label="Ariff",
            parts=["RS1G08"],
            replace_parts=True,
            sample_size=2,
            base=tmp,
        )
        ariff_roots = [Path(r) for r in (ariff.get("roots") or [])]
        if not ariff_roots:
            raise AssertionError("Ariff assign must ensure a root")
        ariff_root = ariff_roots[0]
        if "Ariff" not in str(ariff_root):
            raise AssertionError(f"Ariff root must include operator: {ariff_root}")
        marker = ariff_root / "sessions" / "ariff_only.txt"
        marker.write_text("ariff", encoding="utf-8")
        (ariff_root / "workbook" / "keep.xlsx").write_bytes(b"xlsx-marker")

        jane = assign_owner_products(
            label="JaneAssign",
            parts=["RS1G08", "ZZZZ_NOT_A_PART", "rs1g07"],
            replace_parts=True,
            sample_size=2,
            base=tmp,
        )
        unmatched = list(jane.get("unmatched") or [])
        if "ZZZZ_NOT_A_PART" not in unmatched:
            raise AssertionError(f"unmatched must list ZZZZ: {unmatched}")
        if any("zzzz" in str(r).lower() for r in (jane.get("roots") or [])):
            raise AssertionError("unmatched code must not mkdir")
        owner = jane.get("owner") or {}
        parts = [str(p).lower() for p in (owner.get("parts") or [])]
        if "rs1g08" not in parts or "rs1g07" not in parts:
            raise AssertionError(f"Jane parts must include matched keys: {parts}")
        if "zzzz_not_a_part" in parts:
            raise AssertionError("unmatched must not land on parts:")
        jane_roots = [Path(r) for r in (jane.get("roots") or [])]
        if len(jane_roots) < 2:
            raise AssertionError(f"Jane must ensure RS1G08 + RS1G07: {jane_roots}")
        jane_rs1g08 = next((r for r in jane_roots if "RS1G08" in str(r)), None)
        if jane_rs1g08 is None or "JaneAssign" not in str(jane_rs1g08):
            raise AssertionError(f"Jane RS1G08 sibling missing: {jane_roots}")
        if jane_rs1g08 == ariff_root:
            raise AssertionError("Jane must be a sibling folder, not Ariff's path")
        if marker.read_text(encoding="utf-8") != "ariff":
            raise AssertionError("Jane assign must not clobber Ariff sessions")
        if not (ariff_root / "workbook" / "keep.xlsx").is_file():
            raise AssertionError("Jane assign must not clobber Ariff workbook")

        before_dirs = {p for p in jane_rs1g08.rglob("*") if p.is_dir()}
        gone = assign_owner_products(
            label="JaneAssign",
            parts=[],
            unassign=["rs1g08"],
            replace_parts=False,
            base=tmp,
        )
        after_parts = [str(p).lower() for p in ((gone.get("owner") or {}).get("parts") or [])]
        if "rs1g08" in after_parts:
            raise AssertionError("unassign must drop rs1g08 from parts:")
        if not jane_rs1g08.is_dir():
            raise AssertionError("unassign must not delete Version folders")
        if before_dirs and not jane_rs1g08.is_dir():
            raise AssertionError("unassign must keep folder tree")

        print(
            "OK check_assign_owner: matched ensure + unmatched report + "
            "Jane sibling non-clobber + All refuse + unassign yaml-only"
        )
        return 0
    finally:
        dbmod.OWNERS_PATH = old_owners
        dbmod.CLOUD_PEOPLE_PATH = old_cloud
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
