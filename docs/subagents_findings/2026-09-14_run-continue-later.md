---
keywords: continue, later, hide-popup, run-strip, wait, delay, run-page, gateHeld, notification
main_idea: Continue popup is wait-only. Later parks it to header Waiting + run strip. Other tabs stay usable. Next DUT/test does not start until Continue or Abort.
---

PREFLIGHT: PARTIAL. Reuse: 2026-09-13_prd-clean-run-ux, 2026-09-14_opamp-start-sim-continue. Spawn: skip.

## Concept

1. WAIT = operator gate (board / DUT / wiring). Popup or strip Continue / Abort.
2. DELAY = settle / dwell (e.g. CIN 5s). Strip shows countdown. No Continue.
3. RUN = measure. Timeline + log keep moving.
4. Hide popup with Later, dim click, or another tab. Header Waiting is the notification. Open brings the checklist back. Worker stays blocked.

## What was broken

- Overlay covered header + tabs, so you could not leave Run during a wait.
- No Later. hideModal treated hide as "prompt consumed".
- Poll `autoOpen: true` re-opened the popup every 350ms.
- Run page said "press Continue" with no button.

## Check

```
python -m ate.core.check_ui_contract
```

Does not prove a live USB Continue cycle. Ctrl+F5 the console (static UI). No worker restart.
