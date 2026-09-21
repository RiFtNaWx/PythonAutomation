---
keywords: rs1g126, ioz, recipe, awg, pnp-unknown, catalog, gt34-mix, leftover-honest
main_idea: AWG missing because Windows USBTMC Status=Unknown on DG8Q281600755 (Discover skips ghosts). IOZ was already in JianHong Version_1 catalog; the Logic DC "Enabled tests" line was allTests (often a leftover RS1GT34 DC list). Recipe panel is product_model YAML, not the xyflow Recipe tab.
---

PREFLIGHT: PARTIAL. Reuse 2026-09-21_rs1g126-ioz-usb-awg.md + a14-recipe-canvas.

## Causes

1. AWG not in `Session open (...): PSU, DMM, MSO` -- PnP `Unknown` for `USB\VID_1AB1&PID_0646\DG8Q281600755`. visa_known.yaml has that serial. Discover will not *IDN Unknown rows (NI viOpen hang). PSU/DMM/MSO were Status=OK.
2. IOZ missing on the recipe line -- `renderLogicDc` printed `allTests` (Run list), not `parts/rs1g126.yaml` `enabled_tests`. A leftover RS1GT34 list is exactly `delta_icc, icc, ii, input_threshold, voh, vol` (oe none, no ioz). JianHong `test_catalog.yaml` already had `ioz`.
3. Recipe "weird" -- `#panel-logic-dc` dumps product_model JSON (truth/isolation/pass_mode/card_fields). That is not A14 `#page-recipe` xyflow. Pin table was empty because `panel_payload` never sent `pin_port_map` / `icc_corner_rows` / `has_oe`.
4. VOH card said "RS0204 AWG DC + DMM" -- `stimulus.py` hardcoded that for id `voh`/`vol` for every SKU.

## Fixes (this sitting)

- Session hint: `not on bus: AWG (Windows USBTMC Unknown -- ...)`
- Logic DC enabled line: SKU `part_yaml` vs this Version catalog; mismatch if dropdown != worker campaign
- `panel_payload`: `enabled_tests`, `has_oe`, `icc_corner_rows`, `pin_port_map`
- Path B voh/vol/ioz stimulus text (not RS0204) when part is not rs0204
- Path A available ids for rs1g126 include voh/vol/ten/tdis

## Do not (busy run)

Worker `busy: true` session_2026-09-21_144509. No restart. START ioz already FAIL-closed Missing AWG (see sibling finding).

## Leftover-honest

- Live IOZ uA still needs DG822 PnP OK then Discover + Open Session.
- Catalog still has wrap ids (`voh_load`, `ioff_leakage`) plus Path B `ioz`. Path A Save of part yaml would show `voh`/`vol`/`icc` instead of wrap names.
- VOH_2p0V specs on the paste were RS1GT34 overlay, not rs1g126 voh_table (1.65/2.3/3.0/4.5/5.5).
---
