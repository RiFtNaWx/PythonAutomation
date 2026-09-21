---
keywords: junior, cmos, tp, tidle, and, or, strap-b, cmos_prop, leftover-honest, physics_scale
main_idea: Combinational CMOS tp/tidle is Path B in ate/tests/logic/cmos_prop.py (AND B=VCC, OR B=GND, no AWG CH2 reverse). Not the Soo/Ariff level-shifter wrap. Proven SIM 218/218, physics 199/19 before RS29511 DC.
---

# CMOS combinational tPD Path B

## Why wrap was wrong

`logic_tests.test_tp` is a copied bidirectional level-shifter recipe (IN->OUT then AWG CH2 reverse Y->A). CMOS AND/OR use CH2 as the other input. DFF/shift/monostable already ban combinational `tp`.

## Body

- File: `ate/tests/logic/cmos_prop.py` -- `run_tp` / `run_tidle` only. Does not `register(TestSpec)`.
- `wraps.py` routes non-rs29511 `tp`/`tidle` here; rs29511 stays `rs29511_prop`.
- AND `{rs1g08, rs1gt08}`: `setup_dc(gen, 2, vcc)` `strap_b=VCC`.
- OR `{rs1g32, rs1gt32, rs1gt32d}`: `setup_dc(gen, 2, 0)` `strap_b=GND`.
- OD `{rs1g07, rs74aup1g07}`: Continue 10k pull-up Y.
- OE-low `{rs1g125}`: jumper `/OE` to GND.
- Inverter `{rs1g14}`: Y is not A; still FFDelay/RRDelay.
- Else buffer: Y follows A. No reverse.
- Eugene IDD wrap expanded: rs1g07, rs74aup1g07, rs1g14, rs1g125, rs164, rs1g74, rs1g123. Not rs29511.

## Proof (this sitting, before RS29511 DC)

```
python -m ate.core.physics_scale
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_specs_datalog
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

OK: rows=218 REALIZED=199 LEFTOVER=19. `check_sim_run` asserts rs1g08 `strap_b=VCC` and rs1g32 `strap_b=GND`, not `hotswap_prop`. logic=45 tests (cmos_prop does not register).

## Leftover-honest (do not reclassify)

iso/xtalk/usb_iso/usb_xtalk (MSO 70 MHz), ron 10 mA vs PDF, settling photo, noise Vpp, vos_sweep G201, rs74aup1g07 vih_vil no PDF VOH/VOL. RS29511 Soo ICC/VOUT/CAP closed in the following DC finding.
