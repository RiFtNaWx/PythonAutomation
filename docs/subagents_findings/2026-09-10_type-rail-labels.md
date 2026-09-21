---
keywords: type-rail, power, ldo, analog-switch, labels, board_type, inventory-filter, tags.yaml
main_idea: Left rail is product type (OpAmp/Logic/Analog SW/Level/Power). Power is a live LDO suite. Analog SW tests follow the selected part yaml. Setup Add labels is kind+value chips in tags.yaml/TAGS.txt/session json, reusable per family, no Tags folder.
---

# 2026-09-10 Type rail + Setup labels

PREFLIGHT: PARTIAL. Reuse: ldo-level-translator-split, product-class-operator, a17-tags. Spawn: skip.

## Type rail

- Rail: OpAmp, Logic, Analog SW, Level, Power.
- Tracking-sheet picker filters by `category` (level / power / analog_switch / ...).
- RS0204 stays `category: level` + `ate_suite: logic`.
- Power `run_ic.yaml` `live: true`, `family: power`. Not OpAmp.

## LDO / Analog SW

- `ate/tests/power/ldo.py` -- IQ, VINMIN, LIR, LOR, IOUTMAX, IEN. `power_on_protected`, Continue, no Ariff import.
- RS3213 / RS3235 part yaml; each SKU is its own campaign.
- Analog switch `_part_cfg` uses campaign `part_key` (RS2227 yaml, not hardcoded rs2323).

## Labels

- Setup Test Database, after Year: Add labels (kind + value, or type `kind:value`).
- Kinds: `board`, `board_type` in `boards.yaml`; more kinds from saved campaign labels.
- Store: `_manifest/tags.yaml` + `TAGS.txt` only. Session `report.json` identity includes `tags` / `labels`.
- Vocab per family. `list_boards(power)` does not fall back to G11.
- Reuse across campaigns of the same component via scanning `_manifest/tags.yaml`.

## Checks

`python -m ate.core.check_new_product`
`python -m ate.core.check_family_load`
`python -m ate.core.check_tags_datalog`
`python -m ate.core.check_ui_contract`
