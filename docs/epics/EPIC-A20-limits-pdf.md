# EPIC-A20 - Limits everywhere + sheet-quality P/F PDF

**PRD:** PRD-001 (follow-on to F25)
**Status:** in progress (local lookup + inventory limits 2026-09-11; PDF table extract still thin)
**Depends on:** A19 preferred for Excel path; A18 merge required; `ate/core/specs.py` exists
**Do not:** scrape en.run-ic.com catalog; use root `limits.py` for console; fake PASS without min/max

## Goal

1. `ate/config/limits/<part>.yaml` for parts we actually test (beyond RS622).
2. Every stamped measurement has min/max/typ/result when limits exist.
3. STS `datalog.md|.html|.pdf` honest Parameter / Unit / Min / Max / Typ / Value / Result from living report.

## Tickets

| ID | Seam |
|----|------|
| A20-T01 | limits yaml for active inventory parts |
| A20-T02 | measurement stamp honesty + check |
| A20-T03 | STS export polish |

## Acceptance

See `docs/SHIP_NEXT.md` section 4.

## Out of epic

A19 Excel fill; full Noise/PSRR physics; Comparator suite; A13/A14.
