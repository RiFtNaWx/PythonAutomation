---
keywords: voh, vol, pause_hook, continue, rs1gt34, logic-board, leftover-honest
main_idea: VOH and VOL wiring differs. Continue waits before each on every logic board (ariff_dc + rs0204). Do not keep VOH setup for VOL.
---

# 2026-09-18 VOH/VOL Continue wait

PREFLIGHT: HIT. Reuse ariff-dc, rs1gt34-vih-vil-live. Spawn: skip.

## Job

RS1GT34 VOH is connected. VOL setup is different. Always wait before VOH and before VOL on all logic parts/boards.

## Change

- `ate/tests/logic/ariff_dc.py` `_pause_voh_vol` before PSU on. Distinct titles: VOH (not VOL) vs VOL (not VOH).
- `ate/tests/logic/rs0204.py` same gate on dual-rail voh/vol.
- Checklists on rs1gt34 / G / GT / rs1g07 / rs1g125 / rs0204: `Continue waits before`.
- `check_add_test` fail-closes pause-before-power and the checklist phrase.

Not runner.py. DEMO `auto_continue` still skips the wait. USB START stops.

## Proof

```
python -m ate.core.check_add_test
```

SIM RS1GT34 `voh_load` then `vol_load` auto_continue: VOH 5/5 PASS | VOL 5/5 PASS. Does not prove USB Vref/IOL numbers.

## Operator

If a START is already running, do not restart. Rewire VOL, then Continue. After idle: `restart_ate_worker.bat`, Ctrl+F5, START VOL -- wait at the VOL banner.
