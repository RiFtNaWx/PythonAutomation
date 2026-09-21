keywords: rs1gt34, icc, icct, delta_icc, live-usb, 0.1-step, 3.4V, picture, awg, leftover-honest
main_idea: Live USB ICC 2.0-5.5/0.1 (72 rows) max 0.129 uA PASS vs picture +25C 1 uA. ICCT 5.5 A=3.4 n=1 max 0.103 uA PASS vs 500 uA. Golden IDD kept AWG+DMM; not 0-5.6, not ICCT 3.0-5.5 sweep.

Picture (RS1GT34 card):
- ICC: VI=VCC or GND, IO=0, VCC 2.0-5.5, +25C max 1 uA (Full 10 documented)
- ICCT: one input 3.4 V, others VCC or GND, VCC=5.5, Full 500 uA

Golden Downloads/logic_tests (1).py kept: PSU CH1, AWG DC, DMM series, 0.1 step, high=this VCC, ICCT 3.4, OVP 5.6-class.
Dropped: start 0 stop 5.6, AWG CH2 on n=1, VI=5.5 at VCC=2, TRAC:CLE, input(), ICCT VCC 3.0-5.5 (card is 5.5 only).

Scale: n=1 ICCT one force (OTHERS=none). n=2 holds others H and L.

Live session_2026-09-18_145904 USB DP8C281601446 / DG8Q281600755 / DMM 04676344.
ICC_uA 0.1288515 result pass max 1.0. DELTA_ICC_uA 0.1028304 result pass max 500.
CSV Icc.csv 72 rows 2.0-5.5 L/H. DeltaICC.csv A 3.4 none.

leftover: settle=NON_TIGHT (stable_eps_A null) -- not a picture-current fail. DMM sign can be negative; judge abs. get_last_run_results has no measurements payload.
