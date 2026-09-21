---
keywords: opamp, start, continue, sim, auto-continue, demo, rs622, slew, 3.7, leftover-sim
main_idea: START skipped Continue because leftover Open SIM set gate.auto_continue. Fake 3.7 MV/s slew is SIM. START now always blocks; only DEMO passes auto_continue. USB *IDN + leftover SIM refuses START.
---

# 2026-09-14 OpAmp START looked like DEMO

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_real-logic-usb-speedrun, 2026-09-14_usb-slew-tmo. Spawn: skip.

## Symptom

OpAmp RS622 START walked BUFFER / DUT / CHB with `SIM auto-continue` and slew `SR+=3.7000 MV/s`. Operator saw no Continue block. Header tiles looked live (MSO/PSU/AWG/DMM on).

## Cause

`open_session(sim=True)` set `gate.auto_continue = True`. Later START (not DEMO) inherited that flag. SIM mapping still lights the four tiles. `3.7e6` V/s is `ate/instruments/sim.py`.

USB Discover earlier in the log was real. Then USB session closed, Open SIM / DEMO opened fake SCPI, campaign switched to OpAmp, START kept SIM.

## Fix

- Open SIM does not auto-continue.
- `RunParams.auto_continue` is True only for DEMO + headless checks.
- START + leftover SIM + USB *IDN -> notice, no run.
- SIM tiles use `.tile.sim` (amber). Notice banner no longer overwrites `#session-hint`.

## Check

```
python -m ate.core.check_visa
python -m ate.core.check_ui_contract
python -m ate.core.check_sim_run
```

Does not prove a live USB Continue cycle on RS622 BUFFER.
