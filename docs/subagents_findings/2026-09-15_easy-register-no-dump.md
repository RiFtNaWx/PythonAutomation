---
keywords: register, pickup, all-skus, dump, mine, pic, jianhong, provision, first-run, parts
main_idea: All-SKU Add-person dumped empty folders onto everyone. Mine used those folders as ownership. Default is now name + Pick up. provision_operator refuses the dump unless all_skus=True.
---

PREFLIGHT: HIT
reuse: 2026-09-15_person-name-canon.md, 2026-09-15_progress-stalker-pickup.md
spawn: skip

# 2026-09-15 easy register, no dump

Disk audit showed JianHong/Eugene/Ariff/Chun Tak folders on almost every SKU. Cause: `#add-operator-all-skus` default ON + `provision_operator` with no filter.

## Shipped

- `provision_operator` refuses unless `only_parts` / `only_skus` / `all_skus=True`.
- Add person default OFF. This campaign is pre-ticked.
- Settings All SKUs + golden still sends `all_skus: true`.
- First-run: name + Continue. Products optional. Then Results Pick up.
- Mine = yaml `parts:` + tracking PIC. Not empty provision folders.
- `owners.yaml` parts stripped to PIC/user map. JianHong `parts: []`. Folders on disk were not deleted.

## Not

- Did not wipe `ChangThong/` / `JianHong/` trees.
- Did not merge Soo with ChangTong.
