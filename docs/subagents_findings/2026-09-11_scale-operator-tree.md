---
keywords: scale, ensure_product, ensure_version, operator-folder, rs1g08, zip, git-pull, users-table, all-view-only
main_idea: Create folders / Apply / typed Version_N already make that person's tree. Two people on RS1G08 are two folders. Test code still ships zip or ff-only pull. Checks now fail if a second operator clobbers the first or Version clones xlsx.
---

# 2026-09-11 Scale operator tree (tested)

PREFLIGHT: HIT. Reuse: f22-operator-folder, operator-zip-daily-pull, codeless-owner-tags, setup-combo-level. Spawn: smaller-executor (tree / zip / check runner).

## Verdict

Works. No Users table. Path is `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/`.

| Claim | Result |
|-------|--------|
| Create folders = that person's Version_1 | PASS `ensure_product` + `require_write_operator` |
| Apply mkdir missing tree | PASS `set_context` -> `ensure_tree` |
| New Version under that person only | PASS `applyDb` -> `ensure_version`; no `btn-add-version` |
| Two people on RS1G08 = two folders | PASS (was undocumented in checks; now asserted) |
| Test code = zip or git pull | PASS `pack_ate_console --check` ATE_APP_ONLY; `check_sync_repo` dirty skip / ff-only |
| All is view-only | PASS after Apply All-gate fix (`requireWriteOperator` always) |

## Checks run (all exit 0)

```
python -m ate.core.check_operator_tree
python -m ate.core.check_new_product
python -m ate.core.check_sync_repo
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
python pack_ate_console.py --check
```

## Subagent follow-up

- [Test operator trees](8f2e091f-11a8-47fa-a761-89faa4ce46b8): Apply skipped All when `db-operator` was filled. Fixed: `applyDb` always calls `requireWriteOperator()`.
- [Test zip vs git](99934855-ede9-4e8c-b2c6-d7e7c0a85915): folder create never copies `ate/tests/`. `check_sync_repo` now asserts `ATE_APP_ONLY` skip + `pull --ff-only`. Stub `ate/config/parts/*.yaml` on first Create folders is repo config, not DB Python.
- [Run scale checks](65e13155-2657-4500-8de1-ecca0c673e39): six checks exit 0; no Users/Tags path axis in `ate/`.

## Improve this turn

- `check_new_product`: Ariff + ChangThong on RS1G08; All raises; Version_2 under Ariff only; no xlsx clone; no `.py` in campaign tree
- `applyDb` All-gate + `check_ui_contract` fails if `sel.operator || requireWriteOperator` returns
- `check_sync_repo`: ATE_APP_ONLY + ff-only
- README / STATUS: drop stale + Version button wording

## Not proved

Live click on UI 5174 with a real `#Test_Database` (temp tree only). Combo auto-Apply leftover is already forbidden by `check_ui_contract`. Operators get new test Python only when the zip is rebuilt.
