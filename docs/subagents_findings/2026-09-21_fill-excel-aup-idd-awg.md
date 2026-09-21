---
keywords: fill-excel, onedrive, tempfile, aup-idd, awg-pnp, rs1gt34, leftover-honest
main_idea: Fill Excel on Eugene RS1GT34 returned ok in 0.5s (golden_auto). AUP IDD now 1.8/2.5/3.3 not 5.5. USB Open Session has PSU+AWG+DMM+MSO. OpAmp fill uses local temp xlsx so OneDrive does not hang 60s.
---

# 2026-09-21 Fill Excel + AUP IDD + AWG on bus

PREFLIGHT: HIT. Reuse screenshot-from-mso, usb-icc-start-outputs, rs1g126-ioz-usb-awg.

## Excel paste (existing Fill Excel / fill_workbook)

Cause: `load_workbook` on the OneDrive golden hung 60s (RS622 photos). Logic RS1GT34 uses Path B `excel_lock` golden_auto and filled in 0.5s.

Change: `fill_workbook_from_report` copies the source to a local `ate_xlsx_` temp, fills, pastes photos there, then copies `*_filled.xlsx` back. Does not invent a second Excel writer.

Proof: RPC `fill_workbook` on Eugene RS1GT34 SOT23-5 Version_1 -> status=ok filled=1 plots=6 Icc.csv + golden_auto xlsx. `check_session_values` EXIT 0.

## AUP IDD (config, not a new TestSpec)

`eugene_cap.run_idd` now uses Parameters `vcc_list`, else yaml `vih_vil_vcc_list` when max < 4.5. RS74AUP1G07 SIM IDD n=6 last @ 3.3 V (was 5.5). RS1G07 still keeps 5.5. `check_add_test` EXIT 0.

## AWG

After idle worker restart, Windows PnP Status=OK on DG8Q281600755. Discover + Open Session mapping is PSU+AWG+DMM+MSO. Earlier IOZ FAIL Missing AWG was USB leftover / PnP Unknown, not a missing TestSpec.

## Leftover-honest

- AUP `delta_supply_current` still sweeps 0..5.0 V.
- MUST_STAY 13 + 6 draft supply_current.
- Comparator/Clock `live: false`.
- Live IOZ uA still needs a wired DUT + START Continue (AWG is on the bus now).
- Goal not complete.
