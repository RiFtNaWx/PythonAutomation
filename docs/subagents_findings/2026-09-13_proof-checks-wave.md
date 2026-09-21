keywords: proof-checks, ate.core, wave-2026-09-13, check_add_test, campaign_outline, sim_run, demo_families, false-red
main_idea: Child wave saw 15 PASS + 2 FAIL. Parent re-ran after AST/YAML-token locks; both FAILs were comment false-reds and now EXIT 0. Do not "fix" eugene_cap or write FILL_ME cells.

# Proof checks wave (2026-09-13)

Child [proof checks](3c16da8f-f942-46fd-8b88-fb1aeba7fc50) ran 17 modules (~21s, no 90s timeout). Parent later classified the 2 FAILs as false-red:

1. `eugene_cap.py` docstring `No input().` -- `check_add_test` now AST Call only. EXIT 0.
2. RS1G07 SC70-5 comment `Do not write FILL_ME.` -- `check_campaign_outline` now exact YAML token. EXIT 0.

Do not invent Excel cells or strip those comments.

Runner: `venv\Scripts\python.exe -m <module>` from junction cwd (apostrophe path breaks the PowerShell wrapper). Worker/UI not started by this child.

| Module | Child exit | Parent after lock |
|--------|------------|-------------------|
| `ate.core.check_add_test` | 1 (false-red) | 0 |
| `ate.core.check_campaign_outline` | 1 (false-red) | 0 |
| `ate.core.check_sim_run` | 0 | SIM loopback + RS1G07 full suite + RS622 slew/psrr; Version_1 records + STS PDF |
| `ate.core.check_demo_families` | 0 | SIM cin+cpd, iplus, vih, iq, slew across demo families |
| `ate.core.check_launch` | 0 | Silent start, daily sync on splash, no backend windows |
| `ate.core.check_visa` | 0 | IVI backend, ASRL skip, SIM mapping, empty live mapping OK |
| `ate.core.check_session_values` | 0 | OK |
| `ate.core.check_specs_datalog` | 0 | OK |
| `ate.core.check_ui_contract` | 0 | Tabs + fonts contract OK |
| `ate.core.check_test_detect` | 0 | Wrap/dirty/missing/cross-family/operator isolation OK |
| `ate.core.check_tags_datalog` | 0 | OK |
| `ate.core.check_operator_tree` | 0 | migrate+list_tree; ChangThong label; unassigned |
| `ate.core.check_new_product` | 0 | categories=10 inventory=37 demo_instruments DMM+PSU |
| `ate.core.check_progress` | 0 | observer blocked, people merge, board round-trip |
| `ate.core.check_cloud_db` | 0 | env wins, sharepoint url, first_data_line |
| `ate.core.check_lookup` | 0 | pdfs=28 index=datasheets.yaml |
| `ate.core.check_sync_repo` | 0 | dirty never pulls, stamp gates, ATE_APP_ONLY skip, ff-only |

## FAIL output (full)

### ate.core.check_add_test (exit 1)

```
FAIL check_add_test:
  - eugene_cap.py must not call input()
```

### ate.core.check_campaign_outline (exit 1)

```
FAIL campaign_outline:
  - C:\Users\OoiJianHong\#Test_Database\Logic\RS1G07\SC70-5\Eugene\Version_1\_manifest\sheet_map.yaml: FILL_ME still present
```

## PASS tail lines (last 20 lines each)

### ate.core.check_sim_run (exit 0)

```
SIM loopback: {'ok': True, 'checks': [{'id': 'psu_off_current', 'ok': True, 'detail': 'I=1e-12'}, {'id': 'psu_on_volt_received', 'ok': True, 'detail': 'V=3.3'}, {'id': 'psu_on_icc', 'ok': True, 'detail': 'I=8e-07'}, {'id': 'awg_vpp_received', 'ok': True, 'detail': 'Vpp=1.0'}, {'id': 'awg_count_received', 'ok': True, 'detail': 'COUNT=120.0'}, {'id': 'awg_off_vpp', 'ok': True, 'detail': 'Vpp=0.001'}, {'id': 'awg_off_count', 'ok': True, 'detail': 'COUNT=0.0'}, {'id': 'psu_off_volt', 'ok': True, 'detail': 'V=0.001'}]}
DB: OpAmp/RS622/TTSOP8/Version_1 model=RS622 DUTs=[1]
Lab report: C:\Users\OOIJIA~1\AppData\Local\Temp\ate_sim_run__0a6v3yl\#Test_Database\OpAmp\RS622\TTSOP8\Eugene\Version_1\workbook\RS622_Lab_Report_TTSOP8.xlsx
Channels: ['CHA']
Plan: category -> channel -> DUTs (2 cat x 1 ch x 1 DUT) = 5 timeline steps
Fixture batches: BUFFERx1 -> ATEx1
Safe idle (config_change): AWG OFF, PSU OFF, then scope STOP
Config BUFFER confirmed
Safe idle (dut_change): AWG OFF, PSU OFF, then scope STOP
DUT_1 confirmed (CHA)
=== RUN Slew Rate (mode=BUFFER, DUT_1, CHA) ===
Safe idle (post DUT_1 CHA slew): AWG OFF, PSU OFF, then scope STOP
Safe idle (config_change): AWG OFF, PSU OFF, then scope STOP
Config ATE confirmed
=== RUN PSRR (mode=ATE, DUT_1, CHA) ===
Safe idle (post DUT_1 CHA psrr): AWG OFF, PSU OFF, then scope STOP
Safe idle (sequence done): AWG OFF, PSU OFF, then scope STOP
Session manifest -> C:\Users\OOIJIA~1\AppData\Local\Temp\ate_sim_run__0a6v3yl\#Test_Database\OpAmp\RS622\TTSOP8\Eugene\Version_1\sessions\session_2026-09-13_232524.json
Session closed.
OK check_sim_run: SIM COUNT/VPP/GBW/Cpd-current; RS1G07 full suite + PDF/log/shot-txt; RS622 slew+psrr separated, Version_1 records + STS PDF
```

### ate.core.check_demo_families (exit 0)

```
Final Mapping:
{'MSO': 'SIM::MSO5072', 'PSU': 'SIM::DP832', 'AWG': 'SIM::DG811', 'DMM': 'SIM::DMM6500'}
SIM session -- no USB; PSU/AWG/DMM/MSO are fake SCPI
SIM session open (no USB) -- fake SCPI for MSO/PSU/AWG/DMM
SIM loopback: {'ok': True, 'checks': [{'id': 'psu_off_current', 'ok': True, 'detail': 'I=1e-12'}, {'id': 'psu_on_volt_received', 'ok': True, 'detail': 'V=3.3'}, {'id': 'psu_on_icc', 'ok': True, 'detail': 'I=8e-07'}, {'id': 'awg_vpp_received', 'ok': True, 'detail': 'Vpp=1.0'}, {'id': 'awg_count_received', 'ok': True, 'detail': 'COUNT=120.0'}, {'id': 'awg_off_vpp', 'ok': True, 'detail': 'Vpp=0.001'}, {'id': 'awg_off_count', 'ok': True, 'detail': 'COUNT=0.0'}, {'id': 'psu_off_volt', 'ok': True, 'detail': 'V=0.001'}]}
DB: OpAmp/RS622/TTSOP8/Version_1 model=RS622 DUTs=[1]
Lab report: C:\Users\OOIJIA~1\AppData\Local\Temp\ate_demo_fam_029shmhj\#Test_Database\OpAmp\RS622\TTSOP8\Eugene\Version_1\workbook\RS622_Lab_Report_TTSOP8.xlsx
Channels: ['CHA']
Plan: category -> channel -> DUTs (1 cat x 1 ch x 1 DUT) = 3 timeline steps
Fixture batches: BUFFERx1
Safe idle (config_change): AWG OFF, PSU OFF, then scope STOP
Config BUFFER confirmed
Safe idle (dut_change): AWG OFF, PSU OFF, then scope STOP
DUT_1 confirmed (CHA)
=== RUN Slew Rate (mode=BUFFER, DUT_1, CHA) ===
Safe idle (post DUT_1 CHA slew): AWG OFF, PSU OFF, then scope STOP
Safe idle (sequence done): AWG OFF, PSU OFF, then scope STOP
Session manifest -> C:\Users\OOIJIA~1\AppData\Local\Temp\ate_demo_fam_029shmhj\#Test_Database\OpAmp\RS622\TTSOP8\Eugene\Version_1\sessions\session_2026-09-13_232526.json
Session closed.
OK check_demo_families: SIM cin+cpd, iplus, vih, iq, slew; busy claimed before thread; sleep skipped
```

(Remaining 13 PASS modules had short output; see table above.)
