---
keywords: junior, rs0204, vih, vil, translator, sim-dmm, vccb, leftover-honest
main_idea: RS0204 VIH/VIL now apply 0.65/0.35*VCCA and check B-side Vout. Trip-vs-VIH-min was failing good parts. SIM unmatched dual-rail DMM drives VCCB. SIM 221/221. Not junior-100%.
---

# 2026-09-15 RS0204 VIH condition + translator SIM

PREFLIGHT: PARTIAL. Reuse: 2026-09-15_ort-mso-delay.md. Spawn: skip.

## This sitting

1. `ate/tests/logic/rs0204.py` VIH/VIL apply datasheet *conditions* (0.65/0.35 * VCCA) and require B-side Vout high/low vs VCCB/2. Stamp `VIH_V`/`VIH_RATIO` as the applied condition. Do not judge a ~0.5*VCCA trip against VIH min 0.65.
2. SIM DMM: unmatched CH1/CH2 (level shifter) VOH = VCCB. Matched rails stay OpAmp follower. Single-rail CMOS unchanged.
3. RS0302 stays empty (I2C switch, not RS0204 CMOS translator). Do not copy RS0204 ids.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_specs_datalog
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **221/221**. RS0204 vih/vil/voh no longer SPEC FAIL. Logic `voh_load` SIM still SPEC FAIL (loaded VOH vs CMOS DMM) -- USB is the production number.

## Leftover-honest (goal still open)

- AOL/EMIRR still mapped. Noise = 0.1-10 Hz Vpp not nV/rtHz. ISC missing
- Settling still photo/cursor
- Analog-switch BW/ISO/XTalk; rON min/max PDF image
- RS0302 empty. RS74AUP1G07 no PDF VOH/VOL
- Excel unique VOX Vcc rows; RS0204 Icc/VOH empty/grid
- Logic `voh_load` SIM CMOS vs loaded VOH
- USB START of every SKU
- Path C `input_off_leakage` unfilled
