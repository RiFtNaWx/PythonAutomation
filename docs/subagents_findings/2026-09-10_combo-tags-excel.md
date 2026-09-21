---
keywords: combobox, dropdown, caret, tags, compact, +N more, excel, identity.tags, datalist
main_idea: Native datalist does not open on Chrome/Windows. Setup path fields use a body-level .combo menu (click/caret, type-to-add, x). Tags Space/Enter add; chips show last + "+N more". save_tags stamps the lab xlsx Tags cell.
---

# 2026-09-10 Combo menus + compact tags + Excel stamp

PREFLIGHT: PARTIAL. Reuse: setup-combo-level, a17-tags-session-datalog. Spawn: skip.

## Why dropdowns looked dead

`<input list=datalist>` has no caret and Chrome/Windows often will not open the list on click. `select { appearance: none }` also hid native arrows. Fix: `.combo` + `#ate-combo-menu` appended to `body` (z-index 4000, not clipped by `.panel`). Native selects get a CSS chevron.

## Behavior

- Component / Part / Package / Operator / Version / Kind / Value / board: click box or caret, filter, Add {typed}, x clears. Version/part still create folders via Apply / `ensure_version` / `ensure_tree`.
- Do not delete campaign folders when x is clicked on a list row. x on tag/label rows removes campaign tokens only.
- Tags: type in `#db-tag-input`, Space or Enter adds. Chips below: last tag + `+N more`; click expands; chip x removes.
- `save_tags` writes tags.yaml + TAGS.txt and stamps a Tags row on the campaign xlsx (column A must already say Tags, or a new Tags row is appended). Wrong default B2 is not used (that cell is often Sample Size). Locked workbook -> `excel_status: locked`, yaml still saved.

## Checks

`python -m ate.core.check_ui_contract`
`python -m ate.core.check_tags_datalog`
`python -m ate.core.check_new_product`
