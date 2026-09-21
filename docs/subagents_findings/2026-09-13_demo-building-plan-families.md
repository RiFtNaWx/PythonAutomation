---
keywords: demo, building-plan, run-epoch, claim-async, sim-sleep, logic, switch, level, power
main_idea: DEMO stuck on Building plan because waitForRunComplete treated busy=false as done before the run thread started. Claim busy + run_epoch first. SIM skips time.sleep. Logic/switch/level/power DEMO now complete like OpAmp.
---

# 2026-09-13 DEMO Building plan + non-OpAmp families

## Cause

`run_sequence_async` returned `{started:true}` before `run_sequence` set `_busy`. The UI loop saw `busy=false` and treated the run as finished. Banner stayed on Building plan / Complete with no new tests. DEMO also paid every `time.sleep` in Logic DC sweeps, so a full RS1G08 Select-all looked hung.

## Shipped

- `claim_async_run()` + `run_epoch` before the thread starts. UI waits until `epoch > epoch0 && !busy`.
- SIM `run_sequence` skips `time.sleep`.
- `python -m ate.core.check_demo_families` (cin+cpd, iplus, vih, iq).
- Live worker DEMO: RS1G07 cin/cpd, RS2323 iplus, RS0204 vih, RS3213 iq all success. UI DEMO RS1G08 Select-all finished (24 rows; VOL/VOH fail because SIM DMM voltage is a flat 3.3 V).

## Does not prove

- Live USB START.
- VOL/VOH numbers matching a real DMM (SIM voltage is 3.3 V).
