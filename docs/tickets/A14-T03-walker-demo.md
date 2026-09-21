# A14-T03 - Closed walker + DEMO

**Epic:** [EPIC-A14-recipe-canvas.md](../epics/EPIC-A14-recipe-canvas.md)
**Status:** implemented
**Depends on:** A14-T01, A14-T02

## Acceptance

> WHEN START/DEMO runs a registered recipe id, THE SYSTEM SHALL walk allowlisted opcodes via recipe_walk and return measurements.
> WHEN an unknown opcode appears, THE SYSTEM SHALL refuse (check_recipe fails).
> WHEN for_corners n=2, THE SYSTEM SHALL enumerate 4 corners.
> WHEN psu_set runs, THE SYSTEM SHALL call power_on_protected only.

## Touch

- `ate/core/recipe_walk.py`
- `ate/core/runner.py` `_run_one` one hook
- `ate/core/registry.py` `register_recipe_specs` after family import
- `ate/core/check_recipe.py`
- example `ate/config/recipes/demo_corners.yaml`

## Do not

- eval / exec
- Edit database.py path
- Unpark A13
