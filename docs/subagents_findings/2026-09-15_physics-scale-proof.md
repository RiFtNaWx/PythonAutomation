---
keywords: junior, physics_scale, leftover-honest, aup, vih_vil, proof, iso, ron, settling, noise
main_idea: File-level proof is ate/core/_check_data/physics_enabled.json (218 rows). RS74AUP1G07 vih_vil is Ariff Path B REALIZED. Leftover 13 is the 70 MHz / 10 mA / photo-settle / Vpp-noise ceiling. Not production-ready.
---

# Physics scale proof + AUP VIH

## Proof file

`python -m ate.core.physics_scale` and `check_all_parts` write:

`ate/core/_check_data/physics_enabled.json`

Every enabled `(part_key, test_id)` is REALIZED or LEFTOVER. Unclassified fails the check.

## This sitting

RS74AUP1G07 `vih_vil` moved to REALIZED: Ariff Path B at 1.8/2.5/3.3. `voh_load`/`vol_load` stay disabled (no English PDF). Do not copy G-family 5.5 V VOH.

SIM 218/218. REALIZED=205 LEFTOVER=13.

## Leftover 13 (must stay; do not fake)

| Part | Test | Why |
|------|------|-----|
| rs2323 | iso, xtalk | 1 MHz high-Z, not 110 MHz 50 ohm (MSO 70 MHz) |
| rs2227 | usb_iso, usb_xtalk | 1 MHz high-Z, not 550 MHz 50 ohm |
| rs2323 / rs2227 / rs0302 | ron / usb_ron / i2c_ron | 10 mA platform vs PDF image / 64 mA |
| rs622 / rs358 / lm358 | settling | photo/cursor; no MSO delay as 0.1% SETTLE_us |
| rs622 / rs358 / rs8551 | noise | 0.1-10 Hz Vpp, not nV/rtHz; ISC missing |

Those Path B bodies still run USB SCPI (ISO 1 MHz, rON 10 mA, settling photos, noise Vpp). They are leftover vs datasheet BW / 0.1% / density.

## Not production-ready

Goal bar: physically correct datasheet values on every enabled test. Leftover 13 cannot meet that on this bench without faking. Proof is leftover-honest named, not a green check that cannot fail.
