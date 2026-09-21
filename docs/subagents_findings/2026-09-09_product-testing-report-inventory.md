---
keywords: product-testing-report, qualification-list, inventory, lm358, rs2227, rs29511, rs1gt32d, onedrive
main_idea: Inventory now includes Qualification Product List-20260320.xlsx SKUs plus Product Testing Report 2026-09-03 folders (LM358, RS2227, RS29511, RS1GT32D) with report paths. RS0204 stays level + ate_suite logic.
---

# 2026-09-09 Product Testing Report inventory

## Sources

- `Qualification Product List-20260320.xlsx` Main sheet (already SKU-unique)
- `C:\Users\OoiJianHong\Downloads\OneDrive_2026-09-03\Product Testing Report`

## Folders wired via `report:`

Logic Series: RS1G07/08/14/32/97/125/126. Level: RS0204. Analog SW: RS2323. OpAmp: RS622.

## Added (on disk, not on Qualification Main)

| Part | Class | PIC | Report |
|------|-------|-----|--------|
| LM358 | opamp | eugene | Training_LM358测试报告.xlsx |
| RS2227 | analog_switch | lim | RS2227A Test Report.xlsx |
| RS29511 | logic | soo | RS29511 Test Report.xlsx |
| RS1GT32D | logic | ariff | 高低温测试-20251222.xlsx (not RS1GT32XC5) |

Wong Chun Wei RS1G08 template stays a remark on RS1G08 (not an owners.yaml person). Do not invent PIC.

## Check

`python -m ate.core.check_new_product`
