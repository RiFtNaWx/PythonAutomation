# A09-T01 - Logic campaign YAML + Ariff DC slots

**Epic:** EPIC-A09
**Status:** closed-accepted
**Step:** current: 6 / 6

## Problem

Logic wraps exist but `#Test_Database` has no Logic campaign, only `rs622` part yaml, map coverage is OpAmp-hardcoded, and `list_fixture_modes` returns empty for Logic. Ariff vs Soo cannot edit different specs without forking Python.

## Acceptance

WHEN a Logic campaign is Applied, THE SYSTEM SHALL point DbContext at `#Test_Database/Logic/<Part>/...` with sheet_map coverage against Logic `lab_sheet`s.

WHEN part_key is `rs29511`, THE SYSTEM SHALL list only Soo-enabled tests. WHEN part_key is `rs1g08`, THE SYSTEM SHALL list Ariff timing + DC ids (delta_supply_current, off_current, input_thresholds, ioff_leakage, input_leakage_sweep).

WHEN Logic family is active, THE SYSTEM SHALL expose fixture mode LOGIC from part yaml (no OPA G11).

WHEN `python -m ate.core.check_logic_campaign` runs, THE SYSTEM SHALL pass RS29511 map coverage + family_load Logic probe.

## Files

- `ate/config/parts/rs29511.yaml`, `rs1g08.yaml`
- `#Test_Database/Logic/RS29511/...`, `Logic/RS1G08/...`
- `ate/tests/logic/ariff_dc.py`, wraps/param_defaults/worker/checks
- PRD F16, EPIC-A09, ATE_PLUGIN
