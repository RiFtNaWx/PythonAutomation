---
keywords: golden-refs, per-part, workbook, vix, vox, stub, ariff, provision, sheet-map
main_idea: One Parameter/DUT table is the wrong golden. Collect senior lab books into #Test_Database/_ate/goldens and copy that ref per SKU. Probe cells from that xlsx.
---

# Per-part golden workbooks (not one autofill format)

Every test sheet and every part is a different lab book. Ariff RS1G08 SOT23 (`#Test_Database/Logic/RS1G08/SOT23/Ariff/Version_1/workbook/RS1G08_Lab_Report.xlsx`) is VIX/VOX/"Test Parameter". JianHong provision stubs are 28 KB Parameter/DUT grids. Those stubs are not the golden.

## What to use

| Path | Role |
|------|------|
| `python -m ate.core.golden_refs` | Scan campaign `workbook/*.xlsx` + inventory Product Testing Report. Skip stubs, `_filled`, datalogs. Copy winners to `#Test_Database/_ate/goldens/{Component}/{Part}/{Package}/golden.xlsx`. Write `index.yaml`. |
| `create_clean_golden_workbook` | Live tree: copy `resolve_golden` then probe `sheet_map.yaml`. Never replace a senior book. Replace a Parameter stub. Temp check tree: still invents the stub. |
| Fill Excel | Still `*_filled.xlsx`. Source golden stays the template. |

Do not copy `sessions/`. Do not run OpAmp `apply_golden_workbook` on Logic VIX/VOX.

## Proof

```
python -m ate.core.check_golden_refs
python -m ate.core.check_provision_operator
```

`check_golden_refs` fails if a Parameter stub wins over a VIX/VOX book, or if live RS1G08 has no senior VIX/VOX Lab_Report.

## Not this job

- Do not overwrite Ariff / ChangThong workbooks.
- Replacing JianHong stubs happens on the next live `provision_operator` after collect (stub dest + golden ref).
- Leftover SR/PSRR sheets inside Logic books stay leftover, not TestSpecs.
