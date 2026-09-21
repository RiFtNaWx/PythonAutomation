---
keywords: first-run, observer, kevin, people.yaml, progress-board, heartbeat, github-issue
main_idea: First-run pick/add name then product. Names sync via #Test_Database/_ate/people.yaml. Kevin is observer (no START). Results board is open to everyone. gh issue create is clone-only.
---

# 2026-09-11 First-run people + open progress board

PREFLIGHT: HIT. Reuse: codeless-owner-tags, operator-zip-daily-pull, central-run-ledger. Spawn: skip.

## Behavior

- Empty `ate_operator` -> modal Who are you + What product.
- New names: `upsert_owner` writes git owners.yaml + cloud `_ate/people.yaml`.
- Kevin / All / `role: observer` cannot START / ensure_product.
- Results Lab progress: run counts, last-seen heartbeat, comments/questions in `_ate/board.yaml`.
- Open GitHub issue uses `gh` on clone PCs only.

## Proof

```
python -m ate.core.check_progress
python -m ate.core.check_operator_tree
python -m ate.core.check_ui_contract
```
