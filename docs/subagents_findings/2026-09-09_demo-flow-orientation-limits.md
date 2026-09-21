---
keywords: demo, orientation, limits, vccb, vol, current_limit, fixture-order, lm358, power_on_time
main_idea: DEMO now requires ticked tests, walks fixture order, mocks VOL low / current as i_ua / dual-rail VCCB on PSU CH2, and overlays part current_limit. Empty DEMO no longer dumps every Logic slot.
---

# DEMO flow orientation + limits (2026-09-09)

PREFLIGHT: PARTIAL. Reuse: new-product-demo, operator-flow-e2e, operator-default-eugene. Spawn: skip.

## What was wrong

- Empty DEMO called `all_tests()` so Logic mixed Soo + Ariff + RS0204 on one walk.
- Every DMM mock was `0.96*vcc` -- VOL looked like a VOH fail vs spec_max ~0.5 V.
- RS0204 DEMO omitted VCCB / PSU CH2.
- Part yaml `current_limit: 0.05` never reached `psu_golden` (UI sent 0.10).
- BUFFER catalog listed `power_on` but the spec id is `power_on_time` (sorted last).
- RS29511 fixture label said "level-shifter board".
- LM358 had no `enabled_tests` so training showed VOS research slots.
- DEMO jumped to Results so the Run timeline was hidden.

## What changed

- `build_demo_steps`: fixture order, VOL low, leakage `i_ua`, VCCB on CH2, current_limit.
- UI: tick tests first; timeline shows fixture + label; land on Run.
- `list_tests` honors opamp `enabled_tests` (LM358 general board only).
- Checks: `check_new_product` (VOL/VCCB/i_ua), `check_family_load` (rs1g08 0.05 A).

Left alone: SOT23 vs SC70-5 campaign folder names (disk trees + `check_open_inventory` still SOT23). TTSOP8 lab spelling.
