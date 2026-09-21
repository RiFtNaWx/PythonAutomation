keywords: sim, stamp-hunt, iq, vout-yaml, vin-node, leftover-13, leftover-honest, goal-open, post-ldo
main_idea: Closable USB-path holes after LDO VOUT. IQ no longer stamps yaml VOUT_V. SIM IQ current follows VIN (CH2), not VOUT-bias ICC. Leftover stays 13. SIM 218/218 REALIZED=205. Goal OPEN.

# Post-LDO stamp hunt (2026-09-15)

PREFLIGHT: HIT. Reuse `2026-09-15_sim-ldo-vout-node.md` and `2026-09-15_physics-formula-stamp-audit.md`. Did not UpdateGoal complete. Did not Discover / Open Session / live START. No PyVISA. No runner.py.

## Verdict

Closed: LDO IQ yaml-VOUT stamp + IQ VIN-sweep flat (VOUT-bias ICC).
Leftover 13: stays 13.
SIM n/ok: **218/218**. REALIZED=205 LEFTOVER=13.
Goal: **OPEN**.

Worker: `session_status` busy=True (live USB RS622 slew/settling). Did not idle-restart.

## Hunt (current tree)

Parsed `ate/core/_check_data/sim_stamps.json` n=218 ok=218 ran=218.

Empty (not closable this pass):

- NaN / non-finite: 0
- Rigol-invalid `|v|>1e10`: 0
- VOH < VOL: 0
- VIH < VIL: 0
- RS1G14 VOH A=VCC: VOH tracks rail with A=0; VOL=0.001 with A=VCC
- LIR_mV VIN*1000 / |dVIN|*1000: LIR=0.0 (leftover-honest regulation)
- IOUTMAX VIN-stamp: 3.248 not 3.3/5.0
- MUST_STAMP gap: 0
- CH3+CH2<1V LDO shortcut: still absent in `_dmm_volt`

## What closed (file:line)

1. IQ yaml VOUT -- `ate/tests/power/ldo.py:150` arms `set_ldo_dut`. `:164` stamps only `IQ_uA` from DMM current. Removed yaml `_vout_nominal` as `VOUT_V` (DMM is DCI).
2. IQ VIN node -- `ate/instruments/sim.py:315-324` `_dmm_current` when `ldo_dut`: VIN=CH2 if CH3 off (IQ), else CH1. Leftover `_icc_a(vin)`, not PDF Iq, not CH1 VOUT-bias ICC.
3. Loopback -- `sim.py:796` `ldo_iq_follows_vin`. `power_off` after `reset_bus` so leftover CH3 EN cannot steal VIN=CH1.
4. Fail-closed -- `check_add_test.py:543-547` IQ arm + no yaml VOUT. `:898-904` current-gate + loopback. `check_all_parts.py:708-721` / `:863-871` reject IQ `VOUT_V` and IQ_uA flat vs VIN.

Stamps after: rs3213/rs3235 `IQ_uA=0.55` (worst VIN=5.0). No IQ `VOUT_V`. LIR_mV=0.0. IOUTMAX_V=3.248.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM n/ok: **218/218**. physics REALIZED=205 LEFTOVER=13.

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

Do not fake these in software:

- LIR_mV=0 -- both VIN in regulation; no datasheet line-reg model.
- LOR_mV leftover sag, Vdo=50 mV leftover, not PDF.
- IQ_uA leftover `_icc_a(VIN)` uA-class, not PDF tens of uA.
- VOL_* floor 0.001 CMOS -- `sim.py` `_dmm_volt` VIN low.
- rs1g126 ICC/II/IOFF/IOZ one-node DMM when CH2+CH3 on.
- SR~5.55, GBW 7.006, DELAY two-bin, pulse 0.5/f, FMAX 20 Mbps, TR/TF 5 ns MSO 70 MHz, VOS_mV=0, OVERSHOOT=0.
- POWERON_ns us-window 40000. rs29511 TEN=100000 ns us-window.
- rs0204 VOH_DROP_V=0 -- no-load VOUT=VCCB.
- `imported_input_off_leakage.py:31` still scaffold. Not enabled.

## Do not

- Reclassify leftover 13 as REALIZED.
- Fake SR 0.5, GBW datasheet, DELAY SPICE, pulse RC, FMAX 50 Mbps, TR 6.6 ns, LIR datasheet, AOL_dB from BUFFER, IQ datasheet.
- Restore CH3+CH2<1V LDO shortcut.
- Fill or enable `imported_input_off_leakage`.
- Edit `runner.py` / goldens rewrite / `input()` / `Lim` / `Ariff` / `Soo`.
- Close goal (live USB DMM unproven; leftover 13 is method ceiling).
- Restart worker while busy=True.

Goal: **OPEN**.
