# EPIC-A25 - Same-family suggest and enable existing tests

**PRD:** [PRD-002](../prd/PRD-002-operator-profile-workflow.md)
**Status:** BLOCKED on A22 WIP, must not overlap A26, and **must not fly with A27** (shared `test_detect.py` + Tests page). Wrap-copy leftover is PRD-003; suggest-enable only in this epic.
**Do not reopen:** A16 copy-from-part UI (`btn-copy-tests` stays absent). A03 stays closed. No-code wizard stays parked.

| Field | Value |
|-------|-------|
| Tier | capability + Tests page surface |
| Repo | this repo |
| Contract impact | additive suggest payload; catalog enable only |
| Depends on | A16 Path A/C; A22 SKU list helpful |
| Blocks | EPIC-A26 |
| Appetite | 1 wave |

## Goal

1. Suggest tests classified product family -> part number -> executable registry ids.
2. If ids already exist, enable them on **this** operator Version (`test_catalog.yaml`).
3. Learn from **this** operator's other Versions (version-gaps already). Other operator folders stay skipped (not merged).
4. Same family only. Cross-family refuse. Do not implement wrap-copy here. After A27, wrap is pointer+trigger; this epic only suggest-enables existing registry ids.

## Tickets

Epic-agent Mode A after A22. Suggested seams:

| ID | Seam |
|----|------|
| A25-T01 | suggest payload family -> part -> ids; enable writes this catalog; cross-family refuse |
| A25-T02 | Tests page suggest list; `check_ui_contract` still forbids `btn-copy-tests` |

## Parked (not this epic)

- Wholesale copy of another part's `enabled_tests` (RS0204 dual-rail onto RS1G07)
- Copy another person's Python or catalog files
- Wrap into another family
- No-code wizard / Monaco
- A14 xyflow
- Named groups (A26)

## Checks

```
python -m ate.core.check_test_detect
python -m ate.core.check_add_test
python -m ate.core.check_ui_contract
```

`copy_between_people` stays false. `btn-copy-tests` must stay absent. Enable cin on Jane catalog must not rewrite Ariff's `test_catalog.yaml`.

## Acceptance

See PRD-002 EPIC-A25 acceptance block (buyer seat).
