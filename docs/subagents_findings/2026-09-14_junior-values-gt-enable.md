---
keywords: junior, tpd, io z, ioz, ion, iin, cin, cpd, gt08, gt32, tdis, vih_vil, sweep, wrap-measurements
main_idea: Junior START now stamps TP delays and analog-switch IOZ/ION/IIN. GT08/GT32 enable cin/cpd (and GT32 tp). AND/OR drop OE-only tdis. G/GT VIH lists include 5.5 V. RON/DFF/RS0302/Excel leftover stay.
---

# 2026-09-14 Junior values + GT enable

PREFLIGHT: PARTIAL. Reuse: junior-production-scale, ariff-dc-logic-scale, report-ocr-coverage. Spawn: skip.

## Closed this sitting

1. Logic wraps stamp `TPD_PHL_ns` / `TPD_PLH_ns` / TIDLE / TDIS / TEN / `ICC_uA` from legacy dicts (`ate/tests/logic/wraps.py`).
2. RS2323/RS2227 leakage stamp `IOZ_uA` / `ION_uA` / `IIN_uA` (was nested data only).
3. RS1GT08 / RS1GT32 enable existing `cin`/`cpd` (GT32 also `tp`/`ioff_leakage`).
4. RS1G08 / RS1GT08 drop `tdis` (no OE pin). Keep `tidle` as slow tPD.
5. G-family `vih_vil_vcc_list` includes 1.65 and 5.5. GT adds 5.5 (OVP already capped at 6.0 V).

Proof: `python -m ate.core.check_add_test` ; `check_specs_datalog` ; `check_family_load` ; `check_all_parts` SIM exit 0.

## Still leftover-honest

- Analog-switch RON/Ton/Toff/Con/Coff -- Lim golden has current tests only. Do not invent a rON min/max table.
- RS164 / RS1G74 / RS1G123 / RS0302 -- no shift/DFF/mono/level recipe.
- OpAmp PSRR/CMRR/AOL mapped captures. Excel VOX corners / RS0204 Icc grid unprobed (Product Testing Report drop missing on this PC).
- USB live numbers are not SIM.

Idle-restart worker if console is open (`ate/tests/logic/wraps.py` + `ate/tests/lim/rs2323.py`).
