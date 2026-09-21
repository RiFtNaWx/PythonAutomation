# A08 DMM + every mapped test

keywords: a08-t01, epic-a08, dmm, mapped_dc, check_mapped_tests, stubs, vohl, sheet_map, f15
main_idea: Discover/session classify DMM (optional at open). Every sheet_map excel_sheet has a non-stub TestSpec. VOL needs DMM+PSU at run. Setup shows map coverage. Do not treat mapped_dc as full analog PSRR/CMRR/AOL recipes.

## What shipped

- `ate/instruments/discovery.py` `classify_idn()` -> MSO / PSU / AWG / DMM.
- `Instruments.dmm` optional at `open_session`; VOL / Logic IDD still fail missing DMM at run.
- Root `instruments.py` re-exports ate discovery+session (no second map).
- Deleted `ate/tests/opa/stubs.py`. Remaining map rows live in `ate/tests/opa/mapped_dc.py`.
- Coverage: `python -m ate.core.check_mapped_tests`. Worker RPC `mapped_coverage`. Setup `#setup-map-hint`.
- Console parse trap: do not merge `btn-shot` into `btn-open` (unclosed try kills entire `app.js`).

## Mapped ids (platform use cases, not full lab analog)

power_on_time, emirr, psrr, cmrr, aol, vohl (DMM), noise. Existing BUFFER/GBW/ORT/VOS stay as they were.

## Verify (8.3 cwd)

```
venv\Scripts\python.exe -m ate.core.check_mapped_tests
```

Browser 2026-09-03: Setup `Map coverage OK: 15 sheet_map tests registered`. Run lists Power On / PSRR / CMRR / AOL / VOHL (DMM+PSU) / EMIRR / Noise. DMM tile present; Discover had no DMM this session.

## Out

Full analog PSRR/CMRR/AOL; MOSFET PowerOn; RS1G/Lim; DataLogger replace; A01-A07 reopen; implementer self-close of R-0003.
