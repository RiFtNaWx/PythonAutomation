---
keywords: combobox, version, labels, datalist, +version, level-rail, rs0204, suite-alias
main_idea: Setup Component/Part/Package/Operator/Version/labels are one shared editable datalist (no +Version, no Or type). Level rail is not a stub; it lists tracking SKUs and loads the RS0204 dual-rail suite.
---

# 2026-09-10 Setup combobox + Level SKUs

PREFLIGHT: PARTIAL. Reuse: type-rail-labels, level-ldo-folders. Spawn: skip.

## Setup boxes

- Component / Part / Package / Operator / Version are `input list=datalist`. Pick or type. Apply writes folders.
- Version typing calls `ensure_version` (copies `_manifest` stubs). No `+ Version` button.
- Labels: Kind + Value comboboxes. No separate Or type. `kind:value` in Value still works.

## Level

- `list_tree` skips `_` parts (`_retired_Stub` hidden).
- Tracking SKUs merge into the Part list so Level is not empty before folders exist.
- Rail click jumps to first live Level SKU (RS0204 dual-rail), not Stub.
- `load_family("level")` keeps the Level rail key and loads `ate.tests.logic` (`SUITE_ALIASES`).
- `family_for_component("LevelShifters")` is `level`, not `logic`.

## Checks

`python -m ate.core.check_ui_contract`
`python -m ate.core.check_family_load`
`python -m ate.core.check_operator_tree`
`python -m ate.core.check_new_product`
