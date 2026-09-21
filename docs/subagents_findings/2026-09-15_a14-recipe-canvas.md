---
keywords: a14, recipe-canvas, xyflow, closed-opcode, recipe_walk, prd-005, demo_corners
main_idea: A14 unparked. Recipe tab + committed xyflow dist. Closed ISA walker on START/DEMO. No eval. Comparator stays live:false.
---

PREFLIGHT: PARTIAL reuse scalable-test-recipe + per-test-params.

## Shipped

1. PRD-005 + EPIC-A14 + tickets T01-T03; ledger unpark (INDEX/SHIP_NEXT/AGENTS/UI_CONTRACT/ate-prompt).
2. Recipe tab `#page-recipe` + `#recipe-root`; Vite `@xyflow/react` island; dist at `ate/ui/web/canvas/`.
3. `ate/core/recipe_store.py` + `recipe_walk.py` + `check_recipe.py`; example `demo_corners.yaml`.
4. Worker RPCs: list/load/save_recipe, preview_corners, grep/attach product+person.
5. `load_family` registers recipes; `runner._run_one` walks `notes` starting with `recipe:`.
6. Checks PASS: check_recipe, check_ui_contract, check_walk_order, check_add_test, check_sim_run.

## Not this wave

A13; live Comparator bodies; unrestricted eval; Path A becomes canvas.
