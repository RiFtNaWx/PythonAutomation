keywords: ariff-dc, scale, logic, vih_vil, voh_load, vol_load, open-drain, gt-family, datasheet
main_idea: Enable existing Ariff VIH/VIL/VOH/VOL TestSpecs on Logic gate/buffer SKUs from datasheets. Skip Soo/RS0204/DFF/shift/mono. Do not rewrite Eugene cin/cpd or wrap bodies.

## What scaled

Push-pull G/GT (DC first: vih_vil, voh_load, vol_load):

- rs1g08, rs1g14, rs1g32, rs1g125, rs1g126, rs1g97
- rs1gt08, rs1gt32, rs1gt32d, rs1gt34 (already)

Open-drain:

- rs1g07: vih_vil + vol_load first. No voh_load. Keep cin/cpd/supply_current.
- rs74aup1g07: vih_vil only at 1.8/2.5/3.3. PDF unfound -- no G-family 5.5 V VOH/VOL.

## Datasheet notes (local extracts, not web scrape)

- G-family (1G07/14/08/32/125/126/97): VCC 1.65-5.5. VOH/VOL tables copied from rs1g08 9.2.
- 1G07: "Open-Drain Output" -- no VOH.
- 1G14: Schmitt inverter, no OE -- dropped ten/tdis.
- 1G125: 3-state, /OE active-low. Checklist: tie /OE low for DC. Keep ten/tdis wraps.
- 1G126: 3-state, OE active-high. Checklist: tie OE high.
- 1G97: 3-input configurable. Ariff body is 2 AWG channels -- tie unused pin. No new 3-input body.
- GT (1GT08/32/32D/34): VCC 2.0-5.5. Stripped illegal 1.65 VOH/VOL corners.

## Left alone (fully ATE / wrong class)

- rs29511 Soo wraps
- rs0204 dual-rail vih/voh/icc
- rs1g74 DFF, rs164 shift, rs1g123 monostable
- eugene_cap cin/cpd bodies
- wraps.py tp/tidle/tdis/ten/supply_current bodies
- Excel cells -- not guessed. Path A catalog still wins per Version.

## Checks (venv)

- python -m ate.core.check_add_test (scale assert)
- python -m ate.core.check_family_load
- python -m ate.core.check_specs_datalog
- python -m ate.core.check_open_inventory
- python -m ate.core.check_logic_campaign
- python -m ate.core.check_sim_run

Worker: parts/limits yaml only -- RPC re-reads. Ctrl+F5. Proof: DEMO vih_vil on RS1G14 (USB).
