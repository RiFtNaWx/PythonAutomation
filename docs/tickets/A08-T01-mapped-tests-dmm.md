# A08-T01 - DMM + every sheet_map test

**Epic:** EPIC-A08
**Status:** closed-accepted (R-0003 leftover-honest: PSRR/CMRR/AOL still mapped captures)
**Step:** current: 6 / 6

## Problem

Discover/session had no DMM, so Logic IDD/VOUT and OpAmp VOL could not run. Remaining mapped workbook sheets were RuntimeError stubs.

## Acceptance

WHEN Discover finds a DMM6500 / 344xx / Keithley DMM, THE SYSTEM SHALL put `DMM` in the mapping and `instr.dmm` on the session (optional at open).

WHEN every `sheet_map.yaml` `excel_sheet` is loaded, THE SYSTEM SHALL have a matching `TestSpec.lab_sheet` that is not registered from `stubs.py`.

WHEN VOL runs without DMM, THE SYSTEM SHALL fail missing instruments. WHEN PSRR/CMRR/AOL/EMIRR/Noise/PowerOn run with MSO+PSU+AWG, THE SYSTEM SHALL capture (and paste if `paste.photos` exists) instead of raising the stub RuntimeError.

WHEN `python -m ate.core.check_mapped_tests` runs, THE SYSTEM SHALL pass classify + map coverage + lab_report_sync.

## Files

- `ate/instruments/discovery.py`, `session.py`, root `instruments.py`
- `ate/tests/opa/mapped_dc.py` (replaces stubs.py)
- `ate/core/check_mapped_tests.py`, `check_lab_report_sync.py`
- Setup DMM tile + map coverage hint
