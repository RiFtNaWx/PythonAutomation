# A09 Logic campaign platform (Ariff / Soo)

keywords: a09-t01, epic-a09, logic, rs29511, rs1g08, ariff, soo, enabled_tests, sheet_map, paas, f16
main_idea: One Logic rail; Soo RS29511 vs Ariff RS1G08 differ by campaign/part YAML (enabled_tests, timing, fixture LOGIC). Family-aware map coverage. Lim stays next wave.

## Shipped

- Campaigns: `#Test_Database/Logic/RS29511/SOIC/Version_1` and `Logic/RS1G08/SOT23/Version_1`
- Part yaml: `ate/config/parts/rs29511.yaml`, `rs1g08.yaml`
- Ariff DC TestSpecs: `ate/tests/logic/ariff_dc.py` (no `import Ariff.*`)
- Enable filter on `list_tests`; `logic_catalog_for_ui`; `check_logic_campaign`
- Worker 0.2.7; set_context prefers part-yaml model when switching parts

## Verify

```
python -m ate.core.check_family_load
python -m ate.core.check_logic_campaign
```

Browser 2026-09-03: Logic RS29511 -> 7 Soo tests, map 7. RS1G08 -> 8 Ariff tests (DeltaIDD etc), no CapLoad. OpAmp restore keeps GBW.

## Out

Lim RS2323; LA-1 copy into ate/; RS1G07 cpd/cin; DataLogger replace; implementer self-close R-0003.
