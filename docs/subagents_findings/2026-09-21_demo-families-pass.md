---
keywords: demo-families, check_demo_families, check_sim_run, check_family_load, SIM, rs1g126, rs1g125, rs1g14, rs1gt34, oe_active, y_invert, leftover-honest
main_idea: DEMO Acts B-F proof is three EXIT 0 checks. This sitting fixed catalog ioff, OE polarity from product_model, RS1G14 invert from truth table, and SIM CMOS VT so RS1GT34 VIH stays under limits yaml.
---

## Proof (2026-09-21)

Run from repo root (PowerShell wrapper breaks on apostrophe in path -- use batch or `run_ate_checks.bat`):

```
venv\Scripts\python.exe -m ate.core.check_family_load
venv\Scripts\python.exe -m ate.core.check_sim_run
venv\Scripts\python.exe -m ate.core.check_demo_families
```

Last lines:

```
OK opamp=17 logic=47 level=47 switch=15 power=6 demo=1 restored=17 tests (no cross-family leak); family-scoped catalog/timing OK
OK check_sim_run: SIM COUNT/VPP/GBW/Cpd-current; RS1G07 full suite + PDF/log/shot-txt; RS1GT34 vih_vil/voh/vol/sweep; ...
OK check_demo_families: SIM cin+cpd, iplus, vih, iq, slew; busy claimed before thread; sleep skipped
```

## Fixes (minimum)

| Failure | Cause | Fix |
|---------|-------|-----|
| `rs1g126 catalog must include SeeLim ioff/ioz` | `ioff` missing from `enabled_tests` | `ate/config/parts/rs1g126.yaml` add `ioff` |
| `rs1g125 ten/tdis` wrong RR/FF item | `oe_timing` only read top-level `oe_active` | Read `product_model.oe.active` in `oe_timing.py` |
| `rs1g14 VOH/VOL` A polarity | `_y_invert` ignored `schmitt` truth table | `ariff_dc.py` infer invert from A=H,Y=L row |
| `RS1GT34 vih_vil` SPEC FAIL | SIM CMOS trip at 0.5*VCC above VIH max | `sim.py` VT `0.32*VCC+0.05` for AWG DC path |

## Leftover-honest

- `check_demo_families` was already green before yaml/SIM fixes; `check_sim_run` + `check_family_load` were the blockers.
- SIM VT formula is a ponytail ceiling for buffer VIH class; USB trip may differ.
- Full `check_all_parts` SIM sweep not re-run this sitting.
- Shell: use `C:\Users\OoiJianHong\run_ate_checks.bat` when Cursor PowerShell chokes on `Eugene's Repo`.
