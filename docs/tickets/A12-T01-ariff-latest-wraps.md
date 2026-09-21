# A12-T01 - Ariff latest Logic wraps

**Epic:** EPIC-A12
**Status:** closed-accepted
**Step:** current: 4 / 4

## Problem

A09 Ariff DC slots are thinner than Ariff Repo (2026-09-03 16:41). Newer `test_vih_vil` / `test_voh` / `test_vol` and full supply sweep are missing. Operators cannot select those rows.

## Acceptance

WHEN Logic loads, THE SYSTEM SHALL register `supply_current_sweep`, `vih_vil`, `voh_load`, `vol_load` plus thickened `off_current` (8 combos), `ioff_leakage` (pin-force), `input_leakage_sweep` (VCC list), `input_thresholds` (0.05 V + hysteresis).

WHEN part_key is rs1g08 (and rs1g32 / rs1gt32d), THE SYSTEM SHALL enable those ids so console checkboxes can select/deselect.

WHEN part_key is rs29511, THE SYSTEM SHALL NOT expose Ariff-only ids in the catalog.

WHEN `python -m ate.core.check_logic_campaign` and `check_family_load` run, THE SYSTEM SHALL pass; `ariff_dc.py` SHALL NOT call `input(` or import `Ariff`.

## Files

- `ate/tests/logic/ariff_dc.py`
- `ate/config/parts/rs1g08.yaml`, `rs1g32.yaml`, `rs1gt32d.yaml`
- `ate/core/param_defaults.py`, `check_logic_campaign.py`, `check_family_load.py`
- RS1G08 sheet_map; PRD F21; finding

## Out

LDO; Excel A13; xyflow A14; `import Ariff.*`
