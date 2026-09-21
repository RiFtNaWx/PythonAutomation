# EPIC-A23 - Typed-phrase Forget and confirm

**PRD:** [PRD-002](../prd/PRD-002-operator-profile-workflow.md)
**Status:** BLOCKED on A22 (same Setup person panel: `index.html` / `app.js` / `remove_owner`)
**Do not reopen:** A01-A22 until A22 is closed. A13/A14 stay parked.

| Field | Value |
|-------|-------|
| Tier | boundary |
| Repo | this repo |
| Contract impact | additive (`remove_owner` requires `confirm_text`) |
| Depends on | EPIC-A22 |
| Blocks | none |
| Appetite | 1 wave |

## Goal

1. Forget person requires browser confirm AND typed phrase `FORGET {label}`.
2. Phrase is a type-to-confirm pattern, not a password or auth system.
3. Default remains yaml-only. Version folders stay.

## Tickets

Epic-agent Mode A after A22. Suggested seams:

| ID | Seam |
|----|------|
| A23-T01 | `remove_owner` refuses without matching `confirm_text`; All/Kevin still refused |
| A23-T02 | Setup Forget UI prompt + `check_ui_contract` |

## Parked (not this epic)

- Folder delete on Forget (founder decision default PARK). If unparked later: passphrase + type-the-label, this operator only, never other operators' trees.
- Login / Users table
- SKU unassign (A22)

## Checks

```
python -m ate.core.check_operator_tree
python -m ate.core.check_ui_contract
```

`remove_owner` without phrase must leave yaml unchanged (fail the check if it still deletes).

## Acceptance

See PRD-002 EPIC-A23 acceptance block (buyer seat).
