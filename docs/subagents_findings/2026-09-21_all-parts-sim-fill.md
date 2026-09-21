keywords: check_all_parts, physics_scale, sim-248, leftover-19, fill-excel, rs622, leftover-honest
main_idea: Scale SIM `check_all_parts` EXIT 0 on 32 yaml parts: 248/265 stamps, 246 REALIZED, 19 named LEFTOVER. Eugene RS622 Fill Excel RPC wrote `RS622XK_Lab_Report_filled.xlsx` in 10 s (temp-xlsx path).

PREFLIGHT: HIT. Reuse 2026-09-21_physics-scale-demo.md + 2026-09-21_fill-excel-aup-idd-awg.md.

## Console / check path (not a new TestSpec)

- `python -m ate.core.check_all_parts` = scale loop (SIM `run_sequence` every enabled id, `time.sleep` patched).
- Results **Fill Excel numbers** = worker `fill_workbook` on Eugene RS622 SOP8 Version_1.

## Proof

- SIM 248/265 parts=32 yaml=32 keep=29 mso=20 stub=[] visa_known PSU+AWG+DMM+MSO. physics REALIZED=246 LEFTOVER=19.
- AUP `delta_supply_current` is in KEEP (yaml 1.8/2.5/3.3). Did not abort the scale.
- Fill: status=ok filled=2 annotated=2 photos=0 excel `OpAmp/RS622/SOP8/Eugene/Version_1/workbook/RS622XK_Lab_Report_filled.xlsx`.

## Leftover-honest (19)

- settling: lm358, rs358, rs622 (SETTLE_VPP_V, not 0.1% us)
- noise: rs358, rs622, rs8551 (0.1-10 Hz Vpp, not nV/rtHz)
- ron / usb_ron: rs2323, rs2227 (10 mA; PDF min/max)
- iso / xtalk / usb_iso / usb_xtalk: 1 MHz high-Z vs RF (MSO 70 MHz)
- i2c_ron rs0302: 10 mA vs 64 mA
- supply_current draft: rs1g00, rs1g02, rs1g04, rs1g86, rs2g08, rs2g32 (no eugene_cap IDD)

## Not proven

- USB START of every inventory SKU (this scale is SIM).
- Comparator / Interface / Vref / Clock `live: false`.
- RS622 fill stamped 2 cells from living report, not a full OpAmp campaign paste.
- SIM 17/265 ran without `ok` increment; leftover wrap bodies, not a FAIL (check EXIT 0).
