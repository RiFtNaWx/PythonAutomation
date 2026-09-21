---
keywords: junior, ort, delay, rs622, leftover-honest, mapped, aol
main_idea: ORT now stamps ORT_POS_us / ORT_NEG_us from MSO delay before photos. Extract 0.5 s is garbled so no invented min/max. SIM 221/221. Not junior-100%.
---

# 2026-09-15 ORT MSO delay stamp

PREFLIGHT: PARTIAL. Reuse: 2026-09-15_dc-vohl-rail-swing.md. Spawn: skip.

## This sitting

1. `ate/tests/opa/ort.py` measures RRDelay (POS) and FFDelay (NEG) on the locked G_NEG100 squares, then captures JPEGs. Stamps `ORT_POS_us` / `ORT_NEG_us`. Writes us into the existing ORT grid helper when the sheet exists.
2. Did not take extract "Overload Recovery Time ... 0.5 s" as a limit (garbled; settling 0.1% is the same token).
3. AOL/EMIRR still mapped. Analog-switch ISO still skipped (SIM CH2 sine is G11 GBW). RS0302 still empty.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_stimulus
python -m ate.core.check_specs_datalog
python -m ate.core.check_mapped_tests
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **221/221** parts=25 stub `rs0302`. USB MSO on G_NEG100 is the production ORT number.

## Leftover-honest (goal still open)

- AOL/EMIRR still mapped captures. Noise = 0.1-10 Hz Vpp not nV/rtHz. ISC missing
- Settling still photo/cursor (no SETTLE_us stamp)
- Analog-switch BW 110 MHz / ISO / XTalk; rON min/max PDF image
- RS0302 empty suite. RS74AUP1G07 no PDF VOH/VOL
- Excel unique VOX Vcc rows; RS0204 Icc/VOH empty/grid; SIM RS0204 VIH/VOH CMOS vs dual-rail
- USB START of every SKU
- Path C `input_off_leakage` unfilled
