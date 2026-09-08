"""Self-check: tags.yaml + TAGS.txt + rolling report.json + archive (A17-T01).

Run: python -m ate.core.check_tags_datalog
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    errors: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="ate_a17_tags_"))
    from ate.core import database as dbmod
    from ate.core import paths as pathmod
    from ate.core.database import begin_session, end_session, record_step, set_context
    from ate.core.datalog import archive_dir, report_path
    from ate.core.tags import import_tags, list_boards, load_tags, save_tags, tags_txt_path

    old_root = pathmod.TEST_DB_ROOT
    old_db_root = dbmod.TEST_DB_ROOT
    pathmod.TEST_DB_ROOT = tmp / "#Test_Database"
    dbmod.TEST_DB_ROOT = pathmod.TEST_DB_ROOT
    try:
        pathmod.TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
        set_context(
            component="OpAmp",
            part="A17Check",
            package="TTSOP8",
            operator="Eugene",
            version="Version_1",
            model="A17CHECK",
            part_key="a17check",
            sample_size=2,
        )
        from ate.core.database import get_context

        ctx = get_context()
        ctx.ensure_tree()

        saved = save_tags(
            ["project:A17-char", "board:G11-REV3"],
            boards=["G11-REV3"],
            ctx=ctx,
        )
        if "project:A17-char" not in saved["tags"]:
            errors.append("save_tags missing project tag")
        txt = tags_txt_path(ctx)
        if not txt.is_file():
            errors.append("TAGS.txt not written")
        else:
            body = txt.read_text(encoding="utf-8")
            if "board:G11-REV3" not in body:
                errors.append("TAGS.txt missing board token")

        loaded = load_tags(ctx)
        if "project:A17-char" not in loaded["tags"]:
            errors.append("load_tags round-trip failed")

        vocab = list_boards(family="opamp", package="TTSOP8", ctx=ctx)
        if not vocab:
            errors.append("list_boards empty for opamp/TTSOP8")

        set_context(
            component="OpAmp",
            part="A17Other",
            package="TTSOP8",
            operator="Eugene",
            version="Version_1",
            model="A17OTHER",
            part_key="a17other",
            sample_size=2,
        )
        other = get_context()
        other.ensure_tree()
        save_tags(["project:imported"], boards=[], ctx=other)
        other_root = other.root()

        set_context(
            component="OpAmp",
            part="A17Check",
            package="TTSOP8",
            operator="Eugene",
            version="Version_1",
            model="A17CHECK",
            part_key="a17check",
            sample_size=2,
        )
        ctx = get_context()
        import_tags(other_root, ctx=ctx, merge=True)
        if "project:imported" not in load_tags(ctx)["tags"]:
            errors.append("import_tags failed")

        begin_session({"unit_index": 1, "dut_indices": [1, 2], "run_label": "a17check"})
        record_step(
            "ort",
            success=True,
            summary="ok",
            fixture_mode="G_NEG100",
            dut=1,
            measurements=[{"id": "demo_v", "unit": "V", "min": -1, "max": 1, "value": 0.1}],
        )
        rp = report_path(ctx)
        if not rp.is_file():
            errors.append("report.json missing after record_step")
        else:
            doc = json.loads(rp.read_text(encoding="utf-8"))
            if doc.get("schema") != "ate.datalog.v1":
                errors.append("report schema wrong")
            if not doc.get("steps"):
                errors.append("report steps empty")
            if not any(
                m.get("id") == "demo_v"
                for s in doc.get("sites") or []
                for m in (s.get("measurements") or [])
            ):
                errors.append("site measurement not folded")

        end_session("completed")
        arch = archive_dir(ctx)
        archives = list(arch.glob("session_*.json")) if arch.is_dir() else []
        if not archives:
            errors.append("archive missing after end_session")
    finally:
        pathmod.TEST_DB_ROOT = old_root
        dbmod.TEST_DB_ROOT = old_db_root
        shutil.rmtree(tmp, ignore_errors=True)

    if errors:
        print("FAIL check_tags_datalog:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_tags_datalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
