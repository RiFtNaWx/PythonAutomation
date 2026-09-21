# RS29511 SDA Path B + fail-closed physics map

keywords: junior, rs29511, tp, tidle, rs29511_prop, wraps, physics_scale, leftover-honest, sim, seelim, vos
main_idea: RS29511 tp/tidle is Path B SDAIN->SDAOUT (not CMOS Y wrap). Every enabled (part, test) is REALIZED or LEFTOVER or the check fails. SIM 218/218 is not USB-ready and not physics-complete.

## What landed

- `ate/tests/logic/rs29511_prop.py` -- EN jumper to VCC, AWG SDA, MSO SDAIN/SDAOUT. Does not `register(tp)` (Ariff keeps the wrap id).
- `wraps.py` routes `part==rs29511` tp/tidle to that body. Other SKUs still `logic_tests.test_tp`.
- Limits: TPD_PHL_ns max 50 (tPZL). TPD_PLH_ns has no max -- SIM ns-window is 50 ns, datasheet tPLZ max is 10 ns.
- `ate/core/physics_scale.py` -- fail-closed map consumed by `check_all_parts` / `check_add_test`. Missing class = fail. BW/AOL/settle/noise/10 mA rON must stay leftover.

## Proof this sitting

- `python -m ate.core.physics_scale` -- 218 rows, REALIZED=183, LEFTOVER=35, unclassified=0
- `python -m ate.core.check_sim_run` -- RS29511 tp SDA Path B, TEN tIDLE-class, TDIS ns-window
- `python -m ate.core.check_all_parts` -- yaml=26 SIM 218/218 physics REALIZED=183 LEFTOVER=35
- `check_add_test` / `check_family_load` / `check_specs_datalog` OK

## Spec judge leftover (same sitting)

SeeLim ICC/II nested `at_VCC=5.5` was judged against ICC_uA max 1.0 when measurements were empty (`_prefer_spec_ids` fell back to flatten). VOS SIM slope 0 stamps nan. Fixes: prefer spec ids only; seelim always stamp ICC_uA/II_uA; vos omit non-finite VOS_mV; leftover-name vos_sweep.

## Leftover-honest (goal not complete)

- Analog-switch BW 110/550 MHz on a 70 MHz MSO -- iso/xtalk/usb_iso/usb_xtalk stay 1 MHz high-Z
- BUFFER/G11 cannot measure AOL_dB; settling is photo; noise is 0.1-10 Hz Vpp not nV/rtHz; ISC missing
- rON / i2c_ron 10 mA platform; RS0302 datasheet 64 mA
- CMOS wrap `tp`/`tidle`/`supply_current`/`output_voltage`/`cap_load` still goldens (except RS29511 tp/tidle and eugene IDD)
- SIM DELAY two bins; cannot prove tPLZ 10 ns
- USB START of every SKU with instruments plugged in is not this sitting
- Path C `input_off_leakage` scaffold must stay unfilled
- RS74AUP1G07 no PDF VOH; SeeLim RS1G97 no VOH/VOL in his tree
