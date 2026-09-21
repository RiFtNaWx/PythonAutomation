keywords: rs1gt34, icc, live-usb, named, chun-tak, path-b, sim-overwrite, leftover-honest
main_idea: Live USB Path B `icc` named 2.0/3.3/5.5 on RS1GT34 Chun Tak DUT1 CHA. Max 0.00849 uA vs spec 1.0 uA PASS. Do not treat SIM step 0.600 uA as lab data. RS1G123/RS1G74 stay out of this pass (UNCONFIRMED stubs).

PREFLIGHT: HIT
reuse: docs/subagents_findings/2026-09-18_rs1gt34-icc-connected.md
spawn: smaller-executor

## Live result (2026-09-18 14:13)

- Campaign: Logic / RS1GT34 / SOT23-5 / Chun Tak / Version_1
- USB: PSU DP832, DMM6500, AWG DG822, MSO5072
- Mode: named (not 0.1 step). n=6, 2^1 corners, IO=0, DMM-on-VCC
- ICC_uA max 0.008493 @ 5.5 V IN_A=L. Spec max 1.0 (+25C). result=pass
- Record: icc/DUT_1/records/icc_2026-09-18_141312080.json
- Latest CSV: sessions/csv/Icc.csv

| VCC | IN_A | ICC_uA |
|-----|------|--------|
| 2.0 | L | 0.002425 |
| 2.0 | H | 0.002879 |
| 3.3 | L | 0.004094 |
| 3.3 | H | 0.004101 |
| 5.5 | L | 0.008493 |
| 5.5 | H | 0.007518 |

Datasheet card ICC (OCR of DC table, already in limits yaml): VI=5.5 or GND, IO=0, VCC 2.0 to 5.5, +25C typ 0.1 max 1, Full 10. No new ingest.

## Leftover-honest

- First script fell to SIM because worker session was closed. SIM step 72-pt (0.600 uA ramp) overwrote latest Icc.csv. Live named run replaced that latest file. Older live records remain (13:37 max 0.00989 uA).
- Cursor Shell on `Eugene's Repo` apostrophe still broken. Junction `C:\Users\OoiJianHong\PythonAutomation\` works.
- Tags on this campaign still say `psu_ch2_a` (VIH leftover). ICC requires PSU CH2 Y-load OFF.
- RS1G123 monostable / RS1G74 DFF not Path B DC this pass.
- 0.1 V step (36 VCC x 2 = 72) not run live. Operator must pick `icc_vcc_mode: step` on the Logic DC panel.
