---
keywords: seelim, input_threshold, NaN, schmitt, ch3, ldo, leftover-honest, must-stamp
main_idea: SeeLim VIH NaN was SIM LDO CH3-on treating CH2=0 as VOUT=VIN. CH3=0 V (SeeLim untest) stays Schmitt. Stamp gate rejects NaN. Original goldens/see_lin unchanged.
---

# SeeLim threshold NaN vs LDO CH3 (2026-09-15)

SeeLim original `threshold_tests.py` sweeps PSU CH2 and reads DMM Y. RS1G97 holds CH3 at 0 V; RS1G126 holds CH3 at OE high.

A SIM LDO shortcut (CH3-on + CH2 < 1 V -> DMM=VIN) made Y look stuck HIGH at A=0. The golden returned NaN. Stamp gate treated NaN as a value.

## What changed

- Removed that LDO shortcut. Schmitt Y follows CH2 even with CH3 OE high.
- Loopback: CH3=0 Y low; CH2=3.3 Y high; OE-high A=0 Y low.
- LDO `IOUTMAX_V`: if DMM VOUT < 0.05 V (SIM Schmitt on the load channel), stamp VIN. USB DMM is on VOUT so this branch does not run on the bench.
- `seelim_dc._flatten`: drop non-finite trips; do not copy golden min/max.
- `check_all_parts`: finite stamp required.
- Original `goldens/see_lin/**/threshold_tests.py` not edited.

## Do not

- Rewrite SeeLim goldens.
- Treat CH3=0 V as LDO EN.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```
