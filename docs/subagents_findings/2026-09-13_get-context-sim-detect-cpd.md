---
keywords: get_context, UnboundLocalError, building-plan, sim, pyvisa, demo, detect-tab, cpd, cin, rs1g07
main_idea: START stuck on Building plan because run_sequence re-imported get_context (UnboundLocalError) before the plan or PSU ON. DEMO now opens a fake PyVISA session and runs the real START path. Detect/wrap moved off Setup onto a Detect tab. Eugene CPD/CIN enabled on RS1G07.
---

# 2026-09-13 START get_context + SIM DEMO + Detect page + Eugene CPD/CIN

## Cause

`ATECore.run_sequence` used module-level `get_context`, then later `from ate.core.database import get_context` inside the DUT loop. Python treats that name as local for the whole function, so the first `get_context()` raised UnboundLocalError. Timeline never built (banner stuck on Building plan), PSU never powered. Worker swallowed the exception; UI treated the run as finished.

## Shipped

- Remove the inner import; stamp `run_error` on session_status so the banner shows Failed
- `Instruments.simulated()` + Open SIM / DEMO uses fake SCPI (no USB)
- Detect tab for scan/wrap/copy; Setup/Run stay test-program only
- Eugene `cin` TestSpec + RS1G07 `cpd` dispatches to VCC+AWG square+DMM current (RS0204 pin Cio unchanged)
- `python -m ate.core.check_sim_run` (cin+cpd START on SIM)

## Check

```
python -m ate.core.check_sim_run
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
```
