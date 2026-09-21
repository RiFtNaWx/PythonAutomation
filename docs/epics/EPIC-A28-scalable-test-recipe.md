# EPIC-A28 - Scalable test recipe

**PRD:** [PRD-004-scalable-test-recipe.md](../prd/PRD-004-scalable-test-recipe.md)
**Status:** implemented (2026-09-15)
**Do not reopen:** A01-A27 as failed. A13/A14 stay parked.
**Next:** Parameters + 2^n + who-source; then checks.

## Goal

1. `vcc_list` / `logic_inputs` / `levels` / `rails` in `_manifest/test_params.yaml` (and part yaml).
2. `RunParams.resolved_vcc_sweep` honors `vcc_list` from overlay.
3. Uncap `_logic_inputs`; `itertools.product` corners in Ariff DC bodies.
4. Test program Parameters UI: VCC list, n, rails digits; Write.
5. Results who-has-what: operator x SKU x test id x source file:line.

## Out of epic

- A14 xyflow; wizard-Python; Comparator bodies; copy-between-people.

## Checks

```
python -m ate.core.check_walk_order
python -m ate.core.check_ui_contract
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
```
