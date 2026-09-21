---
keywords: golden-refs, rs1gt08, rs1gt32, ariff, product-testing-report, reference, datasheet, reports-zip
main_idea: Lab reports always come from Downloads/Product Testing Report (unzip of Test Reports.zip). Datasheets stay in Downloads/Reference/Reference. RS1GT08/RS1GT32 senior books are now Ariff goldens (VIX/VOX).
---

# Product Testing Report drop + Ariff GT08/GT32

Zip `C:\Users\OoiJianHong\Downloads\Test Reports.zip` is the archive. Live drop is `C:\Users\OoiJianHong\Downloads\Product Testing Report` (`inventory.yaml` `reports_root` / `reports_zip`). Do not keep using `OneDrive_2026-09-03`. Datasheets stay `Downloads\Reference\Reference` (`bench.yaml` `reference_root`).

The zip had no RS1GT08 / RS1GT32 lab books (only RS1GT32D). Those two Downloads xlsx were copied into the drop and into `#Test_Database/Logic/RS1GT08|RS1GT32/SC70-5/Ariff/Version_1/workbook/`. JianHong stubs untouched.

`python -m ate.core.golden_refs` extracts lab xlsx from the zip (skips Files/Raw Data/PNGs), then collects goldens with **report_drop** winning over campaign copies.

Proof:

```
python -m ate.core.check_golden_refs
python -m ate.core.check_lookup
```
