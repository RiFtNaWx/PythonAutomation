keywords: scpi, undefined-header, -116, -113, FREQ, DCYC, OUTP3, generator_setup, sim, check_visa, leftover-honest
main_idea: Live generator_setup set_frequency/query_frequency still sent :SOURn:FREQ (DG822 Pro -116). Helpers now re-APPL; SIM SYST:ERR is -116/-113; checks fail-closed on write/query lines. Goldens keep banned headers by design.

## What failed
`check_walk_order` allowed unused `set_frequency` to keep `:SOUR{ch}:FREQ`. USB DG822 Pro queues Error 116. SIM always returned `0,"No error"`, so DEMO hid the header.

## Live product change (not goldens, not runner.py)
- `generator_setup.py`: `_awg_ch` 1-2 only; `set_frequency` / `set_amplitude` / `set_phase` re-APPL; `query_frequency` / `query_amplitude` parse APPL?; `is_banned_awg_scpi`; `set_duty_cycle` still no-op.
- `ate/instruments/sim.py`: banned AWG write/query -> SYST:ERR -116; DMM *RST/NPLC/AZER/AVER/TRAC/MEAS:CURR/RANG:AUTO -> -113; APPL? returns offset.
- `check_visa` / `check_walk_order` / `check_all_parts`: scan write/query lines (f-strings too). SIM injects FREQ and *RST to prove the error codes.

## Proof
`python -m ate.core.check_walk_order` OK
`python -m ate.core.check_visa` OK (SIM loopback 34/34; USB *IDN PSU+AWG+DMM+MSO)
`python -m ate.core.check_stimulus` OK

## Leftover-honest
- `goldens/**` still write FREQ/DCYC/OUTP3. Do not rewrite. Path C that triggers those functions still -116.
- `set_offset` still `:VOLT:OFFS` (vos / ac_vin 101-pt sweep). Not in the 116 list on this box.
- Worker idle-restart closed the USB session; Open Session again before START.

## Not proven
Live USB START of ioz uA (needs Open Session + Continue). Checks are SIM + source scan, not a DUT measurement.
