---
keywords: junior, excel, rs2227, rs2323, seelim, workbook, stub, package, leftover-honest
main_idea: Recreated missing RS2227 xlsx. SeeLim RS2323 MSOP keeps the package-named stub and gained Ron/Vth/TON Parameter tabs. UQFN does not get the MSOP golden. Not junior-100%.
---

# Analog-switch PIC workbooks

PREFLIGHT: PARTIAL. Reuse 2026-09-15_pic-cin-seelim-paste.md, 2026-09-15_stub-enabled-sheets.md. Spawn: skip.

`create_clean_golden_workbook` looked only for `{part}_Lab_Report.xlsx`, so SeeLim `RS2323_Lab_Report_MSOP.xlsx` was skipped and a second book was copied from the MSOP golden. `resolve_golden(part, UQFN)` fell back to the MSOP package.

Now dest glob reuses `{part}_Lab_Report*.xlsx` (not `_filled`). Cross-package golden fallback is gone. `(stub)` A1 plus Parameter tabs still counts as a stub so collect will not promote it. `apply_campaign_map` writes `workbook.path` to the live dest name.

Live:

- JianHong + SeeLim RS2227 MSOP Parameter stubs with usb_ron / usb_ton_toff F2:I2.
- SeeLim RS2323 MSOP: LeakageOff B2 kept; Ron/Vth/TON/CinConCoff/TBBM added; map points at `_MSOP.xlsx`.
- SeeLim RS2323 UQFN: new Parameter stub (no MSOP golden photos).

## Leftover-honest

- Analog-switch BW/ISO/XTalk. MSO5072 is 70 MHz.
- AOL/EMIRR mapped. Settling is photo. Noise is 0.1-10 Hz Vpp.
- UQFN SeeLim book is a stub, not a UQFN-probed senior layout.
- USB START of every SKU is not SIM. Path C `input_off_leakage` unfilled.

## Proof

```
python -m ate.core.check_golden_refs
python -m ate.core.check_campaign_outline
python -m ate.core.check_provision_operator
```
