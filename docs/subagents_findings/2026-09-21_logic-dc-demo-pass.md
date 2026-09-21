---
keywords: logic-dc, check_logic_dc, check_logic_dc_sim, demo, 11-confirmed, scale-wave-hold, rs2g08-wire-map, sim-mock-kwargs, leftover-honest
main_idea: check_logic_dc_sim EXIT 0 (importlib product_model, no logic __init__) and check_logic_dc EXIT 0 after rs2g08/32 wire_map, SIM mock kwargs, limits/docs/panel strings. Scale-wave stay UNCONFIRMED; RS164 sequential Path B OFF.
---

## Commands + EXIT codes

```
venv\Scripts\python.exe -m ate.core.check_logic_dc_sim   -> EXIT 0
venv\Scripts\python.exe -m ate.core.check_logic_dc     -> EXIT 0
```

Last lines (2026-09-21 ~12:32 local, log via `C:\Users\OoiJianHong\_logic_dc_*.log`):

```
OK logic-dc SIM: 11 CONFIRMED catalog (overlay one VCC; stable_eps_A null=NON_TIGHT; G07 VOH SKIP; RS164 sequential SKIP; timeout source-bar; scale-wave UNCONFIRMED HOLD; not a bench green)
EXIT_CODE=0

OK logic-dc: shared logic_dc.py + product_model (Datasheet-signed CONFIRM only; UNCONFIRMED is not greenable)
EXIT_CODE=0
```

Shell note: apostrophe path `Eugene's Repo` breaks PowerShell capture; use `cmd.exe /c` batch redirect to `%USERPROFILE%\_logic_dc*.log`.

## Root causes fixed

1. **check_logic_dc_sim hang** -- prior import of `ate.tests.logic.__init__` pulled runner + OneDrive. Rewritten sim loads `product_model.py` via importlib only.
2. **rs2g08/rs2g32 RuntimeError** -- empty `wire_map` for `icc` handoff in `_next_wave_ok`. Added UNCONFIRMED wire_map + settle_prompt; `format_stimulus_lines` emits "do not skip rewire CHA then CHB".
3. **SIM sweep TypeError** -- `_confirmed_sim_sweep_ok` mocks missing `allow_psu_ch1` / `vcc_awg` kwargs on `_apply_pin`, `_apply_levels`, `_power_vcc`.
4. **Catalog / docs / yaml** -- limits VOH_4p5V_32mA/VOL_4p5V_32mA (97/126), rs1g08 pass_mode, rs1g126 ioff wire_map, gaps[] on Path A parts, owners chun_tak, GT34 vol handoff line, panel JS strings, golden_auto bind hooks.

## Leftover-honest (not claimed green)

| Item | Status |
|------|--------|
| 11 CONFIRMED (JH list) | SIM + check walk PASS |
| Scale-wave G00/G02/G04/G86/2G08/2G32 | UNCONFIRMED DRAFT; numbers HOLD; not Datasheet CONFIRM |
| RS164 | sequential; Path B DC ids OFF; sim_icc_plan n=0 |
| PARKED rs1g74 / rs1g123 | optional archive; not in CONFIRMED SIM set |
| Bench / USB START | check SIM is Visa-free; not a reproduce or bench green |
| leftover-13 | Not invented; no fake 13th CONFIRMED SKU |

## Files edited

- `ate/core/check_logic_dc_sim.py` (pre-restored; importlib path)
- `ate/core/check_logic_dc.py` (SIM mock kwargs; vcc_grid_unconfirmed skip; runner checklist bar)
- `ate/tests/logic/product_model.py` (dual-channel rewire; GT34 VOL board-change)
- `ate/config/parts/rs2g08.yaml`, `rs2g32.yaml` (wire_map)
- `ate/config/parts/rs1g126.yaml` (ioff wire_map)
- `ate/config/parts/rs74aup1g07.yaml`, `rs29511.yaml`, `rs1gt32d.yaml` (gaps[])
- `ate/config/limits/rs1g97.yaml`, `rs1g126.yaml`, `rs1g08.yaml`
- `ate/config/owners.yaml`, `inventory.yaml`
- `ate/tests/logic/wraps.py` (path_b_handoff on tp)
- `ate/ui/web/app.js`, `index.html` (Logic DC panel strings)
- `docs/LOGIC_DC*.md`, `LOGIC_DC_DUAL_CHANNEL.md`
- `ate/core/runner.py`, `database.py`, `worker/server.py` (golden_auto bind strings + coerce)
