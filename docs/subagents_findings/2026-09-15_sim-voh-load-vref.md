---
keywords: junior, voh_load, sim-dmm, xlat, vref, vccb, leftover-honest
main_idea: Ariff voh_load SIM SPEC FAIL was CH2 load Vref (80-320 mV) treated as translator VCCB. xlat now requires a logic rail (v2 > vcc and v2 >= 1.2). SIM 221/221, no SPEC FAIL. Not junior-100%.
---

# 2026-09-15 SIM VOH load vs translator VCCB

PREFLIGHT: PARTIAL. Reuse: 2026-09-15_rs0204-vih-condition.md. Spawn: skip.

## This sitting

1. `_dmm_volt` unmatched CH2 was any `abs(vcc-v2)>=0.05`. Ariff VOH sets CH2 to Vref 0.08-0.32 V. SIM returned Vref as VOH (SPEC FAIL). USB DMM on Q still reads ~VCC.
2. xlat now: CH2 ON, `v2 > vcc + 0.05`, and `v2 >= 1.2` (logic rail). RS0204 VCCA=1.8 / VCCB=3.3 still follows VCCB. CMOS single-rail unchanged. Matched dual-rail stays OpAmp follower.
3. `stimulus.py` had a duplicate dict after a closed `}` (IndentationError). Removed the orphan copy. First dict already had the sweep hints.
4. Checks: `check_add_test` (xlat tokens), `check_sim_run` (VCC vs Vref vs VCCB), `check_stimulus`, `check_mapped_tests`, `check_specs_datalog`, `check_family_load`, `check_all_parts`.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_stimulus
python -m ate.core.check_all_parts
```

SIM **221/221** parts=25 stub `rs0302`. No `SPEC FAIL` in that run. yaml=26.

## Leftover-honest (goal still open)

- AOL/EMIRR still mapped. Noise = 0.1-10 Hz Vpp not nV/rtHz. ISC missing
- Settling still photo/cursor (do not stamp MSO delay as 0.1% SETTLE_us)
- Analog-switch BW 110 MHz / ISO / XTalk; rON min/max still PDF image
- RS0302 empty (I2C bidirectional switch; RON at 64 mA, DMM 10 mA). Do not copy RS0204
- RS74AUP1G07 no PDF VOH/VOL
- Excel unique VOX Vcc rows; RS0204 Icc/VOH empty/grid. Probe live xlsx, never guess A91
- USB START of every SKU is not SIM
- Path C `input_off_leakage` unfilled and not enabled
- RS2227 no rON (USB DPDT pinout != RS2323)
