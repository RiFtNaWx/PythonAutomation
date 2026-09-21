---
keywords: physics_scale, check_all_parts, logic, scale-wave, leftover-honest, MUST_STAY_LEFTOVER, sim, VOH_, VOL_
main_idea: DEMO green on physics_scale + check_all_parts logic + all-families. 264 rows REALIZED=245 LEFTOVER=19 (13 bench ceiling + 6 draft supply_current). Logic SIM 186/202 on 24 SKUs. Not USB/production proof.
---

# 2026-09-21 Physics scale DEMO

PREFLIGHT: HIT. Reuse 2026-09-15_physics-scale-proof, 2026-09-18_logic-scale-check-all-parts.

## Commands (EXIT 0)

```
venv\Scripts\python.exe -m ate.core.physics_scale
venv\Scripts\python.exe -m ate.core.check_all_parts logic
venv\Scripts\python.exe -m ate.core.check_all_parts
```

Shell tip: apostrophe in `Eugene's Repo` breaks Cursor PowerShell cwd. Run from `C:\Users\OoiJianHong\_run_ate_demo_checks.bat` or `_tmp_demo_checks.bat`.

## Proof counts

| Check | rows | REALIZED | LEFTOVER | SIM |
|-------|------|----------|----------|-----|
| physics_scale (all) | 264 | 245 | 19 | n/a |
| check_all_parts logic | 202 enabled | 195 | 7 | 186/202 |
| check_all_parts all | 264 | 245 | 19 | 247/264 |

## Leftover-honest (19)

**MUST_STAY_LEFTOVER 13** unchanged: iso/xtalk/ron/settling/noise on switch+opamp.

**+6 draft supply_current** (scale-wave G00/G02/G04/G86/2G08/2G32): no eugene_cap IDD Path B; UNCONFIRMED DRAFT numbers HOLD. SIM stamps ICC_uA=0 leftover stub in `wraps.py`.

## Fixes (minimum)

1. `physics_scale.py` -- `LEFTOVER_PAIRS` for 6 draft `supply_current`.
2. `wraps.py` -- leftover-honest SIM stub instead of RuntimeError on draft IDD.
3. `check_all_parts.py` -- `VOH_`/`VOL_` MUST_STAMP; `MUST_STAMP_ANY` for schmitt `input_threshold`/`vth`; `_scale_sim_hard_fail`; per-part `reset_bus()`.
4. `sim.py` -- `logic_loaded` bus for Path B loaded VOH/VOL (before dual-rail opamp branch); RS0204 xlat trip 0.4*VCCA.
5. `logic_dc.py` -- SIM bus hooks for loaded voh/vol + `_sim_is()`.
6. `specs.py` -- `greenable: false` downgrades fail to unspec (UNCONFIRMED honest).

## Not

- runner.py / database.py untouched
- USB START of 24 logic boards
- Datasheet CONFIRM on UNCONFIRMED scale-wave SKUs
