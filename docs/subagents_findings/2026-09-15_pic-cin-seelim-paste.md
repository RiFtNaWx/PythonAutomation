---
keywords: junior, excel, ariff, cin, cpd, seelim, leakage, stub, leftover-honest
main_idea: Ariff Cin/Cpd paste now probes Average Cin H21 / Average Cpd E8 (case-insensitive sheet names). SeeLim MSOP leakage stubs paste B2 like Iplus. Not junior-100%.
---

# PIC Cin/Cpd + SeeLim leakage paste

PREFLIGHT: PARTIAL. Reuse 2026-09-15_switch-excel-dut-grid.md, 2026-09-15_logic-stub-enabled-sheets.md. Spawn: skip.

Ariff goldens use sheet `Cin`/`Cpd`, not `CIN`. Probe required exact `CIN`, so Fill Excel skipped PIC capacitance. SeeLim MSOP leakage tabs are `(stub)` with no DUT headers; only Iplus had B2.

Now `_sheet_by_fold` + Average-column probe (formula to the right, else first value below). SeeLim `(stub)` sheets get first measurement id at B2.

Live apply: Ariff RS1GT08 CIN_pF H21, CPD_pF E8. RS1GT32 CIN_pF H21, CPD_pF D12 (no Average row; first sample formula). SeeLim RS2323 MSOP IOZ/ION/IIN B2.

## Leftover-honest

- Analog-switch BW/ISO/XTalk. MSO5072 is 70 MHz; do not stamp 110/550 MHz.
- AOL/EMIRR still mapped captures. Noise is 0.1-10 Hz Vpp. Settling is photo.
- RS0204 Icc/VOH condition grids. VIX has no numeric DUT paste.
- Inventory RS2323 PIC package is UQFN; SeeLim golden is MSOP. Lim RS2227 has no xlsx.
- USB START of every SKU is not SIM. Path C `input_off_leakage` unfilled.

## Proof

```
python -m ate.core.check_campaign_outline
```
