keywords: inverter, y-polarity, rs1g14, schmitt, y_invert, voh, vol, sim, leftover-13, leftover-honest, goal-open
main_idea: Closable USB-path hole. RS1G14 Schmitt inverter now has SIM Y invert (DUT flag only) plus Path B VOH A=0 / VOL A=VCC. Leftover stays 13. SIM 218/218 REALIZED=205. Goal OPEN.

# Inverter Y polarity (2026-09-15)

PREFLIGHT: HIT. Reuse `2026-09-15_physics-formula-stamp-audit.md`. Prior audit parked RS1G14 VOH/VIH/VOL as leftover-honest because Path B drove A=VCC for VOH and SIM DMM was a buffer. That is NOT leftover 13. It is a closable USB-path polarity hole. Did not UpdateGoal complete. Did not globally invert `_dmm_volt`. No live USB 218. No NI-VISA. No runner.py.

## Verdict

Closed: RS1G14 VOH/VOL/VIH polarity (SIM DUT invert + Path B stimulus).
Leftover 13: stays 13.
SIM n/ok: 218/218. REALIZED=205 LEFTOVER=13.
Goal: OPEN.

Checks this pass:

- `python -m ate.core.check_add_test` OK
- `python -m ate.core.check_sim_run` OK (loopback `inverter_a_high_y_not_vcc` Y=0.001; `inverter_a_low_y_vcc` Y=5; buffer still Y=VCC after flag off)
- `python -m ate.core.check_all_parts` OK `SIM 218/218 physics REALIZED=205 LEFTOVER=13`

Idle-restart `restart_ate_worker.bat` after `sim.py` / `ariff_dc.py` (session idle, not mid-run). Worker ping ok.

## What closed (file:line)

Tracking inverters: only RS1G14. No 1G04/1G06/NAND/NOR in `parts/*.yaml`. Do not invent invert on AND/OR/buffer/OE/RS29511/RS1G97.

1. SIM DUT model, not global DMM invert -- `ate/instruments/sim.py:80` `set_y_invert`. `_BUS["y_invert"]` default False (`sim.py:48` / `reset_bus`). CMOS AWG-DC Y in `_dmm_volt` (`sim.py:371-381`): invert only when flag set. AND/buffer stay `return high if vin >= thresh else low`. SeeLim CH2 Schmitt (`sim.py:382-393`) and RS164 clk_data (`sim.py:354-359`) stay non-inverting. xlat skipped when invert so Ariff VOL Vref > VCC does not stamp VCCB as VOL.
2. Path B stimulus -- `ariff_dc.py:77` `_y_invert` reads part yaml `y_invert`. VOH `a_voh = 0.0 if invert else vcc` (`ariff_dc.py:649`). VOL `a_vol = vcc if invert else 0.0` (`ariff_dc.py:715`). VIH/VIL edge search flips for inverter (`ariff_dc.py:561-577`). Flag cleared in `_power_down` (`ariff_dc.py:93`).
3. Yaml -- `ate/config/parts/rs1g14.yaml:16` `y_invert: true`. Other parts must not set it (`check_add_test` scans `parts/*.yaml`).
4. Fail-closed -- loopback `inverter_a_high_y_not_vcc` (`sim.py:684`): A=VCC must not read VCC. `check_all_parts._inverter_polarity_errors` (`check_all_parts.py:268`). `check_sim_run` rs1g14 VOH A=0 Y~VCC / VOL A=VCC Y low.

## rs1g14 stamps (sim_stamps.json)

- VOH_1p65V=1.65 ... VOH_5p0V=5.0 VOH_5p5V=5.5 (near VCC with A=0)
- VOL_* = 0.001 (A=VCC, Y low)
- VIH_5p0V=2.5 VIL_5p0V=2.45 (Y-falling / Y-rising search)

## Leftover 13 (must stay; do not reclassify)

`MUST_STAY_LEFTOVER` is `physics_scale.py:112-126` / `:149-150`.

1. lm358 settling -- `ate/tests/opa/settling.py:73` CHAN2 VPP; `:128-137` SETTLE_VPP_V. Not 0.1% SETTLE_us.
2. rs358 settling -- same body.
3. rs622 settling -- same body.
4. rs0302 i2c_ron -- `ate/tests/logic/rs0302.py:119` / `:127` 10 mA. Datasheet 64 mA leftover.
5. rs2227 usb_ron -- `ate/tests/lim/rs2227.py:5` PDF image rON; `:109-111` 10 mA force.
6. rs2227 usb_iso -- `ate/tests/lim/rs2227.py:186-208` 1 MHz high-Z. Not 550 MHz 50 ohm.
7. rs2227 usb_xtalk -- same helper / same BW leftover.
8. rs2323 ron -- `ate/tests/lim/rs2323.py:409-414` 10 mA; PDF rON leftover.
9. rs2323 iso -- `ate/tests/lim/iso.py:1-5` / `:21-29`. 1 MHz high-Z, not 110 MHz RF.
10. rs2323 xtalk -- `ate/tests/lim/xtalk.py:1-5` same 1 MHz / 70 MHz leftover.
11. rs358 noise -- `ate/tests/opa/noise.py:1-4` 0.1-10 Hz Vpp, not nV/rtHz.
12. rs622 noise -- same body.
13. rs8551 noise -- same body.

## Named leftover-honest (not leftover 13)

- RS1G97 configurable gate -- no `y_invert`. SeeLim `input_threshold` uses CH2 Schmitt (`sim.py:382-393`), not Path B VOH. VOH/VOL not enabled.
- LIR/LOR VIN-as-VOUT -- `ldo.py` / `_dmm_volt` follows VIN. Not a DMM invert.
- SR~5.55, GBW 7.006, DELAY two-bin, pulse 0.5/f, TR/TF 5 ns MSO 70 MHz, VOS_mV=0, OVERSHOOT=0 -- same as prior audits.
- `imported_input_off_leakage.py:31` still `imported scaffold -- fill body`. Not enabled.

## Do not

- Reclassify leftover 13 as REALIZED.
- Globally invert `_dmm_volt` (AND/buffer/OE/RS164/xlat).
- Fill or enable `imported_input_off_leakage`.
- Edit `runner.py` / goldens rewrite / `input()` / `Lim` / `Ariff` / `Soo`.
- Close goal (live USB DMM on RS1G14 Y unproven; leftover 13 is method ceiling).
