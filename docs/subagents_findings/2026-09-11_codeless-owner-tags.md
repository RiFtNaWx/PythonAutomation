---
keywords: modularity, owners.yaml, upsert_owner, label-scope, rift-fork, codeless, tag-vocab, forget-person
main_idea: Do not push yet. RiFtNaWx person branches are legacy LabAutomation, not the operator console. Codeless person add is Setup Operator + Apply/Save person. Tag scope is this campaign / this class / all products.
---

# 2026-09-11 Codeless owners + label scope

PREFLIGHT: PARTIAL. Reuse: 2026-09-10_central-run-ledger, 2026-09-10_combo-tags-excel, AGENTS add-person. Spawn: skip.

## Push / fork (all RiFtNaWx branches)

- Origin is `jian-hong/Python_Automation_JH`, branch `general/20260604-151742`, **ahead 1** of origin, plus a large dirty tree (kicad, CircuitSim, screenshots, untracked ate config).
- `https://github.com/RiFtNaWx/PythonAutomation` `main` is **behind** this console (no `ate/` worker/UI). Two commits on rift/main we lack are readme/PR merge only.
- Person branches (`ariff-version`, `feat/eugene-lab-version*`, `lim-version`, later `general/20260611*`) are **legacy** `LabAutomation/` + screenshots + sometimes `venv/`. No merge base with the operator console. Do not merge them into `ate/`. Golden bodies stay ingest via Setup Detect/Wrap.
- Ready to push: **no**. Modular console yes; git tree is not a clean `ate/` commit. Do not push until the user asks and we stage only console files.

## What the operator can do without editing Python

1. **Add a person:** type Operator folder -> Apply campaign or Save person. Writes `owners.yaml`. Records `task` = current part. All stays view-only. Forget person = yaml only (folders stay).
2. **Tags:** Kind/Value pick from boards.yaml + campaign + class history + every `_manifest/tags.yaml` ever. Scope combo: this campaign / this class (all OpAmp) / all products. Chip x removes from this campaign only.
3. Customisation is pick-or-type combo + chip x + Save/Forget person. No Optimize button. No Users/Tags folder axis.

## Checks

`python -m ate.core.check_ui_contract`
`python -m ate.core.check_operator_tree`
`python -m ate.core.check_tags_datalog`
`python -m ate.core.check_new_product`
`python -m ate.core.check_family_load`
