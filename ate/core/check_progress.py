"""Fail-closed: observer cannot write; board yaml round-trips; dirty merge keeps all.

Run: python -m ate.core.check_progress
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from ate.core import database as dbmod
from ate.core import progress as prog


def main() -> int:
    errors: list[str] = []
    try:
        dbmod.require_write_operator("kevin")
        errors.append("kevin observer must not write")
    except ValueError:
        pass
    try:
        dbmod.require_write_operator("all")
        errors.append("All must not write")
    except ValueError:
        pass
    try:
        dbmod.require_write_operator("ate")
        errors.append("ATE must not write")
    except ValueError:
        pass

    from ate.core.database import canonical_person_label

    for raw, want in (
        ("lim", "SeeLim"),
        ("SeeLim", "SeeLim"),
        ("ariff", "Ariff"),
        ("eugene", "Eugene"),
        ("changthong", "ChangTong"),
        ("changtong", "ChangTong"),
        ("soo", "Soo"),
        ("chuntak", "Chun Tak"),
        ("Chun Tak", "Chun Tak"),
        ("See Lim", "SeeLim"),
    ):
        got = canonical_person_label(raw)
        if got != want:
            errors.append(f"canonical {raw!r} -> {got!r} want {want}")
    merged = dbmod._merge_owner_rows(
        [{"id": "jane", "label": "Jane", "parts": []}],
        [{"id": "jane", "label": "Jane", "parts": ["rs622", "rs1g07", "rs1g08"]}],
    )
    if (merged[0].get("parts") or []) != []:
        errors.append("empty git parts: must not fill from cloud dump")
    try:
        folder = dbmod.operator_folder_label("changthong")
        if folder != "ChangThong":
            errors.append(f"disk folder must stay ChangThong, got {folder!r}")
    except Exception as exc:
        errors.append(f"changthong folder: {exc}")

    from ate.core.new_product import load_inventory

    unique_parts = {
        str(r.get("part") or "").strip().upper()
        for r in load_inventory()
        if str(r.get("part") or "").strip()
    }
    cap = max(8, len(unique_parts) // 2)
    for o in dbmod.load_owners():
        oid = str(o.get("id") or "")
        if oid in ("all", "kevin", "ate") or o.get("alias_of"):
            continue
        n = len([p for p in (o.get("parts") or []) if str(p).strip()])
        if n > cap:
            errors.append(f"{oid} parts dump ({n} > {cap})")

    tmp = Path(tempfile.mkdtemp(prefix="ate_progress_"))
    old_owners = dbmod.OWNERS_PATH
    old_cloud = dbmod.CLOUD_PEOPLE_PATH
    old_board = prog.BOARD_PATH
    old_pres = prog.PRESENCE_DIR
    git_owners = tmp / "owners.yaml"
    cloud = tmp / "_ate" / "people.yaml"
    git_owners.write_text(
        yaml.safe_dump(
            {
                "owners": [
                    {"id": "all", "label": "All"},
                    {
                        "id": "kevin",
                        "label": "Kevin",
                        "role": "observer",
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
    dbmod.OWNERS_PATH = git_owners
    dbmod.CLOUD_PEOPLE_PATH = cloud
    prog.BOARD_PATH = tmp / "_ate" / "board.yaml"
    prog.PRESENCE_DIR = tmp / "_ate" / "presence"
    try:
        created = dbmod.upsert_owner(
            label="BoardCheck",
            default_family="logic",
            default_part="rs1g08",
            default_component="Logic",
            default_package="SC70-5",
        )
        if created.get("action") != "created":
            errors.append(f"cloud person must create, got {created.get('action')}")
        if not cloud.is_file():
            errors.append("upsert must write cloud people.yaml")
        ids = {str(r.get("id")) for r in dbmod.load_owners()}
        if "all" not in ids:
            errors.append("merge must keep All")
        if "boardcheck" not in ids:
            errors.append("merge must include cloud person")
        if dbmod.is_observer_operator("kevin") is not True:
            errors.append("kevin must be observer")
        if dbmod.is_observer_operator("ate") is not True:
            errors.append("ATE must be observer/blocked")
        if dbmod.is_observer_operator("eugene") is True:
            errors.append("eugene must not be observer")
        beat = prog.heartbeat(owner_id="eugene", label="Eugene", campaign="OpAmp/RS622/TTSOP8")
        if beat.get("skipped"):
            errors.append("eugene heartbeat must write")
        pres = prog.list_presence()
        if not any(str(p.get("campaign") or "") == "OpAmp/RS622/TTSOP8" for p in pres):
            errors.append("heartbeat campaign must round-trip for Opened column")
        skip = prog.heartbeat(owner_id="all", label="All")
        if not skip.get("skipped"):
            errors.append("All heartbeat must skip")
        added = prog.board_add(author="Eugene", text="GBW settle question", kind="question")
        if added.get("count") != 1:
            errors.append("board_add count")
        items = prog.board_list()
        if len(items) != 1 or "GBW" not in str(items[0].get("text")):
            errors.append("board yaml round-trip")
        summary = prog.progress_summary(limit=5)
        if "people" not in summary or "board" not in summary:
            errors.append("progress_summary keys")
        if "owned" not in summary or "unowned" not in summary:
            errors.append("progress_summary must list owned/unowned SKUs")

        from ate.core import new_product as npmod
        from ate.core.new_product import claim_sku

        old_inv = npmod.INVENTORY_PATH
        inv = tmp / "inventory.yaml"
        inv.write_text(
            "parts:\n"
            '  - {part: RS1G07, sheet_class: "Logic Series", category: logic, package: SC70-5, model: RS1G07XC5}\n'
            '  - {part: RS622, sheet_class: "Low Noise Op-Amp", category: opamp, package: SOP8, model: RS622XK, pic: eugene}\n',
            encoding="utf-8",
        )
        npmod.INVENTORY_PATH = inv
        db_root = tmp / "db"
        try:
            skus = prog.sku_ownership([])
            free = {(r["part"], r["package"]) for r in skus["unowned"]}
            held = {(r["part"], r["package"]) for r in skus["owned"]}
            if ("RS1G07", "SC70-5") not in free:
                errors.append("empty PIC RS1G07 must be unowned")
            if ("RS622", "SOP8") not in held:
                errors.append("eugene PIC RS622 must be owned")
            picked = claim_sku(
                label="Jane",
                part="RS1G07",
                package="SC70-5",
                create=False,
                base=db_root,
            )
            if not picked.get("pic_claimed") or str(picked.get("pic") or "") != "jane":
                errors.append("pickup must claim empty PIC")
            if "Jane" not in str(picked.get("root") or ""):
                errors.append("pickup must create Jane Version folder")
            after = inv.read_text(encoding="utf-8")
            if "pic: jane" not in after:
                errors.append("inventory must gain jane PIC on RS1G07")
            steal = claim_sku(
                label="Jane",
                part="RS622",
                package="SOP8",
                create=False,
                base=db_root,
            )
            if steal.get("pic_claimed"):
                errors.append("must not steal eugene PIC on RS622")
            if "pic: eugene" not in inv.read_text(encoding="utf-8"):
                errors.append("eugene PIC must stay on RS622")
            try:
                claim_sku(label="All", part="RS1G07", package="SC70-5")
                errors.append("All must not claim")
            except ValueError:
                pass
            made = claim_sku(
                label="Jane",
                part="RS9999",
                package="QFN",
                category="logic",
                create=True,
                base=db_root,
            )
            if not made.get("inventory_created"):
                errors.append("Create must append a tracking SKU")
            if "RS9999" not in inv.read_text(encoding="utf-8"):
                errors.append("new SKU must land in inventory.yaml")
        finally:
            npmod.INVENTORY_PATH = old_inv
    finally:
        dbmod.OWNERS_PATH = old_owners
        dbmod.CLOUD_PEOPLE_PATH = old_cloud
        prog.BOARD_PATH = old_board
        prog.PRESENCE_DIR = old_pres

    if errors:
        print("FAIL check_progress:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_progress: observer blocked, people merge, board round-trip, pickup PIC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
