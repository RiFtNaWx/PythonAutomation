---
keywords: labautomation-1, rs622, sssr, lssr, npr, workbook, datalog, rs1g, rs2323, scale
main_idea: LabAutomation-1 is latest recipes plus DataLogger xlsx; ATE workbook is the characterization report. Keep ATE-native GBW/slew/settling/ORT. Wrap LA-1 SSR/LSR/NPR (and later PowerOn/Noise). RS1G07/14 and Lim RS2323 are later families/parts, not this wave.
---

# 2026-09-03 LabAutomation-1 scale (four explore lanes)

PREFLIGHT: PARTIAL. A05 closed. New source tree: C:\Users\OoiJianHong\Downloads\LabAutomation-1\LabAutomation-1

Agents: [OPA](b9d8bebd-2805-4f27-bbcc-fd938d97f8d1) [Logic](ad007dc1-d634-46b2-abe1-cab71feabf65) [datalog](2f4dfc38-144a-43cf-82da-6fdf1ec0419f) [Lim](2c9bb72e-1d43-43b5-9d4d-6aecb8eaada3)

## Two reports

- LA-1 DataLogger / RS622_results.xlsx = pass-fail log. Not the characterization workbook.
- ATE RS622XK_Lab_Report_TTSOP.xlsx + sheet_map = founder deliverable. Paste today: ORT + Settling only. GBW has photo anchors unused.

## RS622 OPA

Keep ATE-native: slew, settling, ORT, gbw (measure_gbw).
LA-1 has real recipes ATE still stubs: test_SSR, test_LSR, test_NPR, test_powerONtime, flicker/noise_bucket.
LA-1 SSR is newer than repo-root opa_tests.test_SSR (overshoot + locked scales vs delay + input()).

## Scale later

- Logic RS29511: already 7 wraps.
- RS1G07/08/14: same Logic family, part yaml + DC sweep specs. Not new families.
- Lim RS2323: extra family later. Not Level stub. configurations.py broken in download.

## Recommended this wave (WIP one epic)

Wrap LA-1 BUFFER photo tests (SSSR/LSSR/NPR) into ATE TestSpec; paste via existing sheet_map photo anchors; optional GBW place_* using A45 grid. Do not copy whole LabAutomation. Do not invent PSRR/CMRR suites.
