---
keywords: usb, demo, start, slew, tmo, visa, dmm, rs622, mso, psu, awg
main_idea: 2026-09-14 USB KEEP is MSO+PSU+AWG (no DMM). DEMO is blocked. Two live RS622 slew STARTs failed VI_ERROR_TMO before any new JPEG. *IDN still works.
---

# 2026-09-14 USB connected, slew TMO

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_real-logic-usb-speedrun, 2026-09-13_usb-live-recording. Spawn: skip.

User: "connected please try to test run demo".

## What ran

- Worker 8766 + UI 5174 started. Operator Eugene. Preflight `mode=usb`.
- KEEP: MSO5072, DP832, DG822 Pro. No DMM. SKIP ASRL3/4.
- DEMO refused (correct). Open Session USB, START `slew` DUT 1 CHA on RS622 BUFFER (no DMM so Logic `supply_current` cannot run).
- Continue auto-clicked at BUFFER + DUT 1 (agent run, not operator).
- Two STARTs: 08:46 and 08:51. Both FAIL `VI_ERROR_TMO` after ~2.5 min (runner MSO retry included). No `SlewRate` JPEG dated 2026-09-14.
- After close, *IDN still answers on all three USB INSTR.

## Do not

- Click DEMO while USB *IDN works.
- Fill Excel unattended.
- Claim Logic smoke: DMM missing; yaml `supply_current` needs PSU+DMM.
- Treat STS `datalog.pdf` from a mid-run campaign switch (browser applied RS2227 once).

## Next sitting

Plug DMM6500 for Logic RS1G07 `supply_current`. For OpAmp slew: look at MSO trigger/AWG OUT during START; session still USB-open on RS622.
