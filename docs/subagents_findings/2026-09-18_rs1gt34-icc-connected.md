keywords: rs1gt34, icc, path-b, logic-dc, io=0, ovp-6.0, named-vcc, icc-vcc-mode, pin-map, panel, golden-auto, excel-lock, leftover-honest
main_idea: Path B `icc` on shared logic_dc.py (not a GT34 fork). Default VCC plan is named 2.0/3.3/5.5. 0.1 V 2.0-5.5 is opt-in (`icc_vcc_mode: step`). Live ICC after VOL fails if Y-load stays on CH2, OVP is 6.05, DMM is still on Y, or VCC list is the VIH 0.1 walk. Latest overwrite is excel_lock golden_auto + sessions/csv + report.json + records JSON, not a second Excel writer.

PREFLIGHT: HIT
reuse: docs/subagents_findings/2026-09-18_rs1gt34-icc-connected.md, docs/subagents_findings/INDEX.md
spawn: skip

## Physics (shared runner)

- Sense: DMM in series with VCC. `io: 0`. PSU CH2 OFF (`_outputs_open`). VI = VCC or GND. Corners = 2^n.
- VCC plan: `recipe.icc_vcc_mode` named | step | list. Default named = `icc_vcc_list: [2.0, 3.3, 5.5]`. Step is 2.0 to 5.5 by `icc_vcc_step: 0.1` (36 VCC x 2 corners = 72 reads). List is custom overlay. Do not silently use VIH merged 0.1.
- ICCT / `delta_icc`: VCC 5.5, one input 3.4 V, others VCC or GND, IO=0, max 500 uA. Do not invent 0.6.
- OVP: `_ovp_v` = min(6.0, max(5.6, v+0.3)). 5.5 V must not trip DP832 at 6.05.
- DMM: CONF once, no AUTO. ICC/II 100 uA. ICCT/delta_icc 1 mA.
- Limits: `ICC_uA` max 1 (`test: icc`). `ICC_FULL_uA` 10 documented. `DELTA_ICC_uA` 500 maps ICCT 5.5 / one_in 3.4.

## Panel / pin map

Setup `#panel-logic-dc` + `#logic-dc-icc-vcc-mode` + `#logic-dc-pin-map` + RPC `get_product_model` / `save_product_model` / `save_test_params`. Customise Parameters is Version overlay, no xyflow. `collectVccGridFromUi` keeps `prev.status`.
GT34 pin map (CONFIRMED YAML, PSU_MSO): A=PSU CH3 VI, VCC=PSU CH1, DMM CHA series VCC, Y=PSU CH2 load OFF for ICC, GND. Do not steal AWG CH1.

## Recording (latest overwrite)

- Excel: one `workbook/RS1GT34_Lab_Report.xlsx` (`golden_auto` / `one_per_version_overwrite`). Sheet `Icc` for ICC, other Path B sheets for other tests. Pretty / ultimate_manual never auto. `_filled.xlsx` is not the dest.
- CSV latest: `sessions/csv/Icc.csv` overwrite-in-place. Per-run points: `sessions/points/icc_DUT1.csv` + `icc/DUT_1/records/*_points.csv`.
- JSON latest: `sessions/report.json` merge by test_id+dut(+channel). Every run: `icc/DUT_1/records/icc_{timestamp}.json` + `sessions/session_*.json`.
- STS: `sessions/datalog.pdf` plus Version-root `report.pdf` via `export_latest_report`.
- `fill_workbook_from_report` must call `uses_excel_lock` before `no_workbook`. Path A leftover `_filled.xlsx` is not a golden orphan. Do not revert excel_lock / export_latest_report / STS Pass-criteria.

## Leftover-honest

- Cursor Shell wrapper is still broken (`FromBase64String('{1}')`). This agent did not run `python -m ate.core.check_logic_dc`. Operator must run it. Prefer that check: named default has no 4.6; mode=step is 2.0..5.5 n=36; ICCT 3.4; pin map present; OVP <= 6.0; no ioz on GT34.
- Last live ICC (named, DUT1 CHA, n=6, ICC_uA ~0.00989, max 1, PASS, settle NON_TIGHT) still stands. Do not START 72-point live unless operator picks step and instruments are Connected.
- `_tmp_fill_icc.py` / `_tmp_fill_icc.bat` left in place (no `_tmp_fill_icc.log`, fill not proven this turn).
- Worker not restarted this turn: no ATE Control tab for session_status, and python.exe pid 10816 was ~30% CPU (do not kill a possible live run). Idle-restart `restart_ate_worker.bat` when Setup is idle, then Ctrl+F5 `?v=20260918icc3`.
- Campaign must stay Chun Tak / Logic / RS1GT34 / SOT23-5 / Version_1 (not RS622). If this Version `test_catalog.yaml` is short, tick `icc` on Tests and Save this Version.
