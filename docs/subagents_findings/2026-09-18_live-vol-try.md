---
keywords: rs1gt34, vol_load, live-usb, chun-tak, 10ohm, 8-24-32mA
main_idea: Live USB START of vol_load only on RS1GT34 Chun Tak DUT1 CHA. VOL 5/5 PASS vs spec_max. 100 uA stayed off.
---

# 2026-09-18 live VOL try

PREFLIGHT: HIT. Reuse live-voh-csv-continue, voh-100ua-disable-vol. Spawn: skip.

## Job

Operator said VOL is connected. Path A existing TestSpec `vol_load` (not Path B). Live USB, not SIM. auto_continue false; Continue fired then operator_force_continue after wiring claim.

## Session

- Operator: Chun Tak / Logic / RS1GT34 / SOT23-5 / Version_1 / DUT1 CHA
- Mapping: DMM `04676344`, AWG `DG8Q281600755`, MSO `MS5A281500878`, PSU `DP8C281601446`
- Continue chain: board LOGIC -> DUT #1 CHA -> VOL load (not VOH)
- Record: `VOL/DUT_1/records/vol_load_2026-09-18_112836080.json`
- CSV: `sessions/points/vol_load_DUT1.csv`

## DMM (5/5 PASS vs spec_max)

| VCC | IOL | Vref | Measured | max |
|-----|-----|------|----------|-----|
| 2.0 | 8 mA | 4.92 | 0.1119 | 0.45 |
| 3.3 | 24 mA | 4.76 | 0.2475 | 0.55 |
| 4.5 | 32 mA | 4.68 | 0.2923 | 0.55 |
| 5.0 | 32 mA | 4.68 | 0.2822 | 0.50 |
| 5.5 | 32 mA | 4.68 | 0.2745 | 0.45 |

INPUT_A_V=0 (buffer). 100 uA OFF. Load 10 ohm.

Does not prove 100 uA IOL. Does not prove Excel fill (no paste.values).
