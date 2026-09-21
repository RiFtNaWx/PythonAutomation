---
keywords: extend, modularity, catalog, controls, vcc_sweep, dropdown, owners, extra_families, vccb, a04-gap
main_idea: Platform add-test slot already existed; Logic/Switch VCC knobs were hidden inside the OpAmp gain panel. YAML sweep lists now render as Run conditions dropdowns; extra family keys with underscores map correctly.
---

# 2026-09-08 extend conditions dropdowns

## Progress (PRD-001)

A01-A06 closed-accepted. A07-A12 implemented (R-0003 pending). Dual-stack `main.py` parked. No-code wizard parked.

## How to add things (no runner.py edit)

- Person: `ate/config/owners.yaml`
- Part: `ate/config/parts/<key>.yaml` + `#Test_Database/{Component}/{Part}/...`
- Test: `register(TestSpec)` in family package + `enabled_tests`
- Corners: `vcc_sweep_list` / `vcc_sweep` or explicit `controls:`
- Family: Import family or `extra_families.yaml` `label:`

## Gap closed this turn

Logic/Analog SW hid `#panel-gain-boards` which also held VCC inputs, so A04's "Logic-relevant fields" never showed. Catalog now returns `controls` from part yaml. UI `#panel-run-conditions` is select-if-choices else number. `RunParams.vccb` is operator-overridable. `family_for_component("demo_ingest")` matches underscore keys.

## Checks

`python -m ate.core.check_family_load` -> OK opamp=17 logic=32 switch=4 demo=1
`check_logic_campaign` / `check_open_inventory` / `check_mapped_tests` -> OK
