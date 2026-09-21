# Datasheet ingest (later AI: follow this, do not invent a second stack)

Live product is `ate/` + worker **8766** + UI **5174**. Recipe command:

```
python -m ate.core.ingest_datasheet RS1G08 --pdf "<file.pdf>" --xlsx "<file.xlsx>" --no-web
```

Audit all SKUs vs lab sheets:

```
python -m ate.core.ingest_datasheet --audit
```

Proof: `python -m ate.core.check_ingest_datasheet` then `python -m ate.core.check_report_coverage`.

## Path rule (zip pack + every PC)

Prefix may be any OneDrive / SharePoint sync folder. Slice at `#Test_Database`.

- Live Excel: `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/workbook/`
- Golden lab xlsx: `%USERPROFILE%/Downloads/Product Testing Report` else `#Test_Database/_ate/goldens`
- Inventory `report:` is a relative key (`RS622/RS622XK_Lab_Report.xlsx`), never `C:\Users\<name>`
- PDFs: `%USERPROFILE%/Downloads/Reference/Reference` else `#Test_Database/Reference`
- `cloud_db.txt` is per-PC (gitignored). START.bat discovers the shortcut.
- Do not dump PDFs into `#Test_Database`. Do not guess A91. Do not store absolute user paths in zip config.

Helpers: `ate.core.paths.PATH_RULE`, `store_portable`, `resolve_portable`, `slice_test_db_root`.

## Canonical files (edit these, not the JSON copy)

| What | File | Format |
|------|------|--------|
| Specs min/typ/max | `ate/config/limits/<key>.yaml` `specs[].id` | YAML SoT |
| Truth table + VOH/VOL tables | `ate/config/parts/<key>.yaml` (`product_model.truth_table` when present) | YAML SoT |
| PDF text blob | `ate/config/datasheets/text/<key>.txt` | text |
| AI export index | `ate/config/datasheets/tables/<key>.json` | JSON copy |
| Coverage audit | `ate/config/datasheets/coverage.json` | relative `xlsx` + `path_rule` |
| PDF index | `ate/config/datasheets.yaml` | `%USERPROFILE%` + filename |

Do not use XML. JSON is the table export. Markdown sweep sidecar is `sessions/sweep_summary.md` (campaign, not git).

## OCR route (stop at first rung)

1. Local PDF text (`lookup._pdf_plain`). Fat text = no OCR.
2. Cloud HTML for **this SKU only** if text is thin.
3. PaddleOCR then EasyOCR only if still thin.
4. Qianfan / Unlimited-OCR stay parked.

Then merge limits yaml (do not overwrite filled min/max). Probe live xlsx cells. Fill `*_filled.xlsx` (source untouched).

Confirm gate: guessed OCR numbers / Excel cells need `Is it like this?` before write.
