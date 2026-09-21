keywords: rs1gt34, icc, icct, golden-idd, dwell, 2s, 5-sample, csv-stamp, RUN_AT, screenshot_from, leftover-honest
main_idea: Last ICC/ICCT was too fast because Path B used recipe settle_s=0.05 and one DMM read. Golden IDD is 2 s after VCC, 1 s after VI, average 5 reads. CSV latest + stamped filename; Excel RUN_AT / last_run_at; optional MSO screenshot_from.

Too-fast cause: `_wait_settled_current_ua` NON_TIGHT waits 0.05 s once. Picture 2.0-5.5/0.1 (72 corners) finished in minutes that were instrument overhead, not IDD dwell.

Fix (Path B `logic_dc.py`, not runner.py):
- `_icc_vcc_dwell_s` default 2.0, `_icc_vi_dwell_s` default 1.0, `_icc_sample_n` default 5
- leftover generic `dwell_s=0.1` must not shorten VI dwell (only >=1 s or vi_dwell_s)
- optional `screenshot_from=mso` -> `{test}/DUT_n/screenshots/`; missing scope skips (ICC is DMM)
- `excel_lock`: `Icc.csv` latest + `Icc_YYYY-MM-DD_HHMMSS.csv`; Setup `last_run_at`; row `RUN_AT`

Proof: live START ICC step 2.0-5.5 + ICCT 5.5/A=3.4, summary `dwell 2/1s x5`, stamped CSV on disk. Screenshot none unless MSO mapped.
