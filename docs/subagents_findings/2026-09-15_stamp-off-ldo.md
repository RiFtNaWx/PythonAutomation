---
keywords: junior, stamp-gate, off_current, OFF_uA, ldo, VINMIN_V, LIR_mV, LOR_mV, IOUTMAX_V, IEN_uA, leftover-honest, sim-stamps
main_idea: Path B stamps OFF_uA and LDO VINMIN/LIR/LOR/IOUTMAX/IEN from DMM. SIM LDO CH2 load no longer hits CMOS Schmitt (IOUTMAX was 1 mV). LIR_mV still follows VIN (no LDO model). Stamp dump ate/core/_check_data/sim_stamps.json. Leftover 13 unchanged.
---

# Stamp off_current + LDO (2026-09-15)

Stamp gate failed 15 rows: 5 AND `off_current` (no measurements) and 10 LDO slots (ids empty). Bodies already ran USB SCPI.

## What changed

- `ariff_dc._run_off_current` stamps `OFF_uA` = worst abs DMM IDD_uA across 8 A/B/Y combos at VCC=0.
- `ldo.py` stamps `VINMIN_V` (first VIN where VOUT >= 0.98*nom), `LIR_mV` / `LOR_mV` (abs dVOUT), `IOUTMAX_V` (min VOUT under load), `IEN_uA` (worst EN current).
- Limits rs3213/rs3235: those ids unspec (no fake PDF min/max).
- `check_add_test` greps the stamp ids.
- `check_all_parts` writes `sim_stamps.json`, requires MUST_STAMP ids, bans `AOL_dB` / `SETTLE_us`, rejects IOUTMAX_V < 1 V (Schmitt load trap).
- `sim._dmm_volt`: CH3 EN + CH2 load < 1 V -> follow CH1, not SeeLim Schmitt.

## Leftover-honest (not leftover 13)

- SIM LIR_mV ~1600: DMM follows PSU CH1 VIN (no LDO regulation model). USB DMM is on VOUT.
- SIM IOUTMAX_V follows VIN, not 500 mA dropout.
- Leftover 13 (iso/xtalk/ron/settling 0.1%/noise nV) unchanged.

## Do not

- Fake LDO dropout / 500 mA Iout / datasheet LIR on SIM.
- Drop the stamp gate to get 218/218.
- Reclassify leftover 13.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_specs_datalog
python -m ate.core.check_all_parts
```

File: `ate/core/_check_data/sim_stamps.json` + `physics_enabled.json`.
