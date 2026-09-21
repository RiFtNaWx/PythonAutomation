# EPIC-A22 - Assign product codes and create this person's folders

**PRD:** [PRD-002](../prd/PRD-002-operator-profile-workflow.md)
**Status:** implemented (T01+T02 2026-09-14). Next: A23 typed-phrase Forget.
**Do not reopen:** A01-A21. A13 Excel MCP and A14 xyflow stay parked.
**Do not:** Users table; move/copy another operator's workbook/sessions; change `DbContext.root()` path shape.

| Field | Value |
|-------|-------|
| Tier | foundation + visible Setup surface |
| Repo | this repo |
| Contract impact | additive |
| Depends on | A15 operator path (shipped) |
| Blocks | A23 (same Setup person panel -- not in flight together) |
| Appetite | 1 wave |

## Goal

1. New person workflow: type label, select existing product codes, save.
2. Upsert `ate/config/owners.yaml` `parts:` for those SKUs.
3. `ensure_product` Version_1 for **this** operator on each matched SKU.
4. Unassign a SKU later: drop `parts:` entry; folders stay.

## Tickets

Mode A filed 2026-09-14 (local files only; no GitHub Issues):

| ID | Ticket file | Status | Seam |
|----|-------------|--------|------|
| A22-T01 | [A22-T01-assign-ensure-unmatched.md](../tickets/A22-T01-assign-ensure-unmatched.md) | implemented | assign + ensure loop + unmatched + unassign core/RPC + checks |
| A22-T02 | [A22-T02-setup-product-code-picker.md](../tickets/A22-T02-setup-product-code-picker.md) | implemented | Setup product-code picker + unassign + Ctrl+F5 / UI_CONTRACT |

Implement order: **T01 then T02**.

## Parked (not this epic)

- Typed-phrase Forget (A23)
- Folder delete
- Limits overlay (A24)
- Suggest-import (A25)
- Named groups (A26)
- Login / Users table
- A13 / A14 / no-code wizard

## Checks

```
python -m ate.core.check_operator_tree
python -m ate.core.check_new_product
python -m ate.core.check_ui_contract
```

Add one check that Jane + RS1G08 does not clobber Ariff's sibling tree (extend `check_new_product` or a small `check_assign_owner` -- epic-agent picks; one runnable check, not a framework).

## Acceptance

See PRD-002 EPIC-A22 acceptance block (buyer seat).

Literal: "migrate related products to him" = upsert `parts:` + `ensure_product` for this operator. Not a MOVE of Ariff/ChangThong/Eugene data.
