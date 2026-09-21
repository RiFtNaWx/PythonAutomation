---
keywords: cin, sweep, dwell, ovp, ocp, protect, delay, psu, dp832, rs1g07
main_idea: CIN re-armed OVP every 1/5/10 MHz so lamps flashed and the sweep had no dwell. Power PSU once, 2s per step, delay after OVP ceiling before VOLT, do not rewrite PROT:STAT if already ON.
---

# 2026-09-14 Sweep too fast / OVP click

User: USB Logic START skipped the freq sweep; OV/OC lamps flashed on/off.

Cause: `_power_awg` called `power_on_protected` on every CIN MHz (OVP 6.0 then tighten, STAT ON rewrite). Dwell was 0.5 s.

Fix: CIN PSU once then AWG freq only. CPD/IDD 2 s dwell. `power_on_protected` arm delay 0.4 s after ceiling; skip STAT ON if already armed.

Check: `python -m ate.drivers.check_psu_protect` and `python -m ate.core.check_walk_order`.
