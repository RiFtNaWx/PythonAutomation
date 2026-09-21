---
keywords: cin, cpd, usb, mso, jpeg, tmo, automated, logic, rs1g07, dmm
main_idea: Latest Logic START was real USB, not DEMO. "Automated: Cin" is a timeline label. Cin hung because it still recovered MSO and grabbed JPEGs. Skip MSO on DMM tests.
---

# 2026-09-14 Logic CIN hung on MSO during USB START

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_opamp-start-sim-continue. Spawn: skip.

## What was true

Session `112525` is USB (`sim False`, mapping PSU/AWG/DMM/MSO). No `SIM auto-continue`. Continue already happened for LOGIC + DUT_1. Worker `busy` with `pending None` = stuck inside CIN measure, not on a Continue modal.

`Automated: Cin CHA` is `timeline.next_hint`, not DEMO.

## Why it sat there

CIN/CPD are DMM current. Runner still `recover_scope_session` + `park_scope_idle` whenever MSO is in the session. CIN also called `_shot` -> `capture_jpeg` (20s TMO, retry) x 3 freqs. Looks like a frozen demo.

## Fix

- Recover/park MSO only if the TestSpec requires MSO.
- CIN/CPD: DMM only, log each step, no JPEG.
- `_ask_operator` emits `waiting_operator` so the pill is WAIT.
- Timeline says `Measure` not `Automated`.

Does not prove a live USB CIN `:READ?` if DMM is poisoned.
