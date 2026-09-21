keywords: ioz, dmm, screenshot, rs1g126, coerce, live-usb, fill-excel, leftover-honest
main_idea: Live RS1G126 IOZ START used the DMM6500 reading card even with MSO on USB. Family-wide coerce + PNG-prefer fill so DMM-only tests cannot grab MSO.

Live session_2026-09-21_163007 (SeeLim RS1G126 SC70-5 CHA DUT1):
- mapping still listed MSO USB, but step screenshot_from=dmm
- PNG IOZ/DUT_1/screenshots/ioz_2026-09-21_163204.png is DMM6500 DCI 2.59289 uA
- n=56 (Vout 0..5.5 step 0.1 at VCC 3.6), max_abs=2.593 uA, spec max 10 uA
- Fill Excel Path B: IOZ sheet images=1, sessions/csv/IOZ.csv 56 rows
- list_tests IOZ_SHOT=dmm, TP_SHOT empty (tp stays MSO)

Class guards (not IOZ-only):
- coerce_screenshot_from in runner + list_tests: DMM-only stale mso -> dmm
- LOGIC_TEST_DEFAULTS setdefault screenshot_from=dmm except tp/ten/tdis/...
- Path B excel_lock and paste_session_photos prefer .png over leftover .jpg
- check_walk_order walks every family TestSpec; check_session_values prefers png

Do not treat this as USB START of every SKU. 13 leftover pairs stay named. Comparator live:false.
