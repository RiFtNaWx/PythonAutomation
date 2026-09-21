---
keywords: check_all_parts, logic, scale, sim, rs1gt34, vih_vil, psu_mso, leftover-honest
main_idea: python -m ate.core.check_all_parts logic SIM 156/156 on 18 SKUs. REALIZED=155 LEFTOVER=1 (rs0302 i2c_ron 10 mA). GT VIH SIM trip is not VCC/2.
---

# 2026-09-18 Logic scale check_all_parts

PREFLIGHT: HIT. Reuse junior-production-scale, physics-scale-proof, rs1gt34-vih-vil-live. Spawn: skip.

## Command

```
python -m ate.core.check_all_parts logic
```

No-args still runs every family. Filtered proof writes `physics_enabled_logic.json` + `sim_stamps_logic.json` (does not clobber the all-family files).

Logic argv includes Level translators (RS0204 ate_suite=logic, RS0302). Filter fail-closes if rs622 leaks in or rs1g08/rs0204 drop out.

## Result

OK `family=logic` yaml=18 keep_parts=18 mso_parts=15 stub=[] SIM **156/156** physics REALIZED=155 LEFTOVER=1. ~38 s.

## What broke, then fixed

RS1GT34 `vih_vil` (`vih_vil_stimulus: psu_mso`) SPEC FAIL: SIM MSO CHAN1 Y tripped at VCC/2 (3.3 V -> VIH 1.65 vs max 1.5; 5.5 V -> 2.75 vs max 2.0). AWG+DMM GT SKUs passed because they have no `VIH_*` limits rows.

Fix: `ate/instruments/sim.py` `_psu_ch2_logic_y` trip `min(0.4*VCC, 1.4)`. Loopback `gt_mso_vin_1p20_y_low` / `gt_mso_vin_1p45_y_high` at VCC=3.3. USB live 2026-09-17 is unchanged (real MSO).

## Leftover-honest

- `rs0302 i2c_ron`: 10 mA platform vs datasheet 64 mA (must stay LEFTOVER).
- SIM GT trip is not silicon VT. Do not quote SIM VIH as datasheet.
- USB START of all 18 SKUs is not this check.
- RS164/RS1G74/RS1G123 catalogs stay short (no full shift/DFF/mono recipes).

## Not

runner.py, database.py, leftover-13 fake-close, worker restart (SIM only).
