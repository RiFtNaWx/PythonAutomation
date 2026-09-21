---
keywords: epic-a05, a05-t01, mode-a, lab-report, sheet_map, noise, sync-check, f9
main_idea: Mode A sliced EPIC-A05 into one READY ticket A05-T01 (map fix + Noise stub + fail-path sync check). Paste stretch out.
---

# 2026-09-03 EPIC-A05 Mode A slice

PREFLIGHT: PARTIAL. Reused PRD A05/F8, A04-T01 format, F8 finding, stubs, sheet_map, check_family_load.

## Slice

- Epic: `docs/epics/EPIC-A05-lab-report-sync.md` (status sliced)
- Ticket: `docs/tickets/A05-T01-lab-report-sync.md` (status ready)
- PRD ledger F9 appended; section 10 -> ticket-runner

## Why 1 ticket

Map drift, Noise gap, and sync check are one honesty invariant. Splitting races half-fixed map vs green check.

## Out

Slew/GBW paste (SlewRate has no photo anchors; GBW needs new place_*). Full Noise/PSRR suites. Level/wizard/A01-A04.

## Fail-path requirement

Check must fail if Noise unregistered or `excel_sheet: Slew` instead of `Slew Rate`.

Next: ticket-runner on A05-T01 (composer-2.5-fast implement / Grok 4.5 high verify R-0003).
