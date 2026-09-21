---
keywords: all-parts, usb, keep, dmm, tmo, system-error, reopen-bench, check_all_parts, psu-idle
main_idea: All 26 part yaml TestSpecs are locked by check_all_parts. USB KEEP (PSU+AWG+DMM) ran 3/21 parts then DMM TMO poisoned NI USB. Runner now reopens PSU/AWG/DMM and idles PSU on close. Remaining USB needs unplug/replug.
---

# 2026-09-14 all parts USB KEEP

## Check

`python -m ate.core.check_all_parts` OK: 26 yaml, 22 KEEP parts, MSO-only lm358/rs358/rs8551, stub rs0302.

Locks: no DMM *RST, REQUIRED_AT_OPEN empty, skip MSO 0x0515, no ovp=6.5, reopen_bench + runner `_visa_bus_error` retry, close_session SAFE IDLE.

## USB procedure (KEEP)

Discover skip 0x0515. Open Session not DEMO. Eugene, DUT 1. Tick tests whose `required_instruments` is a subset of PSU/AWG/DMM. Auto-Continue. No Fill Excel. Skip Path C scaffold `input_off_leakage`. Skip MSO (tp/slew/SSSR).

## What ran 2026-09-14 09:45

USB map PSU+AWG+DMM6500. One session.

| Part | KEEP | Result |
|------|------|--------|
| RS0204 | 7 | 7/7 success, open ~0 |
| RS164 | 1 | 1/1 success |
| RS1G07 | 6 | 6/6 success |
| RS1G08 | 9 | 6 ok then vih_vil TMO, voh/vol SYSTEM_ERROR |
| rest | 71 | all SYSTEM_ERROR after poison |

PSU leftover CH1/CH3 ON. Independent `power_off` then OUTP OFF. Later `list_resources` hung -- NI USB wedged.

## Code fix (not yet proven on remaining USB)

- `Instruments.reopen_bench` closes/reopens PSU/AWG/DMM, `power_off`
- runner retries once on any VI_ERROR including TMO
- `close_session` SAFE IDLE before close_all

## Still blocked

OpAmp BUFFER/slew/GBW: MSO 0x0515 skipped. rs0302 enabled_tests empty. Do not claim CIN/CPD STS PASS with no DUT.
