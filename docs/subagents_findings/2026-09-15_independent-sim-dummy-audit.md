keywords: independent-audit, sim, dummy, 9.91e37, leftover-13, leftover-honest, goal-open, rs1g14, imported_input_off_leakage
main_idea: Independent tree audit found no closable SIM dummy / SCPI-skip hole. Unknown MSO ITEM is Rigol invalid 9.91e37 not 0.12. Leftover stays 13. SIM 218/218 REALIZED=205. Goal OPEN.

# Independent SIM dummy audit (2026-09-15)

PREFLIGHT: PARTIAL. Related 2026-09-15 findings exist. This pass treated claims as unproven and used the current tree + live checks as authority. Did not resume prior conclusions. Did not UpdateGoal complete. Did not invert DMM for RS1G14. Did not reclassify leftover 13. No live USB re-skip. No NI-VISA hammer.

## Verdict

Holes found+fixed: none.
Leftover 13: stays 13.
SIM n/ok: 218/218. REALIZED=205.
Goal: OPEN.

Independent live probe (not JSON trust):

- `:MEAS:ITEM? PERIod,CHAN1` -> `9.91e+37` (not 0.12)
- `:MEAS:ITEM? DUTY,CHAN1` -> `9.91e+37`
- `:MEAS:ITEM? OVERSHOOT,CHAN2` -> `0.0` (1-pole, not 0.12)
- loopback `unknown_item_not_dummy` ok, `PER=9.91e+37`
- `return 0.12 if driven` absent. `return 500e-9` absent.

Checks this pass:

- `python -m ate.core.check_add_test` OK
- `python -m ate.core.check_sim_run` OK (unknown ITEM Rigol invalid not 0.12)
- `python -m ate.core.check_all_parts` OK `SIM 218/218 physics REALIZED=205 LEFTOVER=13`

No loaded code edited. Worker not restarted.

## What was inspected

- `ate/instruments/sim.py` `_scope_item` unknown fallback `sim.py:285-286` `return 9.91e37`. Known ITEM (VPP/DELAY/PWID/RTIME/OVER/VAVG) modeled from AWG/PSU bus. Unmatched non-ITEM `query` fallthrough `sim.py:557` `return "0\n"` is unused by Path B stamps (`measure_delay` / `measure_single` / `:READ?` / ITEM? all hit modeled arms). SIM session never sends `*IDN?` (USB discovery only). Dead `_IDN` dict `sim.py:19-24` is not a stamp dummy.
- Path B `if sim:` skip of USB SCPI: only `ate/tests/lim/iso.py:28` *after* `:MEASure:ITEM? VPP,CHAN2` (`iso.py:26-29`). `check_all_parts.sim_skip_scpi_files` (`check_all_parts.py:196-210`) bans any other `if sim:` under `ate/tests`. xtalk / usb_iso / usb_xtalk reuse that query-then-couple helper.
- `imported_input_off_leakage.py` still `imported scaffold -- fill body` (`imported_input_off_leakage.py:31`). Not in any `parts/*.yaml` `enabled_tests`. `check_all_parts.py:464-468` fail-closes if filled/enabled. `check_add_test.py:110-113` keeps the fill-body marker.
- RS1G14 DMM: `_dmm_volt` (`sim.py:327-381`) has no invert. `check_add_test.py:765-767` bans inventing CMOS invert on the SIM DMM rail. `cmos_prop.py:73-76` uses RFDelay/FRDelay for tPD (MSO), not a DMM invert.

## Named leftover-honest (do not reclassify)

MUST_STAY_LEFTOVER is `physics_scale.py:112-126` / `149-150`. Closing any of these without new bench gear would fake leftover 13.

1. lm358 settling -- `ate/tests/opa/settling.py:73` queries CHAN2 VPP; `:128-137` stamps `SETTLE_VPP_V`. Photo/cursor, not 0.1% SETTLE_us.
2. rs358 settling -- same body.
3. rs622 settling -- same body.
4. rs0302 i2c_ron -- `ate/tests/logic/rs0302.py:119` and `:127` force 10 mA. Datasheet 64 mA leftover.
5. rs2227 usb_ron -- `ate/tests/lim/rs2227.py:5` PDF image rON; `:109-111` stamps 10 mA force.
6. rs2227 usb_iso -- `ate/tests/lim/rs2227.py:186-208` 1 MHz high-Z via `chan2_off_vpp`. Not 550 MHz 50 ohm (MSO 70 MHz).
7. rs2227 usb_xtalk -- same helper / same BW leftover.
8. rs2323 ron -- `ate/tests/lim/rs2323.py:409-414` 10 mA; PDF rON min/max leftover.
9. rs2323 iso -- `ate/tests/lim/iso.py:1-5` and `:21-29`. 1 MHz high-Z, not 110 MHz RF.
10. rs2323 xtalk -- `ate/tests/lim/xtalk.py:1-5` same 1 MHz / 70 MHz leftover.
11. rs358 noise -- `ate/tests/opa/noise.py:1-4` 0.1-10 Hz Vpp, not nV/rtHz; ISC missing.
12. rs622 noise -- same body.
13. rs8551 noise -- same body.

Not leftover-13, also not closable without faking a DUT model:

- `wait_slew_statistics` SIM early return `ate/drivers/mso5072.py:203-204` skips COUNT *wait*, not the later ITEM query.
- LDO LIR/VIN-as-VOUT (`ldo.py:349-353` ioutmax VIN substitute when DMM looks dead): `_dmm_volt` cannot grow an LDO model without breaking SeeLim OE (`sim.py:369-370`). Not a DMM invert. Not a new leftover row.
- `runner.py` `mock_demo_measurements` (`runner.py:892-896`) is unused by the 218 stamp path (every enabled id stamps). Do not edit `runner.py`.

## Do not

- Reclassify leftover 13 as REALIZED.
- Invert SIM DMM for RS1G14.
- Fill or enable `imported_input_off_leakage`.
- Edit `runner.py` / goldens rewrite / `input()` / `Lim` / `Ariff` / `Soo`.
- Close goal.
