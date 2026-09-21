# A16-T01 - Detect / wrap / enable / copy API

**Epic:** EPIC-A16
**Status:** implemented
**Model (implement):** composer-2.5

## Goal

AST-scan golden roots + `ate/tests` for unmatched `def test_*`. Wrap clean ones into family `TestSpec` modules. Enable/copy ids onto same-family part yaml. One runnable check. No UI.

## Acceptance

WHEN `list_detected_tests` runs, THE SYSTEM SHALL return unmatched `def test_*` from `ate/tests` and any existing configured golden root without executing those files.

WHEN a function body contains `input(`, THE SYSTEM SHALL mark it blocked and `wrap_detected_test` SHALL refuse.

WHEN `wrap_detected_test` succeeds for a clean function, THE SYSTEM SHALL write `ate/tests/<family>/imported_<id>.py` with `register(TestSpec)` and reload the family without editing `runner.py`.

WHEN `enable_tests_on_part` copies ids from part A to part B, THE SYSTEM SHALL append to B's `enabled_tests` only if both parts are the same family and the ids exist in that family's registry; otherwise refuse.

WHEN `python -m ate.core.check_test_detect` runs, THE SYSTEM SHALL pass (clean fixture wrapable; dirty `input(` blocked; missing golden root skipped; cross-family copy refused).

## Out of ticket

- Setup UI (+ Version / detected table) -> A16-T02
- In-browser editor; RS1G07 CPD/CIN physics; reopen A01-A15
