---
keywords: rs1gt34, vih_vil, live, psu-ch2, mso-ch1, sot23-5, chun-tak, context-steal
main_idea: LIVE RS1GT34 VIH/VIL used PSU CH2 + MSO CH1 (no AWG). UI SeeLim campaign stole worker context mid-run so the finished session first landed under AnalogSwitch/RS2323; copy back to Logic/RS1GT34/SOT23-5/Chun Tak.
---

# 2026-09-17 RS1GT34 VIH/VIL LIVE PSU+MSO

Jian Hong wiring: PSU CH1=VCC, PSU CH2=A, MSO CH1=Y. Part yaml `vih_vil_stimulus: psu_mso`. VCC = 2.0, 3.3, then 4.5-5.5 start/stop/step (0.01 allowed; cap 201 pts). Package SOT23-5.

LIVE DUT_1 13/13 PASS at 0.1 V step (session_2026-09-17_160711). UI AnalogSwitch/SeeLim mid-run was worker `set_db_context` while busy. Fix: busy_locked + Apply skip + header person follows Operator folder. VIN search is now unidirectional coarse-to-fine (`_search_vin_trip`): arm 0 for VIH / VCC for VIL, ladder 0.5..0.01 scaled by the datasheet limit, hit then -/+30% window, skip the rest. CH1 VCC step 0.1, CH2 VIN fine 0.01. Do not linear-walk 0..VCC.
