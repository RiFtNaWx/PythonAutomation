# EPIC-A26 - Named test groups on the Tests page

**PRD:** [PRD-002](../prd/PRD-002-operator-profile-workflow.md)
**Status:** BLOCKED on A25 (same Tests page + catalog schema)
**Do not:** unpark A14 xyflow; rewrite left rail / fonts / UI_CONTRACT chrome

| Field | Value |
|-------|-------|
| Tier | surface |
| Repo | this repo |
| Contract impact | additive `test_catalog.yaml` `groups:` |
| Depends on | EPIC-A25 |
| Blocks | none |
| Appetite | 1 wave |

## Goal

1. Named groups on the Tests page (add, rename, member ids).
2. Reorder groups and members as list up/down (interpret "drag" as list order, not a canvas).
3. Seed labels from existing `fixture_mode` batches (BUFFER / G11 / LOGIC) without a new family rail.
4. Run still honors `enabled_tests`. A group is organization, not a second enable bit.

## Tickets

Epic-agent Mode A after A25. Suggested seams:

| ID | Seam |
|----|------|
| A26-T01 | `groups:` schema + save this Version + check |
| A26-T02 | Tests page add/rename/reorder; no xyflow |

## Parked (not this epic)

- A14 xyflow / drag-drop canvas
- Left-rail rewrite
- No-code wizard
- Cross-family groups

## Checks

```
python -m ate.core.check_add_test
python -m ate.core.check_ui_contract
```

A group must not enable an id that is not in `enabled_tests`. No canvas bundle in `ate/ui/web`.

## Acceptance

See PRD-002 EPIC-A26 acceptance block (buyer seat).
