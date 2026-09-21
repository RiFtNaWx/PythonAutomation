---
keywords: [a19, a20, a21, voh-load, icc, rs1g32, rs0204, sheet-map-match, tracking-inventory]
main_idea: voh_load now fills sheet VOH (strip _load). DEMO supply_current_sweep stamps ICC_uA. RS1G32/RS1GT08/RS1GT32/RS1GT32D VOH tables in limits. Analog SW rail retries empty tracking list.
---

PREFLIGHT: PARTIAL. Reuse 2026-09-11_a19-a20-a21-handover.md. Spawn: skip.

## A19

`session_values._fold_name` maps `voh_load` -> sheet `VOH` and `supply_current_sweep` -> `Supply_Current`.
Live RS1G08 VOH/VOL/Supply_Current sheets are empty in A1:AN80. RS2323 Iplus is stub `A1` only. Do not invent FILL_ME.
RS622 TTSOP8 DUT grids already fill.

## A20

DEMO `supply_current_sweep` now picks `ICC_uA` (test alias). RS0204 START/DEMO return `VOH_DROP_V` / `VOL_V` / `ICC_uA` / `IL_uA`.
Copied RS1G08-class voh/vol tables onto rs1g32 / rs1gt32 / rs1gt08 / rs1gt32d (same ariff_dc defaults). Not onto open-drain 1G07.
Proof DEMO:

- RS1G32 Ariff SOT23: VOH_* PASS, VOL_* PASS, ICC_uA max 1 value 1 PASS
- RS0204 ChangThong TSSOP14: ICC_uA typ 3.5 PASS, IL_uA max 2 PASS, VOH_DROP_V max 0.4 PASS, VOL_V max 0.4 PASS

## A21

Family rail retries `loadInventory` when tracking rows are empty. Cache `app.js?v=20260911handover3`.

## Not done

R-0003 A07-A12. Logic/LIM numeric DUT cells still missing on disk. PDF 8.4 table extract still thin. Parked A13/A14/stub RUN-IC.
