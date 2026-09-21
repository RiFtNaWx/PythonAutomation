---
keywords: prd-004, scalable-recipe, vcc_list, logic_inputs, 2^n, rails, who-has-what, a28
main_idea: Recipe keys on Test program Parameters (vcc_list, n, levels, rails) overlay via RunParams; ariff_dc uncapped 2^n corners; Results who-has-what table. No xyflow.
---

PREFLIGHT: PARTIAL reuse `2026-09-15_per-test-params.md`, plan ate_recipe_scale.

## Shipped

1. PRD-004 + EPIC-A28 docs.
2. `test_params` cleans `vcc_list` / `logic_inputs` / `levels` / `rails`; `resolved_vcc_sweep` honors `vcc_list`.
3. `ariff_dc` `_input_corners` via itertools.product; AWG n<=2 + pause_hook for n>2.
4. Parameters UI fields + `#progress-who-tests` from `who_has_tests()`.
5. Checks: walk_order, ui_contract, add_test, sim_run PASS.

## Not this wave

A14 xyflow; wizard-Python; Comparator bodies.
