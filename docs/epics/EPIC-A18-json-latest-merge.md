# EPIC-A18 - Living JSON merge + per-test records

**PRD:** PRD-001 F25
**Status:** implemented (2026-09-11)
**Do not reopen:** A01-A17. A13 Excel MCP and A14 xyflow stay parked.
**Next:** A19 standard Excel auto-fill; A20 PDF limit pass/fail.

## Goal

1. `sessions/report.json` is living latest per operator Version -- merge by test_id+dut(+channel); keep tests not run this START.
2. Timestamped history under `{test_key}/DUT_n/records/` (append-only).
3. Full START snapshots stay `sessions/session_{id}.json` + archive on end.
4. Boss-facing `STATUS.md` Done / Ongoing / Not complete.

## Acceptance

WHEN START A records ort and START B records only gbw on the same operator Version, THE SYSTEM SHALL keep ort in `sessions/report.json` with the original timestamp and SHALL add gbw with a new timestamp. WHEN either step is recorded, THE SYSTEM SHALL write `{test_key}/DUT_n/records/{test_id}_{timestamp}.json`. WHEN `python -m ate.core.check_tags_datalog` runs, THE SYSTEM SHALL pass.

## Out of epic

- Standard Excel template + numeric fill (A19)
- PDF datasheet limit pass/fail (A20)
- A13 OneDrive / Excel MCP; A14 xyflow
