# EPIC-A24 - This-Version limits overlay

**PRD:** [PRD-002](../prd/PRD-002-operator-profile-workflow.md)
**Status:** BLOCKED on WIP (start after A22 wave; do not reopen A20 leftovers)
**Do not:** scrape en.run-ic.com; write shared `ate/config/limits/` in the default save path; fake PASS without min/max

| Field | Value |
|-------|-------|
| Tier | capability + visible editor |
| Repo | this repo |
| Contract impact | additive (`_manifest/limits.yaml` last-wins) |
| Depends on | A20 shared limits (shipped, leftover-honest rON image is not this epic) |
| Blocks | none |
| Appetite | 1 wave |

## Goal

1. Everyone can set min/max for measurements on **their** Version.
2. Persist campaign `_manifest/limits.yaml`.
3. `load_part_specs` applies overlay last-wins after shared limits yaml + part yaml.
4. STS / enrich / judge on that campaign use the overlay.

## Tickets

Epic-agent Mode A after A22. Suggested seams:

| ID | Seam |
|----|------|
| A24-T01 | overlay load + `check_specs_datalog` overlay case |
| A24-T02 | Setup/Tests/Results editor for this Version only |

## Parked (not this epic)

- Publish overlay to shared `ate/config/limits/` for every operator of the SKU
- A20 RS2323 rON PDF-image extract
- A19 guessed Excel cells
- Website catalog dump into `#Test_Database`

## Checks

```
python -m ate.core.check_specs_datalog
python -m ate.core.check_ui_contract
```

Overlay must win over shared yaml in a temp campaign. Shared file on disk must stay unchanged.

## Acceptance

See PRD-002 EPIC-A24 acceptance block (buyer seat).
