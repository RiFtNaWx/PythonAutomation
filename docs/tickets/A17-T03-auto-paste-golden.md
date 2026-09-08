# A17-T03 - Auto-paste + golden workbook check

**Epic:** EPIC-A17
**Status:** implemented
**Model (implement):** composer-2.5
**Depends on:** A17-T01 session hooks

## Goal

At session end (and after successful steps with screenshots), paste latest graphs/screenshots into campaign xlsx via existing `paste.photos`. Parameterize golden apply to campaign path. Fail-closed `check_golden_workbook`.

## Acceptance

WHEN a session ends and a test has real (non FILL_ME) `paste.photos`, THE SYSTEM SHALL paste the latest DUT/channel image into the campaign workbook via `place_mapped_photos`.

WHEN `python -m ate.reporting.check_golden_workbook` runs against a campaign workbook, THE SYSTEM SHALL fail on missing golden font / missing image at anchored cell when a screenshot exists; `apply_golden_workbook` then re-check is the fix path.

## Out of ticket

- A13 OneDrive / Excel MCP
- Inventing FILL_ME cells
