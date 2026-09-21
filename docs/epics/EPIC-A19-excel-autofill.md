# EPIC-A19 - Standard Excel + numeric auto-fill

**PRD:** PRD-001 (follow-on to F25)
**Status:** implemented (T01+T02 2026-09-11)
**Depends on:** A18 living `report.json` merge
**Do not:** unpark A13; apply OpAmp golden to Logic; invent a second Excel writer

## Goal

Write measurement numbers from living `sessions/report.json` into campaign workbook cells via `sheet_map` `paste.values` (photos already use `paste.photos`).

## Tickets

| ID | Seam |
|----|------|
| A19-T01 | `ate/reporting/session_values.py` + `check_session_values` |
| A19-T02 | `end_session` hook + AGENTS row + one RS622 values map |

## Acceptance

See `docs/SHIP_NEXT.md` section 3.

## Out of epic

A20 limits/PDF polish; A21 UX; A13/A14.
