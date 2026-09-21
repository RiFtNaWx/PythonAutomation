---
keywords: prd-001, f8, epic-a05, lab-report, sheet_map, noise, sync
main_idea: F8 routes to EPIC-A05 only. Live xlsx is the sheet-name source of truth; Noise is the missing TestSpec; sheet_map excel_sheet drifts; do not invent PSRR/Noise suites this wave.
---

# 2026-09-03 PRD F8 -> A05 report sync

PREFLIGHT: PARTIAL. Reused PRD-001 A01-A04 close, live xlsx sheet list, stubs.py, sheet_map.yaml.

xlsx test sheets: Slew Rate, GBW, SettlingTime, SSSR, LSSR, ORT, NoPhaseReversal, VOS, PowerOnTime, VOL, Noise, PSRR, CMRR, AOL, EMIRR.
Missing spec: Noise. sheet_map names Slew/PhaseReversal/PowerOn/VOHL disagree.

Next: epic-agent Mode A A05 only.

Agent: [prd-agent](960f5316-f5c2-437f-8f36-4f282598d2ae)
