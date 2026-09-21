---
keywords: usb, start, icc, rs1gt34, json, csv, excel, pdf, continue, leftover-honest
main_idea: Live USB ICC on RS1GT34 Eugene completed session_2026-09-21_143132 (IVIVisa PSU+DMM+MSO). JSON/CSV/PDF/records updated. *_filled.xlsx missing. START fetch failed until startInstrumentRun after Open Session.
---

USB START proof (2026-09-21): operator Eugene, Logic RS1GT34 SOT23-5 Version_1, test `icc` only, auto_continue false.

Discover found PSU/AWG/DMM/MSO USB. Open Session second pass dropped AWG (`not on bus`). ICC required DMM+PSU only.

Run: session_2026-09-21_143132 completed 14:36:32. instrument_map USB (not SIM::). steps icc ok True CHA. ICC_uA 0.020825 uA n=26 settle=NON_TIGHT not greenable.

Outputs (Eugene Version_1, mtime 14:36:3x):
- sessions/session_2026-09-21_143132.json
- icc/DUT_1/records/icc_2026-09-21_143631080.json + _points.csv
- sessions/points/icc_DUT1.csv
- sessions/csv/Icc.csv
- sessions/datalog.pdf
- workbook datapoints csv; source xlsx mtime updated
- MISS *_filled.xlsx / *_demo.xlsx
- MISS screenshots (screenshot_from none)

Leftover-honest:
- `#btn-start` applyDb then Failed to fetch twice; run used global `startInstrumentRun(['icc'])` after USB open (same START inner path).
- `_tmp_all_families_app_scale.py` / `_tmp_probe_scale_fails.py` stole campaign until killed.
- Dual `ate.ui.launch` children. Worker db flipped to Chun Tak after DONE.
- Scale-wave G00/G02/G04/G86/2G08/2G32 UNCONFIRMED HOLD. leftover-13 leftover.
- Fill Excel contract is Results `#btn-fill-excel` -> `*_filled.xlsx`; auto end_session did not write that sidecar.
