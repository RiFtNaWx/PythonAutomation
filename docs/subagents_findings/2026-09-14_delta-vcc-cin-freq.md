---
keywords: delta-supply, vcc-sweep, awg-ch1-ch2, cin-freq, cpd-dwell, vcc-start
main_idea: Setup panel VCC start/stop/step (0 to 5 by 0.5). Delta Supply sweeps that and alternates AWG CH1/CH2. CIN OFF then FREQ so 1/5/10 MHz actually steps. CPD waits 5 s per VCC 1.8-5.
---

# 2026-09-14 Delta sweep panel + CIN freq + CPD 5s

Delta Supply used one VCC and four near-threshold combos. CIN APPL while AWG stayed ON so 1/5/10 MHz did not change on the DG822. CPD dwell was 2 s.

Fix:
- `#vcc-start` / `#vcc-stop` / `#vcc-step` on Setup before START
- Delta: `resolved_vcc_sweep`, AWG CH1 high then CH2 high
- CIN: `:OUTP1 OFF`, APPL, `:SOUR1:FREQ`, ON, log `FREQ?`
- CPD: `_CPD_DWELL_S = 5.0` at 1.8 / 2.5 / 3.3 / 5.0

Check: `python -m ate.core.check_walk_order` and `python -m ate.core.check_ui_contract`.
