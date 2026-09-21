# EPIC-A16 - Detect / wrap / copy / +Version / +Session

**PRD:** PRD-001 F23
**Status:** implemented (leftover-honest: wrap still copies `imported_<id>.py`)
**Follow-on:** [PRD-003](../prd/PRD-003-snippet-pointer-trigger.md) / [EPIC-A27](EPIC-A27-snippet-pointer-trigger.md). Do **not** reopen A16-T01/T02 as failed.
**Do not reopen:** A01-A15. A13 Excel merge-center and A14 xyflow stay parked.
**A03 stays closed** (Python `register(TestSpec)` slot already exists). Full no-code wizard stays parked.

## Goal

1. AST-scan `ate/tests` + configured golden roots for unmatched `def test_*` (never execute).
2. Wrap clean functions into family `TestSpec` modules; refuse `input()`.
3. Copy/enable registered test ids onto another same-family part yaml + campaign catalog.
4. Setup `+` creates next `Version_N` and a new run-record `sessions/session_*.json`.

## Tickets

| ID | Seam |
|----|------|
| A16-T01 | Scan + wrap/enable/copy API + `check_test_detect` (no UI) |
| A16-T02 | Setup + Version / + Session / detected table (calls T01 RPCs) |

## Parked (not this epic)

- In-browser code editor / Monaco
- Auto-run dirty goldens
- Clone RS0204 dual-rail bodies onto RS1G07
- Real RS1G07 CPD/CIN measurement physics
- No-code wizard
- A13 / A14

## Checks

```
python -m ate.core.check_test_detect
python -m ate.core.check_family_load
```

## Acceptance

See PRD-001 EPIC-A16 acceptance block (buyer seat).
