---
keywords: rs1gt34, vih_vil, voh_load, vol_load, chuntat, sweep, logic_inputs, buffer
main_idea: RS1GT34 stub listed tp/ten/tdis because new_product copied a generic Logic recipe. Chun Tat wants VIH/VIL then VOH/VOL first. Device is a single buffer (no OE), so ten/tdis do not apply. Enable existing Ariff ids; 5s DMM-delta on VCC sweeps; skip AWG CH2 when logic_inputs=1.
---

# 2026-09-14 RS1GT34 VIH/VIL VOH/VOL first + sweep settle

## Why those tests were missing

`ate/config/parts/rs1gt34.yaml` was a new-product stub: `tp`, `ten`, `tdis`, `supply_current`. Pinout is N.C. / A / GND / Y / VCC -- no OE, so ten/tdis are wrong. VIH/VIL and VOH/VOL already exist as `vih_vil` / `voh_load` / `vol_load` in `ate/tests/logic/ariff_dc.py` (A12). They were never listed on this SKU.

## Shipped

- `enabled_tests` order: vih_vil, voh_load, vol_load, then delta/supply/input leakage sweeps, then tp
- `logic_inputs: 1` so VIH sweep is AWG CH1 only (not AND hold-CH2)
- VOH/VOL tables from datasheet 9.2 (2.0 / 3.3 / 4.5 / 5.0 / 5.5). No G-family 1.65 V
- AWG DC drives inputs high for VOH and 0 for VOL
- VCC sweeps (`delta_supply_current`, `supply_current_sweep`, `input_leakage_sweep`) use the same 5s DMM delta as CIN
- SIM `_dmm_volt` follows AWG DC so VIH/VIL DEMO can trip
- Chuntat `parts:` includes `rs1gt34`

## Not done

- VIH/VIL numeric min/max not in limits yaml: datasheet extract lost the recommended-operating table (9.1). Test still measures `VIH_*` / `VIL_*`. Do not guess TTL 1.5/0.8 until PDF 9.1 is readable.
- `ten`/`tdis` removed from this SKU. Keep `tp`.
- Excel sheet_map cells not probed (no live GT34 xlsx this turn).

## Verify

```
python -m ate.core.check_add_test
python -m ate.core.check_walk_order
python -m ate.core.check_specs_datalog
python -m ate.core.check_sim_run
```

Proof this turn: those four checks PASS, including SIM RS1GT34 `vih_vil` / `voh_load` / `vol_load` / `supply_current_sweep`.

USB START of those ids on Chuntat / RS1GT34 is the operator proof. Ctrl+F5 after worker restart.
