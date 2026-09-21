"""Self-check: provision_operator creates Version_1 + clean golden xlsx.

Run: python -m ate.core.check_provision_operator

Proves: unique inventory SKUs get JianHong-style trees under a temp base;
workbook has Summary + Sweep + DUT headers and no fake measured values;
All refuses; re-run is idempotent (workbook action=exists).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import yaml
from openpyxl import load_workbook

import ate.core.database as dbmod
from ate.core.provision_operator import (
    create_clean_golden_workbook,
    provision_operator,
    unique_inventory_skus,
)


def main() -> int:
    skus = unique_inventory_skus()
    if len(skus) < 1:
        raise AssertionError("inventory must yield at least one SKU")
    keys = {(s["part"], s["package"]) for s in skus}
    if len(keys) != len(skus):
        raise AssertionError("unique_inventory_skus must dedupe part+package")

    tmp = Path(tempfile.mkdtemp(prefix="ate_provision_"))
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
                            "parts": [],
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        dbmod.OWNERS_PATH = tmp_owners
        dbmod.CLOUD_PEOPLE_PATH = tmp / "_ate" / "people.yaml"

        try:
            provision_operator("All", base=tmp / "db")
            raise AssertionError("All must refuse provision")
        except ValueError:
            pass

        sample = skus[0]
        from ate.core.new_product import campaign_root, category_by_id, ensure_product

        ensure_product(
            category_id=str(sample["category"]),
            part=str(sample["part"]),
            package=str(sample["package"]),
            model=str(sample.get("model") or ""),
            sample_size=2,
            operator="JianHong",
            open_folder=False,
            apply=False,
            base=tmp / "db",
        )
        cat = category_by_id(str(sample["category"]))
        root = campaign_root(
            str(cat["component"]),
            str(sample["part"]),
            str(sample["package"]),
            "Version_1",
            operator="JianHong",
            base=tmp / "db",
        )
        if not root.is_dir():
            raise AssertionError(f"missing root {root}")

        wb1 = create_clean_golden_workbook(
            root,
            part=str(sample["part"]),
            package=str(sample["package"]),
            operator="JianHong",
            sample_size=2,
            force=False,
        )
        if wb1.get("action") != "created":
            raise AssertionError(f"expected created, got {wb1}")
        path = Path(str(wb1["path"]))
        if not path.is_file():
            raise AssertionError("xlsx missing")
        book = load_workbook(path, read_only=True, data_only=True)
        names = set(book.sheetnames)
        book.close()
        for need in ("Summary", "Sweep", "Checklist"):
            if need not in names:
                raise AssertionError(f"missing sheet {need} in {names}")

        # No measured values in DUT cells (row 2+ of test sheets stay empty aside note)
        book2 = load_workbook(path, data_only=True)
        for sheet in book2.sheetnames:
            if sheet in ("Summary", "Sweep", "Checklist"):
                continue
            ws = book2[sheet]
            for col in range(6, 10):  # DUT columns start after Param/Unit/Min/Max/Typ
                val = ws.cell(3, col).value
                if val not in (None, ""):
                    raise AssertionError(f"DUT cell should be empty: {sheet} {val!r}")
        book2.close()

        wb2 = create_clean_golden_workbook(
            root,
            part=str(sample["part"]),
            package=str(sample["package"]),
            operator="JianHong",
            sample_size=2,
            force=False,
        )
        if wb2.get("action") != "exists":
            raise AssertionError(f"re-run must keep existing workbook, got {wb2}")

        from ate.core import golden_refs as gr
        from ate.core import provision_operator as po
        from openpyxl import Workbook as XlWorkbook

        keep_root = tmp / "db_keep" / "Logic" / "RS1G08" / "SC70-5" / "JianHong" / "Version_1"
        keep_xlsx = keep_root / "workbook" / "RS1G08_Lab_Report.xlsx"
        keep_xlsx.parent.mkdir(parents=True, exist_ok=True)
        keep_wb = XlWorkbook()
        keep_sum = keep_wb.active
        keep_sum.title = "Summary"
        keep_sum["A1"] = "Device"
        keep_sum["B8"] = "Clean golden template -- no measured values. Fill via START / Fill Excel."
        keep_param = keep_wb.create_sheet("IDD")
        keep_param["A1"] = "Parameter"
        keep_param["F1"] = "DUT_1"
        keep_wb.save(keep_xlsx)
        keep_wb.close()
        fake_ref = tmp / "fake_golden.xlsx"
        fake_wb = XlWorkbook()
        fake_ws = fake_wb.active
        fake_ws.title = "KEEPTEST"
        fake_wb.save(fake_ref)
        fake_wb.close()
        old_live = po._under_live_db
        old_resolve = gr.resolve_golden
        po._under_live_db = lambda _root: True
        gr.resolve_golden = lambda _part, _package: fake_ref
        try:
            kept = create_clean_golden_workbook(
                keep_root,
                part="RS1G08",
                package="SC70-5",
                operator="JianHong",
                sample_size=2,
                force=False,
            )
        finally:
            po._under_live_db = old_live
            gr.resolve_golden = old_resolve
        if kept.get("action") == "copied_ref":
            raise AssertionError("existing stub must not be replaced by a golden ref")
        kept_book = load_workbook(keep_xlsx, read_only=True)
        kept_names = set(kept_book.sheetnames)
        kept_book.close()
        if "KEEPTEST" in kept_names:
            raise AssertionError("golden ref sheet leaked onto existing stub")
        if "IDD" not in kept_names:
            raise AssertionError("existing stub IDD sheet was dropped")

        alt_root = tmp / "db_alt" / "Logic" / "RS1G08" / "SC70-5" / "JianHong" / "Version_1"
        alt_xlsx = alt_root / "workbook" / "RS1G08_Lab_Report_SC70-5.xlsx"
        alt_xlsx.parent.mkdir(parents=True, exist_ok=True)
        alt_wb = XlWorkbook()
        alt_sum = alt_wb.active
        alt_sum.title = "Summary"
        alt_sum["B8"] = "Clean golden template -- no measured values. Fill via START / Fill Excel."
        alt_param = alt_wb.create_sheet("IDD")
        alt_param["A1"] = "Parameter"
        alt_wb.save(alt_xlsx)
        alt_wb.close()
        po._under_live_db = lambda _root: True
        gr.resolve_golden = lambda _part, _package: fake_ref
        try:
            alt_res = create_clean_golden_workbook(
                alt_root,
                part="RS1G08",
                package="SC70-5",
                operator="JianHong",
                sample_size=2,
                force=False,
            )
        finally:
            po._under_live_db = old_live
            gr.resolve_golden = old_resolve
        default_xlsx = alt_root / "workbook" / "RS1G08_Lab_Report.xlsx"
        if default_xlsx.is_file():
            raise AssertionError("must reuse package-named xlsx, not create Lab_Report.xlsx")
        if Path(str(alt_res.get("path") or "")).resolve() != alt_xlsx.resolve():
            raise AssertionError(f"dest must be package-named stub, got {alt_res}")
        if alt_res.get("action") == "copied_ref":
            raise AssertionError("package-named stub must not be replaced by a golden ref")
        sm_path = alt_root / "_manifest" / "sheet_map.yaml"
        if sm_path.is_file():
            sm = yaml.safe_load(sm_path.read_text(encoding="utf-8")) or {}
            got_wb = ((sm.get("workbook") or {}) if isinstance(sm, dict) else {}).get(
                "path"
            )
            if got_wb != "../workbook/RS1G08_Lab_Report_SC70-5.xlsx":
                raise AssertionError(
                    f"sheet_map path must match package-named xlsx, got {got_wb}"
                )

        try:
            provision_operator("JianHong", base=tmp / "db_refuse")
            raise AssertionError("must refuse all-SKU dump without all_skus")
        except ValueError:
            pass

        # Full provision into temp base (all inventory SKUs)
        res = provision_operator(
            "JianHong",
            with_workbook=True,
            dry_run=False,
            base=tmp / "db2",
            sample_size=2,
            all_skus=True,
        )
        if res.get("fail_count", 1) != 0:
            raise AssertionError(f"provision failures: {res}")
        if res.get("ok_count", 0) < 1:
            raise AssertionError("expected at least one ok SKU")
        # Sample one workbook under db2
        hit = next(r for r in res["rows"] if r.get("ok") and r.get("workbook"))
        p = Path(str(hit["workbook"]))
        if not p.is_file():
            raise AssertionError(f"provision workbook missing: {p}")

        sliced = provision_operator(
            "JianHong",
            with_workbook=True,
            dry_run=False,
            base=tmp / "db3",
            sample_size=2,
            only_parts=[str(sample["part_key"] or sample["part"])],
        )
        if sliced.get("fail_count", 1) != 0 or sliced.get("ok_count", 0) < 1:
            raise AssertionError(f"only_parts failed: {sliced}")
        pk = str(sample.get("part_key") or sample["part"]).lower()
        for row in sliced["rows"]:
            got = str(row.get("part_key") or row.get("part") or "").lower()
            if got != pk and str(row.get("part") or "").lower() != str(sample["part"]).lower():
                raise AssertionError(f"only_parts leaked {got}")

        pkg_slice = provision_operator(
            "JianHong",
            with_workbook=True,
            dry_run=False,
            base=tmp / "db4",
            sample_size=2,
            only_skus=[{"part": sample["part"], "package": sample["package"]}],
        )
        if pkg_slice.get("fail_count", 1) != 0 or pkg_slice.get("ok_count") != 1:
            raise AssertionError(f"only_skus failed: {pkg_slice}")
        if str(pkg_slice["rows"][0].get("package") or "") != str(sample["package"]):
            raise AssertionError("only_skus must keep the ticked package")

        i2c = provision_operator(
            "JianHong",
            with_workbook=True,
            dry_run=False,
            base=tmp / "db_i2c",
            sample_size=2,
            only_parts=["rs0302"],
        )
        if i2c.get("fail_count", 1) != 0 or i2c.get("ok_count", 0) < 1:
            raise AssertionError(f"rs0302 provision failed: {i2c}")
        i2c_wb = Path(str(next(r["workbook"] for r in i2c["rows"] if r.get("workbook"))))
        i2c_book = load_workbook(i2c_wb, read_only=True)
        i2c_names = set(i2c_book.sheetnames)
        i2c_book.close()
        for need in ("II", "RON", "Cioff"):
            if need not in i2c_names:
                raise AssertionError(f"rs0302 stub missing {need} in {i2c_names}")

        logic = provision_operator(
            "JianHong",
            with_workbook=True,
            dry_run=False,
            base=tmp / "db_logic",
            sample_size=2,
            only_parts=["rs1g123"],
        )
        if logic.get("fail_count", 1) != 0 or logic.get("ok_count", 0) < 1:
            raise AssertionError(f"rs1g123 provision failed: {logic}")
        logic_wb = Path(str(next(r["workbook"] for r in logic["rows"] if r.get("workbook"))))
        logic_book = load_workbook(logic_wb, read_only=True)
        logic_names = set(logic_book.sheetnames)
        logic_book.close()
        for need in ("CIN", "CPD", "IoffLeakage", "TW"):
            if need not in logic_names:
                raise AssertionError(f"rs1g123 stub missing {need} in {logic_names}")

        print(
            f"OK check_provision_operator skus={len(skus)} "
            f"provisioned={res['ok_count']} slice={sliced['ok_count']} sample={sample['part']}"
        )
        return 0
    finally:
        dbmod.OWNERS_PATH = old_owners
        dbmod.CLOUD_PEOPLE_PATH = old_cloud
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL check_provision_operator: {exc}", file=sys.stderr)
        raise SystemExit(1)
