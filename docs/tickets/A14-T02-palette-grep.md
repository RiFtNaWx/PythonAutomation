# A14-T02 - Opcode palette + product/user grep

**Epic:** [EPIC-A14-recipe-canvas.md](../epics/EPIC-A14-recipe-canvas.md)
**Status:** implemented
**Depends on:** A14-T01

## Acceptance

> WHEN the palette lists opcodes, THE SYSTEM SHALL offer sweep, for_corners, for_list, if_else, pause, psu_set, awg_out, dmm_read, scope_detect, screenshot, measure, end.
> WHEN for_corners n=2 levels=[0,5.5], preview_corners SHALL return four corners.
> WHEN product typeahead hits an inventory/parts key, attach_product SHALL upsert owners.yaml parts for this operator.
> WHEN Comparator is selected as family on a recipe, THE SYSTEM SHALL keep run_ic comparator live: false (no FAMILY_PACKAGES edit).

## Touch

- canvas palette UI
- `preview_corners` / `attach_product` / `attach_person` RPCs
- relationship panel on `#page-recipe`

## Do not

- Live Comparator TestSpecs
- Walker runtime (T03)
- Scrape en.run-ic.com
