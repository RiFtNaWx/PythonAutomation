---
keywords: sim, unknown-item, 0.12, dummy, 9.91e37, leftover-honest, leftover-13, goal-open
main_idea: Last closable dummy was unknown MSO ITEM returning 0.12. Now Rigol invalid 9.91e37; stamps reject abs>1e10. No more closable holes without faking leftover-honest. Leftover 13 stays 13. Goal OPEN.
---

PREFLIGHT: PARTIAL
reuse: `docs/subagents_findings/2026-09-15_sim-npr-overshoot.md`, `2026-09-15_sim-serial-q7-pwid.md`
spawn: skip

# SIM unknown-item dummy closed (2026-09-15)

## Closed this sitting

Unknown MSO ITEM no longer stamps 0.12. USB Rigol returns 9.91e37 for invalid ITEM. Path B bodies do not query PERIod/PDUTy/UNDR; the old fallback was a silent landmine.

1. `ate/instruments/sim.py:286` `_scope_item` fallback is `return 9.91e37` (was `return 0.12 if driven else 0.001`).
2. Loopback `unknown_item_not_dummy` queries `:MEAS:ITEM? PERIod,CHAN1` and requires abs>1e10.
3. Fail-closed: `check_add_test` bans `return 0.12 if driven`. `check_sim_run` rejects PERIod==0.12. `check_all_parts` `_finite_stamp` / `_scope_invalid` reject abs>1e10 (invalid is not a value).

Did not invert `_dmm_volt`. Did not reclassify leftover 13. Did not fake RS1G14 polarity.

## Not closed -- leftover 13 (do not fake)

`ate/core/physics_scale.py:112-126` `LEFTOVER_PAIRS` still 13:

- iso/xtalk 1 MHz not 110 MHz (`ate/tests/lim/iso.py:28` `if sim:` after CHAN2 query)
- usb_iso/usb_xtalk 1 MHz not 550 MHz
- ron/usb_ron/i2c_ron 10 mA
- settling SETTLE_VPP_V not 0.1% SETTLE_us
- noise Vpp not nV/rtHz

## Not closed -- leftover-honest (file:line)

These need a DUT/SPICE model or live USB. Closing them in software would fake leftover 13 or invert DMM.

- RS1G14 VOH/VIH/VOL buffer polarity: `ate/tests/logic/ariff_dc.py:625` `_drive_inputs(..., vcc, vcc)` for VOH. USB inverter wants A=0. Do not invert `_dmm_volt`.
- LIR~1600: `ate/tests/power/ldo.py:242` DMM follows VIN. No LDO model.
- LOR=0 / IOUTMAX VIN swap: same file `_run_lor` / `_run_ioutmax` (~297, ~351).
- SR~5.55 vs 0.5: `ate/instruments/sim.py:189` `3.7e6 * max(vpp, 0.05)`.
- GBW 7.006: `ate/instruments/sim.py:282` G11 `7.0e6 / 11.0`.
- DELAY two-bin ~50 ns: `ate/instruments/sim.py:190-199` ns-window 50e-9; us-window 2*timebase.
- pulse 0.5/f not board RC: `ate/instruments/sim.py:200-208`.
- POWERON_ns=40000: `ate/tests/opa/power_on.py:34` timebase 20e-6 -> DELAY us-window.
- NPR clip = rail-sum, not phase-reversal SPICE (`sim.py:275-281`).
- SSSR OVERSHOOT=0 leftover 1-pole (`sim.py:213-215`).
- SIM COUNT=120 dummy (`sim.py:184-185`) -- not stamped; wait_slew only.
- `imported_input_off_leakage.py` stays unfilled / not enabled.
- Live USB DMM+MSO still unproven (`live_usb_stamps.json` ok=0).

## Hunt result

No other Path B hardcoded `"value": <number>` stamps. No 0.12 / 9.91e37 / NaN in `sim_stamps.json`. No BW>70 / AOL_dB / G11*large VPP in current stamps. Remaining holes above cannot close without faking.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **218/218**. physics REALIZED=205 LEFTOVER=13. `sim_stamps.json` n=218 ok=218.

Worker idle-restarted on 8766 after `sim.py`. Goal stays OPEN (live USB DMM/MSO unproven).
