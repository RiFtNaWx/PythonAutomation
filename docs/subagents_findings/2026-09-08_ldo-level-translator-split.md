---
keywords: ldo, level-translator, level-shifter, inventory, run_ic, ariff, rs3213, rs0204, rs0302
main_idea: Tracking sheet classes split — Logic Series vs Level Shifters vs Linear Regulator/LDO. Ariff Downloads result xlsx moved into Logic/ LDO/ LevelTranslator/. RS0204 stays ate_suite=logic for live dual-rail.
---

# 2026-09-08 LDO / Level Translator separation

## Ariff `LabAutomation test`

| Bucket | Contents |
|--------|----------|
| Logic/ | RS1G08, RS1G32, RS1GT08, RS1GT32 results xlsx |
| LDO/ | RS3213_3.3_results.xlsx; code still `LabAutomation_v1 - Copy/LDO_tests.py` |
| LevelTranslator/ | README only -- no RS0204/RS0302 in this drop |

## ATE config

- `run_ic.yaml`: Level Shifters -> `level` (not logic); LDO aliases on `power`
- `inventory.yaml`: RS0204/RS0302 = level; RS3213/RS3235 = power; Logic Series stays logic
- RS0204 `ate_suite: logic` so New product still hits live dual-rail suite

## Check

`python -m ate.core.check_new_product` -> OK
