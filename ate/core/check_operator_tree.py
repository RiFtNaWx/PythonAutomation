"""Self-check: operator folder path + migrate dry/apply in a temp tree.

Run: python -m ate.core.check_operator_tree
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from ate.core.database import (
    UNASSIGNED_OPERATOR,
    DbContext,
    list_tree,
    prefer_live_operator,
    require_write_operator,
    set_context,
)
from ate.core.migrate_operator_folders import _pic_label_map, apply_moves, plan_moves


def main() -> int:
    try:
        require_write_operator("all")
        raise AssertionError("All must raise for writes")
    except ValueError:
        pass
    try:
        require_write_operator("All")
        raise AssertionError("All must raise for writes")
    except ValueError:
        pass
    if require_write_operator("ariff") != "Ariff":
        raise AssertionError("ariff id must map to Ariff label")
    if require_write_operator("Eugene") != "Eugene":
        raise AssertionError("Eugene label must stay Eugene")

    tmp = Path(tempfile.mkdtemp(prefix="ate_op_tree_"))
    try:
        legacy = tmp / "Logic" / "RS1G08" / "SOT23" / "Version_1"
        (legacy / "_manifest").mkdir(parents=True)
        (legacy / "workbook").mkdir(parents=True)
        (legacy / "sessions").mkdir(parents=True)
        moves = plan_moves(tmp)
        if len(moves) != 1:
            raise AssertionError(f"expected 1 legacy move, got {len(moves)}")
        dry = apply_moves(moves, apply=False)
        if dry[0]["status"] != "dry_run":
            raise AssertionError("dry-run must not move")
        if not legacy.is_dir():
            raise AssertionError("dry-run must leave source")
        applied = apply_moves(moves, apply=True)
        if applied[0]["status"] != "moved":
            raise AssertionError("apply must move")
        op_label = _pic_label_map().get("RS1G08", UNASSIGNED_OPERATOR)
        dest = tmp / "Logic" / "RS1G08" / "SOT23" / op_label / "Version_1"
        if not dest.is_dir():
            raise AssertionError(f"expected dest {dest}")
        if legacy.exists():
            raise AssertionError("source must be gone after move")
        tree = list_tree(tmp)
        ops = (
            ((tree.get("components") or {}).get("Logic") or {})
            .get("parts", {})
            .get("RS1G08", {})
            .get("packages", {})
            .get("SOT23", {})
            .get("operators", {})
        )
        if op_label not in ops:
            raise AssertionError(f"list_tree missing {op_label}: {ops}")
        if "Version_1" not in (ops[op_label].get("versions") or []):
            raise AssertionError(f"list_tree missing Version_1 under {op_label}")

        ctx = DbContext(
            component="Logic",
            part="RSDEMO",
            package="SOT23",
            operator="Ariff",
            version="Version_1",
            part_key="rsdemo",
        )
        # Use isolated root via monkeypatch of TEST_DB_ROOT is heavy; assert identity shape.
        ident = ctx.identity()
        if "operator" not in ident or ident["operator"] != "Ariff":
            raise AssertionError("identity must include operator")
        if "/Ariff/Version_1" not in ident["root"].replace("\\", "/"):
            raise AssertionError(f"root must include operator segment: {ident['root']}")

        pkg = tmp / "OpAmp" / "RS622" / "TTSOP8"
        (pkg / UNASSIGNED_OPERATOR / "Version_1" / "_manifest").mkdir(parents=True)
        (pkg / "Eugene" / "Version_1" / "_manifest").mkdir(parents=True)
        picked = prefer_live_operator(pkg, "Version_1", "RS622", UNASSIGNED_OPERATOR)
        if picked != "Eugene":
            raise AssertionError(f"prefer_live_operator must skip _unassigned, got {picked}")

        retired = tmp / "Level" / "_retired_Stub" / "X" / "Eugene" / "Version_1"
        (retired / "_manifest").mkdir(parents=True)
        live = tmp / "Level" / "RS0204" / "TSSOP14" / "ChangThong" / "Version_1"
        (live / "_manifest").mkdir(parents=True)
        tree2 = list_tree(tmp)
        level_parts = ((tree2.get("components") or {}).get("Level") or {}).get("parts") or {}
        if "_retired_Stub" in level_parts:
            raise AssertionError("list_tree must skip _retired parts")
        if "RS0204" not in level_parts:
            raise AssertionError("list_tree must keep Level/RS0204")

        # set_context rejects All when operator forced
        try:
            set_context(operator="all")
            raise AssertionError("set_context(all) must fail")
        except ValueError:
            pass

        from ate.core import database as dbmod

        old_owners = dbmod.OWNERS_PATH
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
                            "id": "eugene",
                            "label": "Eugene",
                            "default_family": "opamp",
                            "default_part": "rs622",
                            "default_component": "OpAmp",
                            "default_package": "TTSOP8",
                            "parts": ["rs622"],
                        },
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        dbmod.OWNERS_PATH = tmp_owners
        try:
            created = dbmod.upsert_owner(
                label="JaneCheck",
                default_family="logic",
                default_part="rs1g08",
                default_component="Logic",
                default_package="SC70-5",
                task="RS1G08",
            )
            if created.get("action") != "created":
                raise AssertionError(f"new person must create, got {created.get('action')}")
            if dbmod.require_write_operator("janecheck") != "JaneCheck":
                raise AssertionError("new person id must map to folder label")
            exists = dbmod.upsert_owner(label="JaneCheck", default_part="rs1g32")
            if exists.get("action") != "exists":
                raise AssertionError("second add without update_defaults must not rewrite")
            updated = dbmod.upsert_owner(
                label="JaneCheck",
                default_part="rs1g32",
                task="RS1G32",
                update_defaults=True,
            )
            if updated.get("action") != "updated":
                raise AssertionError("Save person must update defaults")
            if str((updated.get("owner") or {}).get("task") or "") != "RS1G32":
                raise AssertionError("Save person must record task")
            try:
                dbmod.upsert_owner(label="All")
                raise AssertionError("All must not be upserted")
            except ValueError:
                pass
            gone = dbmod.remove_owner("JaneCheck")
            if not gone.get("removed"):
                raise AssertionError("remove_owner must return removed row")
            ids = {str(r.get("id")) for r in dbmod.load_owners()}
            if "janecheck" in ids:
                raise AssertionError("remove_owner left yaml row")
            if not tmp_owners.is_file():
                raise AssertionError("remove_owner must keep owners.yaml")
        finally:
            dbmod.OWNERS_PATH = old_owners

        print(
            f"OK operator-tree: migrate+list_tree; label={require_write_operator('changthong')}; "
            f"unassigned={UNASSIGNED_OPERATOR}"
        )
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
