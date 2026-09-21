---
keywords: junior, sim, delay, timebase, tidle, dc-current, usb-path, leftover-honest
main_idea: No-USB SIM delay follows MSO timebase (ns-window 50 ns vs us-window tIDLE ~100 us). DC VIN moves DMM current. RS29511 tp wrap now Continue-wires I2C. Not junior-100%.
---

PREFLIGHT: PARTIAL
reuse: `docs/subagents_findings/2026-09-15_own-code-bank-sim.md`, `2026-09-15_rs29511-en-ready.md`
spawn: skip

## Closed this sitting

1. `ate/instruments/sim.py`: DELAY is 50 ns when timebase < 10 us (CMOS / tDISABLE). DELAY is 2*timebase when timebase >= 10 us (RS29511 TEN at 50 us/div -> 100 us). Not a SPICE model.
2. DC AWG VIN raises SIM DMM current so II / DeltaICC / IDD sweeps are not flat. CIN/CPD still C*V*f at >= 1 MHz square.
3. `check_sim_run` asserts ns-window vs tIDLE-class TEN. RS29511 `tp`/`tidle` wrap Continue names EN=VCC and SDAIN/SDAOUT (do not rewrite `logic_tests.py`).
4. `check_all_parts` SIM scale (no USB).

## Leftover-honest (goal not complete)

1. SIM is two delay bins, not analog EN/READY or USB leakage nA.
2. Analog-switch 110/550 MHz BW. AOL/EMIRR mapped screenshots. Settling photo. ISC missing.
3. RS0302 64 mA RON. SeeLim RS1G97 VOH. Path C `input_off_leakage`. USB instruments still unplugged -- live START not proven.
4. RS29511 `tp` body is still Soo square IN->OUT (tPLZ/tPZL-class), comments still say level shifter.
