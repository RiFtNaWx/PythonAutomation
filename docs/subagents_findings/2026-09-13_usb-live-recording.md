---
keywords: usb, visa, discover, open-session, continue, recording, demo, modular, testspec, cin, cpd
main_idea: Tonight Discover is {} (ASRL only). USB START is Discover then Open Session (not DEMO). Empty Discover cache must rescan on Open Session; silent {} hid the miss. New test = TestSpec file + part yaml, not runner.py.
---

# 2026-09-13 USB live recording + modular edit path

## Tonight (this PC)

Worker `discover` = `{}`. `check_visa` live list is `SKIP ASRL` only. No KEEP USB. Do not START unattended (PSU onto the DUT). SIM session may still be open from the DEMO rehearsal.

## Live vs SIM (say this on camera)

| | DEMO (SIM) | USB START |
|---|---|---|
| Session | `open_session(sim=True)` | Discover then `open_session()` |
| Continue | auto | operator clicks Continue |
| Sleep | skipped | real dwell |
| Excel | `*_demo.xlsx`, no photos | live lab xlsx + photos |
| Hint | `SIM session` | visa backend, not sim |

## Fixes shipped

- `open_session` USB: if Discover cache has no MSO, `find_instruments(force=True)` (plug-in after empty Discover).
- Discover `{}` alerts. Open Session error calls `refreshSession` so START is not left enabled after a failed USB open that closed SIM.
- Discover empty log names skipped ASRL/RAW.
- `check_visa` prints `KEEP`/`SKIP` resource rows. Green with only SKIP does not prove gear is plugged.
- Logic package imports `eugene_cap` with the other modules. `check_family_load` requires `cin`/`cpd`.
- Walk: `docs/DEMO.md` Act A USB, Act B SIM. Edit path: TestSpec + `enabled_tests`, not `runner.py`.

## Recording script (DUT 1, one test)

Discover (tiles ON) -> Open Session (hint not SIM) -> tick `supply_current` or OpAmp `slew` -> START -> Continue at gates -> Results `datalog.pdf`. Warn before Fill Excel on USB.

## Does not prove

- A real MSO/PSU/AWG/DMM is on the bus tonight.
- A full USB START with Continue clicks (not run; would power the socket).
- Slew COUNT wait on live Cnt=0 (`check_slew_capture_run`).
