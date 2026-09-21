---
keywords: logic, demo, runPollActive, waitForRunComplete, awg-gen, 2^n, mso-probes
main_idea: DEMO/RUN stuck after worker restart (stale runPollActive). 2^n is AWG corners not extra MSO channels. recipe_walk awg_out must use instr.gen.
---

PREFLIGHT: HIT. Reuse 2026-09-15_logic-demo-run-fail.md, 2026-09-15_logic-awg-mso-channels.md.

## Fix this sitting

1. `app.js` waitForRunComplete: after 10 idle polls with `!busy && epoch <= startEpoch`, throw Worker restarted -- Ctrl+F5 then DEMO. startInstrumentRun clears stale `runPollActive` when worker is idle.
2. `recipe_walk.awg_out` drives `instr.gen` (session AWG handle). `Instruments.awg` is an alias of `.gen`.
3. Parameters + Recipe tab hint: 2^n = AWG input corners; MSO stays CH1=stim CH2=Y.

## How Logic channels work

- AWG CH1/CH2: DUT input stimulus. `logic_inputs` n -> 2^n corners. n>2 pause_hook rewire.
- MSO CH1/CH2: two probes only (stim + Y/Q). Never scales with n.
- CHA/CHB: DUT socket walk (`run_prefs`). Logic TestSpecs `dual_channel=False`.
