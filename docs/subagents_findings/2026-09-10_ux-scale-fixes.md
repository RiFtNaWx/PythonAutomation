---
keywords: ux-scale, combo-change, applyDb, duplicate-chips, owner-select, unassigned, run-conditions, layout-test, photo-setup, detect-family
main_idea: Existing-campaign combo picks still Apply; typed new Part/Package/Operator/Version wait for Apply. Duplicate Setup chips gone. Header Operator syncs to folder; All blocks writes. Logic photo hint is Setup not ORT.
---

# 2026-09-10 UX scale fixes (post combo/tags)

PREFLIGHT: PARTIAL. Reuse: 2026-09-10_combo-tags-excel, 2026-09-10_ui-dropdown-leftovers, 2026-09-10_operator-ux-leftovers. Spawn: skip (parent implemented).

## Shipped

1. Combo `change` calls `applyDb` only when `campaignKnown` (path already on disk). Typed new Version/Part logs "click Apply campaign to create".
2. `refreshDbCascades(sel, changedId)` keeps typed child values unless the parent field changed.
3. `#setup-label-chips` stays in HTML for `check_ui_contract` but is hidden; chips live under Tags only.
4. `syncOwnerSelectFromFolder` after folder change / `applyDb`. Header All rejected in `requireWriteOperator`. Default owner `eugene`.
5. Operator combo filters `_unassigned`. Header person switch uses latest `Version_N`.
6. Value combo Enter: `stopImmediatePropagation` then Add. Extra keydown listener removed. Board combo fills the box; Add board still commits.
7. Wrap family select keeps its value across detect refresh. `benchValues` copies all `paramCatalog.controls`. Empty layout-test shows `-- no mapped tests --`.
8. Tag combo x prunes `labelValueVocab`. `import_tags` restores `campaignLabels`. Combo Clear is `aria-label=Clear`.
9. Empty Logic/Level photo path falls back to `Setup`, OpAmp still `ORT`.

## Not done (on purpose)

- Native owner/inv/detect/layout/gain `<select>` stay native (they open).
- Lim vs SeeLim inventory pic mapping (config, not this UI pass).
- Hardware START.

## Checks

```
python -m ate.core.check_ui_contract
python -m ate.core.check_tags_datalog
python -m ate.core.check_operator_tree
python -m ate.core.check_new_product
```

UI cache `?v=20260910combo10`. Ctrl+F5. Worker restart after `database.py`.
Boot no longer calls `applyOwner` (that jumped to the person's default part / latest Version). Header onchange still does. Wrap family keeps the user's pick on Refresh/Wrap; Apply campaign resets it to the live family. `updateFamilyChrome` now sets the left rail + tracking sheet to the live family (Logic campaign no longer leaves OpAmp highlighted).
