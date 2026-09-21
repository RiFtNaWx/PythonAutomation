# A14-T01 - Recipe shell (tab + xyflow island + save/load)

**Epic:** [EPIC-A14-recipe-canvas.md](../epics/EPIC-A14-recipe-canvas.md)
**Status:** implemented
**PRD:** [PRD-005-recipe-canvas.md](../prd/PRD-005-recipe-canvas.md)

## Acceptance

> WHEN the operator opens the Recipe tab, THE SYSTEM SHALL show `#page-recipe` with `#recipe-root` mounting the committed canvas dist.
> WHEN Save recipe runs with a valid id, THE SYSTEM SHALL write `ate/config/recipes/<id>.yaml`.
> WHEN Path A `#campaign-tests` reorder is checked, THE SYSTEM SHALL still use HTML5 drag (not xyflow).

## Touch

- `ate/ui/web/index.html` + `app.js` + `styles.css` (Recipe tab)
- `ate/ui/canvas/` (Vite + @xyflow/react source)
- `ate/ui/web/canvas/` (committed dist)
- `ate/core/recipe_store.py` (list/load/save yaml)
- worker RPCs `list_recipes` / `save_recipe` / `load_recipe`
- `pack_ate_console.py` include dist
- `check_ui_contract` asserts `#page-recipe` + `#recipe-root`

## Do not

- Implement walker (T03)
- Full opcode palette (T02)
- Edit `runner.py` yet
- Require npm for zip users
