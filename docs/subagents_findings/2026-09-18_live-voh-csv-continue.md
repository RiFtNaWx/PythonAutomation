keywords: rs1gt34, voh_load, live-usb, continue, csv, points, vol-wait, chun-tak
main_idea: Live USB START on RS1GT34 VOH wrote numeric points CSV and STS log. VOL Continue is waiting on purpose until the operator rewires. Excel fill is 0 because workbook/ is empty (no paste.values to guess).

Live run 2026-09-18 10:26+08 Chun Tak Version_1 DUT1 CHA. Worker idle-restarted first so pause_hook loaded. USB mapping PSU/MSO/AWG/DMM. Open Session then run_sequence_async voh_load+vol_load auto_continue=false.

Continue chain that actually fired:
1. board LOGIC
2. DUT #1 CHA
3. VOH load (not VOL) CH2=Vref IOH
4. STOP -- VOL load (not VOH) still pending. Do not Continue until CH2 IOL rewire.

VOH DMM (5/5 PASS vs spec_min):
VCC 2.0 -> 1.7093 (min 1.6)
VCC 3.3 -> 2.8967 (min 2.5)
VCC 4.5 -> 4.0693 (min 3.8)
VCC 5.0 -> 4.5861 (min 4.2)
VCC 5.5 -> 5.0992 (min 4.8)

CSV (numbers only, no PASS/FAIL):
#Test_Database/Logic/RS1GT34/SOT23-5/Chun Tak/Version_1/sessions/points/voh_load_DUT1.csv
Also per-step `*_points.csv` next to the JSON record.

Log: sessions/run_log.txt + datalog.md|.html|.pdf (living merge still lists prior vih_vil).

Excel: fill_workbook status=no_workbook. workbook/ has no xlsx. sheet_map has excel_sheet VOH/VOL but no paste.values. Do not invent cells. Probe the lab book when it exists (VOX corners in campaign_outline).

UACC pixel clicks missed Chrome buttons (coordinate/DPI). operator_force_continue is the same RPC as the Continue button; Chrome showed WAIT/RUNNING/VOL modal.
