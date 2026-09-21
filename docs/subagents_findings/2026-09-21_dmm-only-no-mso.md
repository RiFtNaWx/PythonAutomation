keywords: screenshot_from, coerce, dmm-only, ioz, rs1g126, seelim, fill-excel, leftover-honest
main_idea: DMM-only TestSpecs never capture MSO. One helper coerce_screenshot_from(shot, required) is applied at list_tests and _run_one for every family. Live SeeLim RS1G126 IOZ session_2026-09-21_160926 wrote 56 VOUT points, 2.838 uA, DMM reading-card PNG, Fill Excel IOZ sheet images=1.

DMM-only stale screenshot_from=mso (yaml or Parameters Write) becomes dmm. MSO TestSpecs keep mso. PSU-only stale mso becomes none. UI already coerces the select the same way.

Live USB: Logic/RS1G126/SC70-5/SeeLim/Version_1. Recipe ioz_vout 0..5.5 step 0.1 (See Lin, n=56) at VCC 3.6 OE L. max_abs 2.838 uA, spec max 10 uA, settle NON_TIGHT / unspec. PNG ioz_2026-09-21_161113.png 606 bytes \x89PNG. Fill workbook/RS1G126_Lab_Report.xlsx IOZ E57=2.838317 images=1.

Leftover: old ioz_2026-09-21_151107.jpg MSO jpeg still on disk (Windows IOZ/ioz same folder). run_log used to rglob every screenshots/* including that jpg; now session artifacts + this-run step shots only. record_step used to keep only rows and drop screenshot; now keeps screenshot/screenshots/screenshot_from. Worker must idle-restart to load those two. First START after coerce restart died (session_2026-09-21_160633 empty steps) when restart_ate_worker.bat --worker-only raced supervisor; second START on the standing worker completed.
