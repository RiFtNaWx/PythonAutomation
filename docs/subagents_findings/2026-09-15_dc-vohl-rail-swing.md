---
keywords: junior, vohl, mapped, rs622, rail-swing, dmm, leftover-honest, iso, sssr
main_idea: Mapped OpAmp vohl replaced with BUFFER DMM rail-swing VOH_V/VOL_V. SSSR/LSSR/NPR now stamp MSO numbers. Analog-switch ISO skipped. SIM 221/221. Not junior-100%.
---

# 2026-09-15 DC VOHL rail swing

PREFLIGHT: PARTIAL. Reuse: 2026-09-15_dc-cmrr-poweron.md. Spawn: skip.

## This sitting

1. Path B `ate/tests/opa/vohl.py`: Vs=5.5 dual-rail, AWG DC near +rail then -rail, DMM VOUT. Stamp `VOH_V` / `VOL_V`. No invented min/max. Fixture stays ATE. Mapped screenshot row removed.
2. BUFFER photo tests stamp numbers they already measured: SSSR `OVERSHOOT`, LSSR `LSSR_VPP_V`, NPR `NPR_VPP_V`. No invented min/max.
3. Analog-switch ISO / XTalk / 110 MHz BW not added. SIM CH2 sine is the G11 GBW filter, not an OFF switch.

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

SIM **221/221** parts=25 stub `rs0302`. rs622 KEEP `psrr, cmrr, vohl`. USB DMM on BUFFER is the production VOH/VOL number.

## Leftover-honest (goal still open)

- AOL/EMIRR still mapped captures. Noise = 0.1-10 Hz Vpp not nV/rtHz. ISC missing
- Analog-switch BW 110 MHz / ISO / XTalk; rON min/max PDF image
- RS0302 empty suite. RS74AUP1G07 no PDF VOH/VOL
- Excel unique VOX Vcc rows; RS0204 Icc/VOH empty/grid
- USB START of every SKU
- Path C `input_off_leakage` unfilled
