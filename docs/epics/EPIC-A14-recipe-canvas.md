# EPIC-A14 - Recipe canvas + closed interpreter

**PRD:** [PRD-005-recipe-canvas.md](../prd/PRD-005-recipe-canvas.md)
**Status:** implemented (2026-09-15)
**Do not reopen:** A01-A28 as failed. A13 stays parked.
**Next:** operator DEMO demo_corners on SIM; optional Export Path B later.

## Goal

1. Recipe tab `#page-recipe` + xyflow island on `#recipe-root` (committed dist under `ate/ui/web/canvas/`).
2. Save/load `ate/config/recipes/<id>.yaml` (+ optional Version overlay `_manifest/recipe_graph.yaml`).
3. Closed opcode walker `ate/core/recipe_walk.py`; one hook in `runner._run_one`.
4. Product/user grep attach; Comparator class stays `live: false`.
5. `python -m ate.core.check_recipe` + `check_ui_contract`.

## Out of epic

- A13 Excel MCP; live Comparator bodies; unrestricted eval; Path A becomes canvas.

## Tickets

| ID | Name | Done when |
|----|------|-----------|
| A14-T01 | Shell | Recipe tab + hello graph + save/load yaml + dist committed |
| A14-T02 | Palette + grep | Opcode nodes + corner preview + product/user typeahead |
| A14-T03 | Walker + DEMO | `recipe_walk` + `_run_one` hook + DEMO SIM recipe id |

## Checks

```
python -m ate.core.check_recipe
python -m ate.core.check_ui_contract
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_walk_order
```
