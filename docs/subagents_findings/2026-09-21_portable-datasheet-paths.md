keywords: portable-paths, coverage.json, #Test_Database, zip-pack, ingest, tables-json, PATH_RULE, leftover-honest
main_idea: coverage.json and datasheets.yaml must store relative / %USERPROFILE% / #Test_Database keys, never C:\\Users\\<name>. Resolve any OneDrive prefix by slicing at #Test_Database. Specs and truth tables stay YAML SoT; JSON is the export index.

## Resolver

`ate.core.paths.PATH_RULE` + `store_portable` / `resolve_portable` / `slice_test_db_root`.
Live Excel stays `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/workbook/`.
Golden xlsx: `%USERPROFILE%/Downloads/Product Testing Report` else `#Test_Database/_ate/goldens`.
PDFs: `%USERPROFILE%/Downloads/Reference/Reference` else `#Test_Database/Reference`.

## Export for later AI

Recipe: `docs/datasheet/INGEST.md`.
Specs SoT: `ate/config/limits/<key>.yaml`.
Truth table SoT: `ate/config/parts/<key>.yaml`.
Copy: `ate/config/datasheets/tables/<key>.json` (JSON, not XML).
Audit: `coverage.json` includes `path_rule` and relative `xlsx`.

## Zip

`pack_ate_console.py` skips `last_ingest.json` and `cloud_db.txt`, ships portable `bench.yaml` + `INGEST.md`, fails if packed config still has `OoiJianHong`.

Proof: `python -m ate.core.check_cloud_db` ; `python -m ate.core.check_report_coverage` ; `python -m ate.core.check_ingest_datasheet` ; `python pack_ate_console.py --check`
