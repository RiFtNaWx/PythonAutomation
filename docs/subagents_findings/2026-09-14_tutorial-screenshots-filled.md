---
keywords: tutorial, screenshots, demo, cin, run-tab, results, continue, uacc, playwright
main_idea: Filled every ATE_TUTORIAL.html figure with real 2026-09-14 captures; ran Logic RS1G07 Cin DEMO; worker had been down until START.bat / pythonw launch.
---

# Tutorial screenshots filled (2026-09-14)

## What we captured

Live ATE at `http://127.0.0.1:5174` after worker was restarted. DEMO (SIM) on **Logic / RS1G07 / SC70-5 / Eugene / Version_1**, test **cin**, 3/3 steps done, CIN ~4 pF. Results STS showed pass rows. `sessions` folder has `datalog.pdf`, `report.json`, `session_2026-09-14_103023.json`.

USB preflight often answered `*IDN` so DEMO correctly refused until a later preflight fell through to SIM. Continue / Discover-empty / USB-refuse shots use the real `#modal` chrome with the exact operator text (DEMO auto-continues, so a live USB pause was not on screen).

## Files

`docs/tutorial/images/` -- 01 Setup, 02 Results, 03 Tests, 05 splash, 08 Continue, 08-setup DUT, 10 Run timeline, 12 USB + Discover, 13 sessions, 15 first-run, plus existing 04/06/07/09.

`docs/tutorial/ATE_TUTORIAL.html` -- no `shot-missing` placeholders. Fast-path copy for a bench person.

## Worker

Splash had been "Could not start" because port 8766 was down. `START.bat` + `pythonw -m ate.ui.launch` brought it back. If splash never clears: double-click START.bat. Always-on watchdog is still a separate change.
