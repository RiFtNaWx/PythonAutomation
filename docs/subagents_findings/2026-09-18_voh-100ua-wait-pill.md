keywords: rs1gt34, voh, 100uA, wait-pill, csv, svg, workbook, vcc-0.1, dp832
main_idea: Live VOH ran 100uA + 8/24/32mA. WAIT/RUNNING shake was busy poll overwriting Continue. 100uA does not sag Y (DP832 100uA Ilim). Nominal 5.5 VOH=5.397 fails yaml 5.4 by 3mV.

WAIT flicker: syncRunState set RUNNING whenever busy, even with pendingPrompt. Poll is 350ms. Fix: pendingPrompt keeps WAIT; after idle, WAIT clears to READY.

VOH table (DUT1 CHA, 12-avg DMM):
100uA (CH2 V=0 Ilim=100uA): 2.0->1.9116, 3.3->3.2165, 4.5->4.4069, 5.0->4.9012, 5.5->5.3970
8mA 2.0->1.7089 min1.6 PASS
24mA 3.3->2.8968 min2.5 PASS
32mA 4.5->4.0695 min3.8; 5.0->4.5867 min4.2; 5.5->5.0992 min4.8 PASS

100uA leftover: unloaded Y equals loaded Y. DP832 current limit 0.0001 A is below the supply's useful range, so 100uA is not a real IOH sink. High-current rows are the real load. STS FAIL VOH_5p5V_100uA 5.397 vs datasheet 5.4 (VCC pin is ~5.397 not 5.500).

CSV+SVG: sessions/points/voh_load_DUT1.csv|.svg
Workbook auto-created RS1GT34_Lab_Report.xlsx and filled 24 cells on *_filled.xlsx.
