---
keywords: junior, production, scale, sim, ovp, 5.5, scaffold, leftover-honest, vih_vil, rs1gt34, rs1g14, check_all_parts
main_idea: Not 100 percent junior-ready across every SKU. Enabled TestSpecs SIM 199/199 after capping VIH/VIL OVP at 6.0 V and dropping the RS1G14 Path C scaffold. Analog-switch RON, DFF/shift, RS0302, mapped OpAmp PSRR, Excel leftover cells stay honesty gaps.
---

# 2026-09-14 Junior production scale audit

PREFLIGHT: PARTIAL. Reuse: all-parts-sim, ariff-dc-logic-scale, leftover-honest R-0003, sweep-settle, report-ocr-coverage. Spawn: skip.

## Verdict

Do not tell a junior every product / every lab-book sheet / every datasheet corner is done.

Inventory 37 rows / 26 unique parts all have `parts/*.yaml`. Stub `rs0302` has zero tests. Enabled non-scaffold bodies SIM-run **199/199** (`python -m ate.core.check_all_parts`).

## Fixed this sitting (execution blockers)

1. `rs1g14` enabled Path C `input_off_leakage` (empty fill-body). Dropped. `ioff_leakage` stays. Check fails if any SKU enables a scaffold.
2. RS1GT34 `vih_vil` at 5.5 V set OVP `5.5*1.1=6.05` > DUT ceiling 6.0 V -- START died. Cap at `OVP_ABS_MAX_V` in `ariff_dc._power_cycle`.
3. `sim_run_all_enabled` wired back into `check_all_parts` main.

## Executable today (USB START, person not All, Open Session)

- Logic G/GT DC: `vih_vil` / `voh_load` / `vol_load` (no VOH on open-drain 1G07) + Eugene `cin`/`cpd`/`supply_current` where enabled. Sweep settle 5 s on CIN/CPD/IDD. VOH tables are datasheet corners. VIH/VIL lists are short (not 0.1 V grid).
- RS0204 dual-rail timing + DC ids (Excel Icc/VOH cells still unmapped).
- RS2323/RS2227 leakage/I+ only (no RON/IOZ TestSpec).
- LDO RS3213/RS3235 IQ family.
- OpAmp RS622 slew/GBW/settling/ORT real; PSRR/CMRR/AOL/EMIRR still mapped captures.

## Leftover-honest (do not fake-close)

- RS164 / RS1G74 / RS1G123: only `tp` + `supply_current` (not shift/DFF/mono recipes).
- RS0302: empty suite.
- RS74AUP1G07: no PDF VOH/VOL.
- Analog switch RON table is a PDF image.
- Logic Excel unique VOX Vcc rows only; yaml 2.0/3.3/5.0/5.5 have no VOX row.
- SIM DEMO can SPEC FAIL (fake DMM vs datasheet) even when `run()` succeeds.
- USB live of every SKU is not the SIM check.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_all_parts
```

Does not prove: live USB numbers, RON extract, guessed Excel cells.
