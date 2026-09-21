---
keywords: junior, wraps, logic_tests, settling, SETTLE_VPP_V, leftover-honest, path-b
main_idea: Logic wraps no longer import repo-root logic_tests. Leftover settling stamps SETTLE_VPP_V (CHAN2 swing), never SETTLE_us. Leftover 13 unchanged.
---

# Wraps fail-closed + settling VPP leftover (2026-09-15)

Enabled logic START never needed `logic_tests.py` after CMOS/RS29511/Eugene Path B. Module import still loaded Soo goldens at family load.

Settling ran USB SCPI photos but stamped no number. 0.1% time stays leftover.

## What changed

- `ate/tests/logic/wraps.py` -- tp/tidle/IDD/READY/Cio route Path B only. Unknown part raises. No `logic_tests`.
- `ate/tests/opa/settling.py` -- stamp `SETTLE_VPP_V` from CHAN2 VPP (~2 V BUFFER square). Not delay-as-us.
- limits rs622 / rs358 / lm358 -- `SETTLE_VPP_V` unspec.

## Do not

- Reclassify settling as REALIZED.
- Stamp SETTLE_us from MSO DELAY.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```
