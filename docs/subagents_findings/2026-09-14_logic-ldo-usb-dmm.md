---
keywords: logic, ldo, dmm6500, psu, usb, syst-err, enable_current, ovp, rs1g07, rs3213
main_idea: Real USB Logic 6/6 and LDO 6/6 TestSpec returns with DMM6500. PSU ON then idle OFF. DMM SYST:ERR 0. enable_current OVP 6.5 was above 6.0 ceiling; now default OVP.
---

# 2026-09-14 Logic + LDO USB all-test

DMM6500 `USB0::0x05E6::0x6500::04698204`. MSO 0x0515 skipped (NI *IDN wedge). PSU/AWG/DMM KEEP. `dmm_setup` no *RST. `REQUIRED_AT_OPEN` empty.

Logic RS1G07 09:31 session `.../Logic/RS1G07/SOT23/Eugene/Version_1/sessions/` 6/6 success, open-circuit ~0. CIN/CPD STS FAIL vs pF min (no DUT). LDO RS3213 5/6 then `enable_current` IEN n=4 after OVP cap. PSU CH1-3 OFF. SYST:ERR 0 both PSU and DMM.
