keywords: a12, ariff, logic, rs1g08, vih_vil, voh_load, vol_load, supply_current_sweep, enabled_tests, f21
main_idea: A12 wraps Ariff Repo 16:41 Logic into native ate/tests/logic/ariff_dc.py. Operator selects/deselects via existing checkboxes. Soo catalog stays clean. No import Ariff.*.

# 2026-09-04 A12 Ariff latest Logic wraps

## Shipped

- Thickened DC: `off_current` 8 combos, `ioff_leakage` pin-force, `input_leakage_sweep` VCC list, `input_thresholds` 0.05 V + hysteresis
- New ids: `supply_current_sweep`, `vih_vil`, `voh_load`, `vol_load` (not `voh`/`vol` -- RS0204 owns those registry ids)
- Part yaml + campaign `test_catalog` / `sheet_map` for RS1G08; rs1g32 / rs1gt32d enabled lists expanded
- Workbook sheets Supply_Current, VIH_VIL, VOH, VOL added
- Checks: `check_family_load` logic=32; `check_logic_campaign` A12 ids; Soo isolation
- Worker **0.2.13**
- PRD F21, EPIC-A12, A12-T01

## Gap table (Ariff Repo vs ATE)

| Ariff function | ATE id | Notes |
|----------------|--------|-------|
| test_tp/tidle/tdis | tp/tidle/tdis | Soo wraps (unchanged) |
| test_delta_supply_current | delta_supply_current | near-threshold combos |
| test_off_current | off_current | 8 combos |
| test_input_thresholds | input_thresholds | 0.05 V + hysteresis |
| test_ioff_leakage | ioff_leakage | pin-force |
| test_input_leakage_sweep | input_leakage_sweep | YAML VCC list |
| test_supply_current | supply_current_sweep | distinct from Soo supply_current |
| test_vih_vil | vih_vil | AWG path (not full 3-PSU Ariff) |
| test_voh / test_vol | voh_load / vol_load | YAML tables |
| LDO_* | -- | parked (not on RS1G) |
| #def stubs | -- | not wrapped |

## Verify

```
python -m ate.core.check_family_load
python -m ate.core.check_logic_campaign
```

## Out / later

Excel merge-center A13; xyflow A14; LDO campaign; full 0..5.6/0.1 via expanding `vcc_sweep_list` in YAML.
