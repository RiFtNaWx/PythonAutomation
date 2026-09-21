---
keywords: [demo, sim, rs1g07, sts-pdf, run-log, screenshot-txt, datasheet, cin, cpd, icc, auto-fill, eugene]
main_idea: RS1G07 Logic DEMO (Eugene / SC70-5 / Version_1) now runs all 6 enabled tests on fake PyVISA, stamps datasheet ids (ICC_uA / CIN_pF / CPD_pF), writes screenshot .txt next to SIM jpgs, sessions/run_log.txt, and STS datalog.pdf. Excel paste.values are still unmapped so Fill Excel skips most cells.
---

# 2026-09-13 RS1G07 DEMO whole-pipeline report

## Product

User asked RS358 or RS1G07. RS358 limits are typ-only and SIM slew/GBW is RS622-shaped, so a tight min/max would FAIL. RS1G07 has 6 enabled tests and proven CIN/CPD SIM.

Campaign:

`C:\Users\OoiJianHong\#Test_Database\Logic\RS1G07\SC70-5\Eugene\Version_1`

## Gaps that blocked a datasheet PDF

1. `setup_dc()` returned None, so Ariff DC tests skipped (`ioff_leakage: setup failed`).
2. SIM DMM current was too high for ICC max 1 uA, or not `I=C*V*f` for Cpd.
3. Cap tests stamped `CIN_uA` / `CPD_uA` instead of pF.
4. No `sessions/run_log.txt` and no SIM screenshot `.txt`.
5. DEMO required a manual Select all.

## Shipped

- Limits in `ate/config/limits/rs1g07.yaml` from RS1G07 Rev A.6 text.
- SIM DMM: 0.8 uA when AWG off; Cpd table 3/4/6 pF when square >= 1 MHz.
- `setup_dc` returns True.
- `specs.py` prefers spec ids; Soo `IDD_mA` aliases to `ICC_uA`.
- `mso5072._write_sim_shot_note` writes `{jpg}.txt` on SimResource.
- `datalog.write_run_log` after STS export.
- DEMO auto-selects campaign tests; post-run `export_datalog` + `fill_workbook`.

## Proven (UI DEMO + disk)

Live console DEMO at 21:54:52 (session_2026-09-13_215452):

| Test | Param | Value | Result |
|------|-------|-------|--------|
| cin | CIN_pF | ~4 | pass (typ 4, window 1-10) |
| cpd | CPD_pF | ~6 | pass (typ 6 @ 5 V) |
| delta_supply_current | DELTA_ICC_uA | 0.8 | pass (max 500) |
| input_leakage_sweep | II_uA | 0.8 | pass (max 1) |
| ioff_leakage | IOFF_uA | 0.8 | pass (max 1) |
| supply_current | ICC_uA | 0.8 | pass (max 1) |

Status completed, Total 6, Pass 6, Fail 0.

Artifacts:

- `sessions/report.json`
- `sessions/datalog.pdf`
- `sessions/run_log.txt`
- `{CIN,Cpd}/DUT_1/screenshots/*.jpg` + matching `.txt`

Subagent verify: [Verify RS1G07 DEMO artifacts](b74ef317-1c8e-47c4-a23e-87e12ecb35ab) 6/6 PASS.

## Not proven / leftover

- Excel `sheet_map.yaml` has no `paste.values`. Fill Excel filled 1 / skipped 5. Do not invent cells.
- Test-program accordion still duplicates each row (12 ticks -> each slot ran twice; merge keeps 6 latest).
- Header model still shows leftover `RS622` next to RS1G07 path. Tests still ran the Logic suite.
- USB START / 4-DUT hardware not this DEMO.
- RS358 not run (OR satisfied by RS1G07).

## Tomorrow

1. Ctrl+F5 on `http://127.0.0.1:5174/`
2. Operator Eugene (not All). Family Logic. Part RS1G07. Package SC70-5. Version_1. Apply campaign.
3. DEMO dry-run (not the left-rail Demo family). SIM auto-continues. Wait for Results PASS + PDF path.

Checks:

```
python -m ate.core.check_sim_run
python -m ate.core.check_specs_datalog
python -m ate.core.check_ui_contract
python -m ate.core.check_demo_families
```
