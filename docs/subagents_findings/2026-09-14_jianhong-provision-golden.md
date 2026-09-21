<!-- keywords: jianhong, provision-operator, golden-workbook, inventory, clean-xlsx, provision-log, check-provision -->
<!-- main_idea: Replicable `python -m ate.core.provision_operator JianHong` assigns all inventory part+package SKUs, ensures Version_1 under that person, writes empty pretty lab xlsx (Summary/test sheets/Sweep/Checklist, no measured values), and logs a sorted AutoFilter Excel under `#Test_Database/_ate`. -->

# JianHong provision + clean golden workbooks (2026-09-14)

## What shipped

| Piece | Path |
|-------|------|
| Provision CLI | `ate/core/provision_operator.py` |
| Fail-closed check | `ate/core/check_provision_operator.py` |
| Live log | `#Test_Database/_ate/provision_JianHong_latest.xlsx` (+ `.json`) |

## Commands

```
python -m ate.core.check_provision_operator
python -m ate.core.provision_operator JianHong
python -m ate.core.provision_operator JianHong --force-workbook
python -m ate.core.provision_operator JianHong --dry-run
```

## Live proof (this machine)

- 29 unique inventory SKUs, 29/29 ok
- owners.yaml `JianHong` with 26 part keys (packages collapse to one key)
- Sample: `Logic/RS1G08/SC70-5/JianHong/Version_1/workbook/RS1G08_Lab_Report.xlsx`
- Sheets include Summary + family test sheets + Sweep + Checklist
- DUT value cells empty; Sweep header ready for Fill Excel sort (VCC/freq/AWG in `session_values._write_sweep_sheet`)

## Invariants

- No scrape; inventory.yaml only
- Never copies Ariff/ChangThong workbook/sessions
- Re-run without `--force-workbook` keeps existing xlsx (`action=exists`)
- All/Kevin refuse via `require_write_operator`
