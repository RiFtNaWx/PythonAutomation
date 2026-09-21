---
keywords: usb, start, not-demo, logic, continue, stop, abort, speedrun, rs1g07, rs1g08, cin, cpd, voh_load
main_idea: Later session is a live USB START (Discover then Open Session), not DEMO. Logic speedrun is DUT 1 + one test, Continue at board/DUT/pause_hook, header STOP for emergency. Select-all is not the first pass.
---

# 2026-09-14 Real USB Logic speedrun (parked until hardware)

PREFLIGHT: PARTIAL. Reuse: 2026-09-13_usb-live-recording, 2026-09-13_sim-loopback-preflight, docs/DEMO.md Act A. Spawn: skip.

User ask: later continue, real connect, not DEMO, press buttons, stop at the right time, logic parts, full-cycle debug.

## Hard rule

| | Do | Do not |
|---|----|--------|
| Session | Discover (tiles ON) then **Open Session** | DEMO (SIM), Open SIM |
| Hint | visa backend, not `SIM session` | START while hint says SIM |
| Continue | operator clicks | auto-continue (that is DEMO) |
| Sleep | real dwell | skipped SIM sleep |
| Excel | warn before Fill (live xlsx + photos) | Fill Excel unattended |

If USB answers *IDN, DEMO aborts and tells you to Open Session + START. That is correct.

## Stop vs Abort vs Continue

| Control | When | What happens |
|--------|------|----------------|
| **Continue** (modal or dock) | Board LOGIC, DUT place, pin-1, cin/cpd wiring, FAIL next-DUT | PSU/AWG already SAFE IDLE. Run proceeds. |
| **Abort** (modal) | Wrong orientation, skip remaining, fail-gate | Remaining tests abort. Bench stays idle. |
| Header **STOP** | Smoke, hang, VISA poison, PSU wrong | `stop` RPC = `request_cancel` + `emergency_cleanup` (AWG then PSU off, scope park). |
| Pin-1 wrong | Hint on Setup | Abort, rotate, Continue -- do not keep powering. |

Do not restart the worker while busy. Header STOP first.

## Speedrun order (USB, DUT 1 only)

Operator **Eugene** (not All, not Kevin). Apply must match a tree that exists. Yaml package is often SOT23; inventory is often SC70-5 -- pick the folder on disk.

1. `python -m ate.core.check_visa` -- need `KEEP USB0` (or USB1) and `preflight mode=usb`. SKIP ASRL only = no gear.
2. Close Ultra Sigma. `run_ate_app.bat`. `http://127.0.0.1:5174` Ctrl+F5.
3. Logic / RS1G07 / existing package / Eugene / Version_1. **Apply campaign**. DUT **1** only.
4. Discover -> Open Session. START disabled until session is USB-open.
5. Tick **one** test. First smoke: `supply_current` (PSU+DMM). Then `cin` or `cpd` (pause_hook wiring).
6. START. Continue at: board LOGIC -> place DUT 1 -> cin/cpd wiring prompt. Do not Select-all.
7. After Results STS: header STOP on a second 1-test run to prove cancel + safe idle.
8. Then RS1G08 (operator **Ariff** folder, do not write Eugene over Ariff): `supply_current_sweep` then `voh_load`. Same USB session if still open.
9. RS1G14 Eugene: `supply_current` then `ioff_leakage`. Skip `input_off_leakage` if it is still Path C scaffold.

Do not claim RS0204 / RS2323 / RS622 in the same first sitting unless Logic 1-DUT smoke is green.

## Buttons: click vs skip on USB day

Click (full cycle): Discover, Open Session, Apply campaign, Open DB/sessions, Screenshot, START, Continue, Abort (once on purpose), STOP, Results Export STS, Run ledger reload. Tests page Refresh scan only (no Wrap).

Do not click during the live START: DEMO, Open SIM, Select all, Forget person, Import family, Fill Excel (until operator confirms live xlsx), Open last question as GitHub issue.

## Debug if it is not smooth

| Symptom | Cause | Fix |
|---------|--------|-----|
| Discover `{}` | Empty cache, Ultra Sigma, unplugged | force rescan, close other VISA, Discover again. Open Session force-rescans if no MSO. |
| Open Session fails after SIM leftover | SIM closed, START still enabled old bug | refreshSession should disable START. Retry Discover then Open Session. |
| START grey | No session | Open Session USB, not DEMO |
| Sit on Building plan | missed run_epoch | wait; if wedged STOP then idle restart worker |
| VISA SYSTEM_ERROR | screenshot poison | runner auto-continues next DUT, no Continue popup |
| Scaffold `imported_input_off_leakage` | empty measurements | skip; fill Path B before USB |
| Package mismatch | SC70-5 vs SOT23 | Apply the tree that exists |

Logs: worker window, `sessions/run_log.txt`, browser F12. Table: docs/VIBE_CODE.md section 5.

## Does not prove (until this sitting happens)

- KEEP USB on this PC tonight (last check was SKIP ASRL).
- A full USB Continue cycle on Logic.
- Header STOP while PSU is ON.
- Select-all of RS1G08 12 tests (too many Continue + dwells for a first pass).
---
