---
keywords: epic-a06, a06-t01, mode-a, labautomation-1, sssr, lssr, npr, buffer, workbook, f12
main_idea: Mode A sliced EPIC-A06 into one READY ticket A06-T01 (LA-1 SSR/LSR/NPR wraps + Test_Database screenshots + paste where sheet_map anchors exist; no hanging input()).
---

# 2026-09-03 EPIC-A06 Mode A slice

PREFLIGHT: PARTIAL. Reused PRD A06/F11, A05-T01 format, labautomation-1-scale finding, stubs.py, sheet_map SSSR/LSSR anchors, lab_report.embed_photo / place_settling_photos.

## Slice

- Epic: `docs/epics/EPIC-A06-la1-buffer-wraps.md` (status open/sliced)
- Ticket: `docs/tickets/A06-T01-la1-buffer-wraps.md` (status ready)
- PRD ledger F12 appended; section 10 -> ticket-runner on A06-T01

## Why 1 ticket

Wrap + screenshot + paste share one run path and the same three BUFFER ids. Splitting paste would race stubs half-replaced. Optional GBW A45 paste is MAY stretch inside T01.

## Acceptance must-haves baked into A06-T01

- stubs no longer RuntimeError for SSSR/LSSR/NPR ids
- run path calls LA-1 recipe (copied/thin wrap; prefer LA-1 over repo-root opa_tests)
- screenshots to Test_Database
- paste if sheet_map photos exist (SSSR/LSSR yes; PhaseReversal/NPR no)
- check_family_load + check_lab_report_sync stay green
- no hanging `input()` (ATE gate or non-blocking capture)

## Out

ATE-native slew/settling/ORT/GBW replacement. PowerOn/Noise/PSRR. Whole LA-1 copy. DataLogger replace. RS1G/Lim/Level. A01-A05 reopen. GitHub Issues.

## Next spawn

ticket-runner on A06-T01 (composer-2.5-fast implement / Grok 4.5 high verify R-0003).
