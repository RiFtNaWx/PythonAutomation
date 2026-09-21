---
keywords: settle, 5s, sweep, safe-idle, mso-idn, post-test, delay, cin, idd, cpd, delta
main_idea: 5 s dwell belongs between sweep points, with a DMM delta log. The random hang after each test was runner SAFE IDLE parking MSO (*IDN TMO) plus AWG park -- skip that between tests; idle only at Continue, and skip MSO on DMM tests.
---

# Sweep settle 5s vs post-test hang

Symptom: parameter steps felt too fast; after a whole test the UI vanished or sat for a long random time.

Cause: `run_sequence` called `_safe_idle_for_operator` after every `_run_one`. That parks AWG (3x `:OUTP?`), PSU off, then `park_scope_idle` -> `*IDN?` at 20 s MSO timeout even for CIN/CPD/IDD. Continue was not shown until that finished.

Fix:
- `_SETTLE_S = 5` after each VCC/freq/AWG change; log `was` / `d=` and WARN if unchanged
- No SAFE IDLE after each test; idle at Continue only
- DMM Continue skips MSO park (`park_scope` only when the TestSpec needs MSO)
- Delta Supply dwell 5 s

Check: `python -m ate.core.check_walk_order` and `python -m ate.core.check_add_test`.
