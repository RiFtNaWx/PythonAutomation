# EPIC-A08 - DMM session + every mapped test runnable

**PRD:** PRD-001
**Status:** implemented (R-0003 pending)
**Sliced:** 2026-09-03 (F15)
**Depends on:** A05 map honesty; A07 photo_layout (reuse, do not reopen)
**Appetite:** 1 wave

## Buyer-visible outcome

First setup: Discover lights MSO/PSU/AWG/DMM tiles. Every `sheet_map.yaml` test appears on Run as a real use case (capture + paste when anchors exist; DMM read when the meter is on the bus). VOL and Logic IDD fail honestly if DMM is missing.

## Acceptance

- Discover classifies DMM; `Instruments.dmm` optional at open.
- No `ate/tests/opa/stubs.py` RuntimeError for mapped sheets.
- `python -m ate.core.check_mapped_tests` green.
- Setup shows map coverage for every sheet_map key.

## Ticket

| ID | File | Status |
|----|------|--------|
| A08-T01 | [A08-T01-mapped-tests-dmm.md](../tickets/A08-T01-mapped-tests-dmm.md) | implemented (R-0003 pending) |

## Out

Full analog PSRR/CMRR/AOL bodies; MOSFET PowerOn fixture; RS1G / Lim; DataLogger replace; A01-A07 reopen.
