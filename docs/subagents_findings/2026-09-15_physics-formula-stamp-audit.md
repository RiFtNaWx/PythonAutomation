keywords: physics, formula, stamp, polarity, sweep, leftover-13, leftover-honest, goal-open, sim-stamps, rs1g14
main_idea: Tree-authority physics hunt found no closable wrong stamp (no VOH<VOL, no NaN, no Q stuck, no MUST_STAMP gap). Leftover stays 13. SIM 218/218 REALIZED=205. Goal OPEN.

# Physics formula/stamp audit (2026-09-15)

PREFLIGHT: HIT. Reuse `2026-09-15_independent-sim-dummy-audit.md` and `2026-09-15_physics-scale-proof.md`. This pass is the other hunt: physically wrong stamps / formulas / polarity / sweeps that USB would not produce, closable without faking leftover 13. Did not UpdateGoal complete. Did not invert `_dmm_volt` for RS1G14. Did not re-hunt 0.12 unknown-ITEM. No live USB 218. No NI-VISA.

## Verdict

Holes found+fixed: none.
Leftover 13: stays 13.
SIM n/ok: 218/218. REALIZED=205 LEFTOVER=13.
Goal: OPEN.

Current tree (not chat):

- `ate/core/_check_data/sim_stamps.json` n=218 ok=218 ran=218
- `ate/core/_check_data/physics_enabled.json` n=218 realized=205 leftover=13; every row has a `file`
- `python -m ate.core.check_add_test` OK
- `python -m ate.core.check_sim_run` OK (unknown ITEM `PER=9.91e+37`)
- `python -m ate.core.check_all_parts` OK `SIM 218/218 physics REALIZED=205 LEFTOVER=13`

No Path B / `sim.py` / worker edit. Worker not restarted.

## Closable hunt (all empty)

Parsed every stamp row:

- NaN / non-finite: 0
- Rigol-invalid `|v|>1e10`: 0
- VOH < VOL (same test and cross-test same VCC suffix): 0
- VIH < VIL: 0
- ICC / `*_uA` negative: 0
- Q7_LOW stuck at VCC (`serial_shift`): 0
- MUST_STAMP missing unique enabled `test_id`: 0 (`check_all_parts.must_stamp_missing_ids`)
- physics_enabled missing SKU/test `file`: 0
- Path B `if sim:` skip except leftover iso couple: only `ate/tests/lim/iso.py:28` after `:MEASure:ITEM? VPP,CHAN2` (`iso.py:26-29`)

VOL_load flat 0.001 across VCC is CMOS floor (`_dmm_volt` VIN low -> 0.001), not a dead sweep. rs1g126 ICC/II/IOFF/IOZ all 0.084 uA is SIM one-node DMM when PSU CH2+CH3 on (`sim.py:299-301`); USB pin topology is not closable without a pin-aware DMM that would break IOZ << ICC (`check_sim_run`).

## Leftover 13 (must stay; do not reclassify)

`MUST_STAY_LEFTOVER` is `physics_scale.py:112-126` / `:149-150`. Closing any of these without new bench gear would fake leftover 13.

1. lm358 settling -- `ate/tests/opa/settling.py:73` queries CHAN2 VPP; `:128-137` stamps `SETTLE_VPP_V`. Photo/cursor, not 0.1% SETTLE_us.
2. rs358 settling -- same body.
3. rs622 settling -- same body.
4. rs0302 i2c_ron -- `ate/tests/logic/rs0302.py:119` and `:127` force 10 mA. Datasheet 64 mA leftover.
5. rs2227 usb_ron -- `ate/tests/lim/rs2227.py:5` PDF image rON; `:44` / `:109-111` stamps 10 mA force.
6. rs2227 usb_iso -- `ate/tests/lim/rs2227.py:186-208` 1 MHz high-Z via `chan2_off_vpp`. Not 550 MHz 50 ohm (MSO 70 MHz).
7. rs2227 usb_xtalk -- same helper / same BW leftover.
8. rs2323 ron -- `ate/tests/lim/rs2323.py:409-414` 10 mA; PDF rON min/max leftover.
9. rs2323 iso -- `ate/tests/lim/iso.py:1-5` and `:21-29`. 1 MHz high-Z, not 110 MHz RF.
10. rs2323 xtalk -- `ate/tests/lim/xtalk.py:1-5` same 1 MHz / 70 MHz leftover.
11. rs358 noise -- `ate/tests/opa/noise.py:1-4` 0.1-10 Hz Vpp, not nV/rtHz; ISC missing.
12. rs622 noise -- same body.
13. rs8551 noise -- same body.

## Named leftover-honest (not leftover 13, not closable)

Do not fake these in software:

- RS1G14 VOH/VIH/VOL buffer polarity -- `ariff_dc.py:625` drives VIN=VCC for VOH; `_dmm_volt` (`sim.py:327-381`) has no invert. `check_add_test.py:765-767` bans inventing CMOS invert. `cmos_prop.py:73-76` uses RFDelay/FRDelay for tPD only.
- LIR~1600 / LOR=0 -- `ldo.py:247-253` / `:297-303`. SIM DMM follows VIN (`sim.py:381`).
- SR~5.55 vs typ 0.5 -- `sim.py:188-189` 1-pole SLEW. lm358/rs358/rs622/rs8551 stamps 5.55 V/us.
- GBW 7.006 G11 1-pole -- `sim.py:282-284`. Under 70 MHz ban.
- DELAY two-bin ~50 ns -- `sim.py:190-199`. rs29511 TEN=100000 ns us-window (`oe_timing.py:88`); TDIS=50 ns ns-window.
- pulse 0.5/f not board RC -- `sim.py:200-208`. rs1g123 PULSE_ns=500000.
- POWERON_ns us-window -- `power_on.py:34` timebase 20 us -> 40000 ns.
- FMAX 20 Mbps AWG cap vs datasheet 50 -- `rs0204.py:485`.
- TR/TF 5 ns MSO 70 MHz ceiling -- `sim.py:134-136` / `:209-212`.
- VOS_mV=0 -- Vos_dut=0 on G201 (`vos.py:105`; `sim.py:219`).
- OVERSHOOT=0 -- 1-pole, not 0.12 dummy (`sim.py:213-215`).
- IOUTMAX VIN substitute when DMM looks dead -- `ldo.py:349-353`.
- tsu/th stamp TEN_ns/TDIS_ns -- workbook names (`check_all_parts.py:87-95`).
- wait_slew_statistics SIM COUNT skip -- `ate/drivers/mso5072.py:203-204` (ITEM query still runs).
- `imported_input_off_leakage.py:31` still `imported scaffold -- fill body`. Not enabled.

## Do not

- Reclassify leftover 13 as REALIZED.
- Invert SIM DMM for RS1G14.
- Fill or enable `imported_input_off_leakage`.
- Edit `runner.py` / goldens rewrite / `input()` / `Lim` / `Ariff` / `Soo`.
- Close goal (live USB DMM/MSO unproven; leftover 13 is method ceiling).
