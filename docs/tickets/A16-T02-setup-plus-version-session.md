# A16-T02 - Setup +Version / +Session / detected table

**Epic:** EPIC-A16
**Status:** implemented
**Model (implement):** composer-2.5
**Depends on:** A16-T01 RPCs

## Goal

Setup UI: `+` beside Version, `+` beside Session (New run record), Detected tests panel (wrap/enable + copy-from-part). Calls T01 RPCs only. No code textarea.

## Acceptance

WHEN the operator clicks + Version, THE SYSTEM SHALL create the next `Version_N` under the current operator folder and refresh the Version dropdown.

WHEN the operator clicks + Session (New run record), THE SYSTEM SHALL write a new `sessions/session_*.json` via `begin_session` without requiring START or VISA Open Session.

WHEN Setup shows Detected tests, THE SYSTEM SHALL list unmatched / blocked rows from `list_detected_tests` and allow Wrap into family + Enable on current part for clean rows only.

WHEN the operator copies tests from another same-family part, THE SYSTEM SHALL call `enable_tests_on_part` and refresh the Run list.

## Out of ticket

- Scanner / wrap implementation (A16-T01)
- Monaco / raw code edit; reopen A01-A15
