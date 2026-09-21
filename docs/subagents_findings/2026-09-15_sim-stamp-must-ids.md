---
keywords: must-stamp, sim-stamps, check_all_parts, gbw, pause_cb, leftover-honest, 70mhz
main_idea: MUST_STAMP now fail-closes every unique enabled test_id to a required measurement id. Ban AOL_dB, SETTLE_us, BW>70 MHz. Leftover 13 unchanged. Goal still OPEN.
---

# SIM stamp MUST ids (2026-09-15)

File-level proof after this sitting:

- `ate/core/_check_data/sim_stamps.json` n=218 ok=218
- `ate/core/_check_data/physics_enabled.json` REALIZED=205 LEFTOVER=13
- `python -m ate.core.check_add_test` OK
- `python -m ate.core.check_sim_run` OK
- `python -m ate.core.check_all_parts` OK SIM 218/218

## What changed

`MUST_STAMP` in `ate/core/check_all_parts.py` covers every unique enabled `test_id` (80 ids). Trailing `_` is a prefix (`VIH_` hits `VIH_V` and `VIH_1p8V`). Missing map keys fail before SIM. After SIM, that id must appear.

Banned: `AOL_dB`, `SETTLE_us`, any `*_MHz` / unit MHz stamp `> 70` (MSO5072).

`check_add_test`: `gbw.py` must not call `input()`; must pass `pause_cb=params.pause_hook` to `opa_tests.measure_gbw` (CHAN1=IN+ CHAN2=VOUT G11). `measure_gbw` itself must not call `input()`.

SIM `if sim:` hunt: only `ate/tests/lim/iso.py` leftover-couple AFTER CHAN2 query. xtalk/usb_iso share that helper. wraps.py still has no `logic_tests` import.

No `ate/tests` body, `sim.py`, `runner.py`, or worker edits this sitting. No worker restart. Did not re-run live USB 218 skips.

## Leftover-honest (not leftover 13)

- SIM LIR_mV ~1600: no LDO model; DMM follows VIN.
- LM358 SR_Vus ~5.55 vs typ 0.5: SIM 1-pole slew, not fake 0.5.
- all-GBW GBW_MHz=7.006 SIM 1-pole G11; under 70 MHz; not datasheet GBW.
- SeeLim `input_threshold` stamps `VIH_A_*` as NaN (golden wrap). Id is present. USB DMM threshold is not proven. Not leftover 13.
- rs0204 `tsu`/`th` stamp `TEN_ns`/`TDIS_ns` (workbook names). USB SCPI still runs.

## Leftover 13 (must stay; do not reclassify)

iso/xtalk 1 MHz not 110 MHz; usb_iso/usb_xtalk 1 MHz not 550 MHz; ron/usb_ron/i2c_ron 10 mA; settling SETTLE_VPP_V not 0.1% SETTLE_us; noise Vpp not nV/rtHz.

## Live USB leftover hardware

PSU+AWG only this sitting. DMM+MSO not PnP. `live_usb_stamps.json` n=218 ok=0. That does not complete the SIM goal and does not block SIM work.

## Do not

- Reclassify leftover 13 as REALIZED.
- Fake 110/550 MHz, AOL_dB from BUFFER, CMOS OE->Y on RS29511.
- Copy opa_tests GBW unless CHAN1=AWG trap (not found; keep measure_gbw + pause_cb).
- Hammer NI-VISA / second USB session while worker owns USB.

## Goal

OPEN. Production-ready is not proven until leftover 13 is honest-named (done) AND every enabled SIM row stamps physically correct USB-path values (SeeLim NaN + LIR/SR/GBW leftover-honest still sit on that bar) AND live USB DMM+MSO exists.
