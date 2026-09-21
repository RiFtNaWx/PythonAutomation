keywords: sim, ldo, vout, lir, lor, vinmin, ioutmax, dmm-node, leftover-13, leftover-honest, goal-open
main_idea: Path B LDO DMM is on VOUT. SIM now uses set_ldo_dut (not CH3+CH2<1V). LIR_mV=0 not 1600 VIN alias. LOR_mV=1.96 leftover sag. IOUTMAX_V=3.248 dropout, not VIN-stamp. Leftover 13 unchanged. Goal OPEN.

# SIM LDO VOUT node (2026-09-15)

PREFLIGHT: HIT. Reuse `2026-09-15_stamp-off-ldo.md` and `2026-09-15_seelim-nan-ch3.md`. Did not UpdateGoal complete. Did not Discover / Open Session / live START. No PyVISA. No runner.py.

Path B `ldo.py` VINMIN/LIR/LOR/IOUTMAX pause text is DMM on VOUT. SIM `_dmm_volt` used to return PSU CH1 VIN (LIR=1600) or SeeLim Schmitt on CH2 load (LOR=0, IOUTMAX VIN-stamp). USB would not stamp VIN as VOUT.

## What changed

- `ate/instruments/sim.py:89` `set_ldo_dut`. `:344` `_ldo_vout` leftover Vdo=50 mV, CH2 load sag. `:367` `_dmm_volt` gates on `ldo_dut` only.
- Did not restore CH3-on + CH2<1V => VOUT=VIN. That broke RS1G126 OE. Loopback `seelim_oe_high_a0_y_low` stays.
- `ate/tests/power/ldo.py:93` arms SIM for vinmin/lir/lor/ioutmax. Removed IOUTMAX VIN-stamp (`vout_min < 0.05` then `min(vins)`).
- Fail-closed: `check_all_parts` rejects LIR `|dVIN|*1000` / `VIN*1000` and IOUTMAX rows where VOUT follows VIN>=4.5 V. `check_add_test` rejects the old CH3 shortcut and VIN-stamp.

## Stamps after (rs3213 = rs3235)

| id | before | after | note |
|----|--------|-------|------|
| LIR_mV | 1600 | 0.0 | both VIN 3.4/5.0 in regulation; not VIN alias |
| LOR_mV | 0.0 | 1.96 | leftover load sag, not Schmitt 1 mV |
| VINMIN_V | 3.3 | 3.3 | first VIN where VOUT >= 0.98*nom |
| IOUTMAX_V | 3.3 | 3.248 | dropout+load; not VIN-stamp 3.3 |

File: `ate/core/_check_data/sim_stamps.json` (rewritten this pass).

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM n/ok: **218/218**. REALIZED=205 LEFTOVER=13.
Idle-restart worker (busy=False). Ctrl+F5 console if UI was open.

## Leftover 13 (must stay; do not reclassify)

Same 13 as `physics_scale.py` MUST_STAY_LEFTOVER / `2026-09-15_sim-reprove-after-walker.md`.

## Named leftover-honest (not leftover 13)

- LIR_mV=0 -- no datasheet line-reg model. DMM node is VOUT (not VIN). Do not fake PDF LIR.
- LOR_mV leftover sag, not datasheet load-reg.
- Vdo=50 mV leftover, not PDF dropout @ Iout.
- GBW runner `_pause` auto-returns. Do not edit runner.py.
- SR~5.55, GBW 7.006, DELAY two-bin, pulse 0.5/f, TR/TF 5 ns MSO 70 MHz, VOS_mV=0, OVERSHOOT=0.
- `imported_input_off_leakage.py` still scaffold. Not enabled.

## Do not

- Restore CH3+CH2<1V LDO shortcut.
- Fake 110/550 MHz, AOL_dB, SETTLE_us, RS1G14 global invert, DELAY SPICE, GBW datasheet, SR 0.5.
- Reclassify leftover 13. Fill or enable `imported_input_off_leakage`.
- Close goal.

Goal: **OPEN**.
