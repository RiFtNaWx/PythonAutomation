---
keywords: junior, iso, xtalk, usb_iso, CHAN2, sim-couple, leftover-honest, scpi
main_idea: Leftover 1 MHz iso/xtalk now always query CHAN2 (same USB SCPI), then leftover-couple SIM because CHAN2 is G11 1-pole. Not 110/550 MHz. Stamp gate on every enabled SIM row.
---

# Iso CHAN2 USB path + stamp gate (2026-09-15)

SIM used to skip `:MEASure:ITEM? VPP,CHAN2` and invent `_SIM_COUPLE`. That is not the live USB path.

## What changed

- `ate/tests/lim/iso.py` `chan2_off_vpp` -- always query CHAN2, then if simulated replace with couple (G11 is not OFF residual).
- `xtalk.py` / `rs2227.py` usb_iso/usb_xtalk reuse that helper.
- `check_all_parts` -- enabled SIM row must stamp `{id,value}`. Spec-filter empty is no longer a pass.

## Do not

- Use SIM CHAN2 G11 VPP as isolation dB.
- Reclassify iso/xtalk as REALIZED (MSO 70 MHz, 1 MHz high-Z leftover).

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```
